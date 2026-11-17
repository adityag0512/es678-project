"""Run with python -m withdrawal.run [--stage prepare|train|evaluate|all]."""
import argparse
import hashlib
import importlib.metadata
import json
import pickle
from pathlib import Path
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from .data import (KEY, GROUPS, load_tables, audit, select_offerings, load_activity,
                   snapshot, enrollment_table)
from .modeling import fit_model, evaluate, paired_bootstrap, top_indices

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'results'
PROCESSED = ROOT / 'data' / 'processed'

def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, default=str), encoding='utf-8')

def prepare(config):
    tables = load_tables(ROOT / 'data' / 'raw')
    audit(tables).to_csv(RESULTS / 'data_audit.csv', index=False)
    selection, candidates = select_offerings(tables, config)
    candidates.to_csv(RESULTS / 'offering_candidates.csv', index=False)
    module, dev, test = selection['module'], selection['development'], selection['test']
    activity = load_activity(ROOT / 'data' / 'raw', module, [dev, test])
    if activity['date'].isna().any() or activity.sum_click.lt(0).any():
        raise ValueError('Invalid activity dates or click counts')
    test_ids = set(enrollment_table(tables, module, test).id_student)
    dev_ids = set(enrollment_table(tables, module, dev).id_student)
    selection['overlapping_students_removed_from_development'] = len(dev_ids & test_ids)
    selection['selected_activity_rows'] = len(activity)
    write_json(RESULTS / 'selection.json', selection)
    cohort = []
    for cutoff in config['cutoffs']:
        for split, offering in [('development', dev), ('test', test)]:
            frame, counts = snapshot(tables, activity, module, offering, cutoff)
            if split == 'development':
                frame = frame.loc[~frame.id_student.isin(test_ids)]
            counts.update(split=split, after_student_separation=len(frame),
                          positives=int(frame.target.sum()), prevalence=float(frame.target.mean()))
            cohort.append(counts)
            frame.to_csv(PROCESSED / f'{split}_day{cutoff}.csv', index=False)
    pd.DataFrame(cohort).to_csv(RESULTS / 'cohorts.csv', index=False)
    print(f'Prepared {module}: {dev} -> {test}; removed {len(dev_ids & test_ids)} overlapping students.', flush=True)

def train(config):
    records = []
    for cutoff in config['cutoffs']:
        dev = pd.read_csv(PROCESSED / f'development_day{cutoff}.csv')
        for group in config['feature_groups']:
            for kind in ['logistic', 'boosted']:
                print(f'Training day {cutoff}: {group}, {kind}', flush=True)
                fit = fit_model(dev, GROUPS[group], kind, config)
                name = f'day{cutoff}_{group}_{kind}'
                with (RESULTS / 'models' / f'{name}.pkl').open('wb') as out:
                    pickle.dump(fit.best_estimator_, out)
                pd.DataFrame(fit.cv_results_).drop(columns=['params']).to_csv(
                    RESULTS / 'cv' / f'{name}.csv', index=False)
                records.append({'cutoff': cutoff, 'feature_group': group, 'model': kind,
                                'cv_recall': fit.best_score_, 'parameters': fit.best_params_})
    write_json(RESULTS / 'training_selection.json', records)
    write_json(RESULTS / 'frozen_config.json', config)
    print('All models selected using development data only.', flush=True)

def assess(config):
    frozen = json.loads((RESULTS / 'frozen_config.json').read_text())
    if frozen != config:
        raise ValueError('Configuration changed since training; retrain before evaluation')
    # All training is complete before any held-out scoring.
    test_frames = {c: pd.read_csv(PROCESSED / f'test_day{c}.csv') for c in config['cutoffs']}
    common = set.intersection(*(set(f.id_student) for f in test_frames.values()))
    rows, comparisons, errors = [], [], []
    for cutoff, test in test_frames.items():
        dev = pd.read_csv(PROCESSED / f'development_day{cutoff}.csv')
        assert not set(dev.id_student) & set(test.id_student)
        predictions = test[['id_student', 'target', 'warning_days']].copy()
        scores = {'inactivity': (test.inactivity_score.to_numpy(), False, 'rule'),
                  'random': (np.random.default_rng(config['seed']).random(len(test)), False, 'random'),
                  'prevalence': (np.full(len(test), dev.target.mean()), True, 'constant')}
        for group in config['feature_groups']:
            for kind in ['logistic', 'boosted']:
                name = f'{group}_{kind}'
                with (RESULTS / 'models' / f'day{cutoff}_{name}.pkl').open('rb') as source:
                    model = pickle.load(source)
                with threadpool_limits(limits=2):
                    scores[name] = (model.predict_proba(test[GROUPS[group]])[:, 1], True, group)
        for name, (score, probability, group) in scores.items():
            predictions[name] = score
            for population in ['dynamic', 'common']:
                mask = np.ones(len(test), dtype=bool) if population == 'dynamic' else test.id_student.isin(common).to_numpy()
                metrics = evaluate(test.loc[mask], score[mask], probability, config['alert_fraction'], config['seed'])
                rows.append({'cutoff': cutoff, 'population': population, 'model': name,
                             'feature_group': group, **metrics})
            if name in ['all_logistic', 'all_boosted']:
                for population in ['dynamic', 'common']:
                    mask = np.ones(len(test), dtype=bool) if population == 'dynamic' else test.id_student.isin(common).to_numpy()
                    print(f'Bootstrap day {cutoff}: {name}, {population}', flush=True)
                    for item in paired_bootstrap(test.loc[mask], score[mask], test.inactivity_score.to_numpy()[mask], config):
                        comparisons.append({'cutoff': cutoff, 'population': population,
                                            'model': name, 'baseline': 'inactivity', **item})
                flagged = np.zeros(len(test), dtype=bool)
                flagged[top_indices(score, config['alert_fraction'], config['seed'])] = True
                categories = np.select([flagged & test.target.eq(1), flagged & test.target.eq(0),
                                        ~flagged & test.target.eq(1)], ['true_positive', 'false_positive', 'missed_withdrawal'],
                                       default='true_negative')
                summary = test[GROUPS['all'] + ['warning_days']].select_dtypes('number').copy()
                summary['error_type'] = categories
                grouped = summary.groupby('error_type').median().reset_index()
                grouped['count'] = grouped.error_type.map(pd.Series(categories).value_counts())
                grouped['cutoff'], grouped['model'] = cutoff, name
                errors.append(grouped)
        predictions.to_csv(RESULTS / 'predictions' / f'day{cutoff}.csv', index=False)
    pd.DataFrame(rows).to_csv(RESULTS / 'metrics.csv', index=False)
    pd.DataFrame(comparisons).to_csv(RESULTS / 'paired_bootstrap.csv', index=False)
    pd.concat(errors).to_csv(RESULTS / 'error_analysis.csv', index=False)
    from .reporting import make_outputs
    make_outputs(RESULTS)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', choices=['prepare', 'train', 'evaluate', 'all'], default='all')
    args = parser.parse_args()
    config = json.loads((ROOT / 'config.json').read_text())
    for directory in [PROCESSED, RESULTS, RESULTS / 'models', RESULTS / 'cv',
                      RESULTS / 'predictions', RESULTS / 'figures']:
        directory.mkdir(parents=True, exist_ok=True)
    versions = {p: importlib.metadata.version(p) for p in
                ['numpy', 'pandas', 'scikit-learn', 'matplotlib', 'seaborn', 'requests', 'nbformat']}
    write_json(RESULTS / 'environment.json', versions)
    if args.stage in ['prepare', 'all']:
        prepare(config)
    if args.stage in ['train', 'all']:
        train(config)
    if args.stage in ['evaluate', 'all']:
        assess(config)
    write_json(RESULTS / 'source_hashes.json', {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted((ROOT / 'withdrawal').glob('*.py'))})

if __name__ == '__main__':
    main()
