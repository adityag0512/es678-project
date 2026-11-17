"""Build the repository's audit, depth analysis and interactive notebook.

Uses frozen predictions only; does not tune or refit a model.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import nbformat as nbf
from sklearn.model_selection import StratifiedGroupKFold
from .data import GROUPS, KEY
from .modeling import top_indices, evaluate

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / 'results'

def markdown_table(frame):
    def cell(value):
        if pd.isna(value):
            return '—'
        return f'{value:.3f}' if isinstance(value, float) else str(value)
    return '\n'.join(['| ' + ' | '.join(frame.columns) + ' |',
        '| ' + ' | '.join(['---'] * len(frame.columns)) + ' |'] +
        ['| ' + ' | '.join(cell(v) for v in row) + ' |' for row in frame.itertuples(index=False, name=None)])

def explore(day=28, population='dynamic', budget=10):
    """Recompute alert decisions from saved scores, without raw data or models."""
    if not (R / 'predictions' / f'day{day}.csv').exists():
        cached = pd.read_csv(R / 'budget_sensitivity.csv')
        selected = cached.loc[cached.cutoff.eq(day) & cached.population.eq(population)
                              & cached.budget_percent.eq(budget)].copy()
        if len(selected) != 4:
            raise ValueError('Choose a saved day, cohort, and integer budget from 5 to 20, or reproduce predictions first.')
        return selected.drop(columns=['cutoff', 'population']).reset_index(drop=True)
    p = pd.read_csv(R / 'predictions' / f'day{day}.csv')
    if population == 'common':
        ids = pd.read_csv(R / 'splits' / f'test_day{day}.csv')
        p = p.loc[p.id_student.isin(ids.loc[ids.common_cohort, 'id_student'])]
    rows = []
    for model in ['inactivity', 'random', 'all_logistic', 'all_boosted']:
        row = evaluate(p, p[model].to_numpy(), model.startswith('all_'), budget / 100, 678)
        rows.append({'model': model, 'budget_percent': budget, **row})
    return pd.DataFrame(rows)

def verify():
    current = pd.read_csv(R / 'metrics.csv').sort_values(['cutoff', 'population', 'model']).reset_index(drop=True)
    reference = pd.read_csv(R / 'reference_metrics.csv').sort_values(['cutoff', 'population', 'model']).reset_index(drop=True)
    pd.testing.assert_frame_equal(current, reference, check_exact=False, rtol=1e-8, atol=1e-10)
    manifest = json.loads((R / 'reference_manifest.json').read_text())
    for relative, expected in manifest.items():
        with (ROOT / relative).open('rb') as stream:
            actual = hashlib.file_digest(stream, 'sha256').hexdigest()
        if actual != expected:
            raise ValueError(f'Reproduction fingerprint differs: {relative}')
    for day in [14, 28, 42]:
        dev = pd.read_csv(ROOT / 'data' / 'processed' / f'development_day{day}.csv')
        test = pd.read_csv(ROOT / 'data' / 'processed' / f'test_day{day}.csv')
        assert not set(dev.id_student) & set(test.id_student)
        predictions = pd.read_csv(R / 'predictions' / f'day{day}.csv')
        assert predictions.id_student.tolist() == test.id_student.tolist()
        assert predictions.target.tolist() == test.target.tolist()
        for model in ['all_logistic', 'all_boosted', 'inactivity']:
            row = evaluate(test, predictions[model].to_numpy(), model.startswith('all_'))
            stored = current.loc[(current.cutoff == day) & (current.population == 'dynamic') & (current.model == model)].iloc[0]
            assert np.isclose(row['recall_at_10pct'], stored.recall_at_10pct)
    assert len(current) == 66
    assert len(list((R / 'models').glob('*.pkl'))) == 24
    print('Verified original metrics, snapshot fingerprints, raw data, split separation and predictions.')

def build():
    config = json.loads((ROOT / 'config.json').read_text())
    (R / 'splits').mkdir(exist_ok=True)
    tests = {d: pd.read_csv(ROOT / 'data' / 'processed' / f'test_day{d}.csv') for d in config['cutoffs']}
    common = set.intersection(*(set(f.id_student) for f in tests.values()))
    examples, budgets, diagnostics = [], [], []
    for day, test in tests.items():
        dev = pd.read_csv(ROOT / 'data' / 'processed' / f'development_day{day}.csv')
        folds = np.full(len(dev), -1)
        cv = StratifiedGroupKFold(config['cv_folds'], shuffle=True, random_state=config['seed'])
        for number, (_, val) in enumerate(cv.split(dev, dev.target, groups=dev.id_student)):
            folds[val] = number
        for name, frame in [('development', dev), ('test', test)]:
            split = frame[KEY + ['cutoff', 'target']].copy()
            split['validation_fold'] = folds if name == 'development' else -1
            split['common_cohort'] = frame.id_student.isin(common) if name == 'test' else False
            split.to_csv(R / 'splits' / f'{name}_day{day}.csv', index=False)
            diagnostics.append({'cutoff': day, 'split': name, 'n': len(frame),
                'no_activity': int(frame.no_activity.sum()),
                'missing_submission_rate': int(frame.submission_rate.isna().sum()),
                'assignments_due': int(frame.assignments_due.iloc[0])})
        predictions = pd.read_csv(R / 'predictions' / f'day{day}.csv')
        assert predictions.id_student.tolist() == test.id_student.tolist()
        for model in ['all_logistic', 'all_boosted']:
            score = predictions[model].to_numpy()
            flagged = np.zeros(len(test), dtype=bool)
            flagged[top_indices(score)] = True
            for category, mask in [('false_positive', flagged & test.target.eq(0).to_numpy()),
                                   ('missed_withdrawal', ~flagged & test.target.eq(1).to_numpy())]:
                indices = np.flatnonzero(mask)
                # A reproducible central example, not a hand-picked extreme.
                order = indices[np.argsort(score[indices], kind='stable')]
                ix = order[(len(order) - 1) // 2]
                row = test.iloc[ix]
                examples.append({'cutoff': day, 'model': model, 'error_type': category,
                    'id_student': int(row.id_student), 'predicted_probability': float(score[ix]),
                    'final_result': row.final_result, 'warning_days': row.warning_days,
                    **{feature: row[feature] for feature in GROUPS['all']}})
        for population in ['dynamic', 'common']:
            for budget in range(5, 21):
                rows = explore(day, population, budget)
                rows['cutoff'], rows['population'] = day, population
                budgets.append(rows)
    pd.DataFrame(examples).to_csv(R / 'error_examples.csv', index=False)
    pd.DataFrame(diagnostics).to_csv(R / 'snapshot_diagnostics.csv', index=False)
    pd.concat(budgets).to_csv(R / 'budget_sensitivity.csv', index=False)
    metrics = pd.read_csv(R / 'metrics.csv')
    main = metrics.loc[metrics.population.eq('dynamic') & metrics.model.isin(['inactivity', 'random', 'all_logistic', 'all_boosted', 'prevalence'])]
    sections = [("Main results", main[['cutoff','model','n','positives','alerts','true_positives','recall_at_10pct','precision_at_10pct','average_precision','brier','median_warning_days']]),
        ('Common cohort: 1,809 students and 300 withdrawals', metrics.loc[metrics.population.eq('common') & metrics.model.isin(['inactivity','all_logistic','all_boosted']), ['cutoff','model','recall_at_10pct','median_warning_days']]),
        ('Ablation: both model families', metrics.loc[metrics.population.eq('dynamic') & metrics.model.str.contains('logistic|boosted'), ['cutoff','model','recall_at_10pct','average_precision','brier']]),
        ('Paired uncertainty', pd.read_csv(R / 'paired_bootstrap.csv')),
        ('Snapshot diagnostics', pd.DataFrame(diagnostics)),
        ('Representative errors: median score within each error group', pd.DataFrame(examples)[['cutoff','model','error_type','id_student','predicted_probability','final_result','total_clicks','active_days','overdue','warning_days']])]
    (R / 'EVIDENCE.md').write_text('# Detailed evidence\n\nGenerated from saved predictions; no model changes.\n\n' + '\n\n'.join('## '+title+'\n\n'+markdown_table(frame) for title, frame in sections)+'\n', encoding='utf-8')
    searches = []
    for path in sorted((R / 'cv').glob('*.csv')):
        frame = pd.read_csv(path)
        frame.insert(0, 'experiment', path.stem)
        searches.append(frame)
    if searches:
        pd.concat(searches, ignore_index=True).to_csv(R / 'cv_results.csv', index=False)
    make_notebook()
    print('Built split manifests, representative errors, budget sensitivity, evidence tables and notebook.')

def make_notebook():
    md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
    nb = nbf.v4.new_notebook()
    nb.cells = [md('# Early Prediction of Student Withdrawal\nES 678 — Aditya Gupta (24110011)\n\nRead the complete reasoning below. Saved results can be inspected without downloading the raw data. The interaction changes an evaluation budget; it does not tune a model.'),
        code("from pathlib import Path\nimport sys\nimport pandas as pd\nfrom IPython.display import display, Markdown, Image\nROOT = Path.cwd()\nif not (ROOT / 'config.json').exists():\n    ROOT = ROOT.parent\nif str(ROOT) not in sys.path:\n    sys.path.insert(0, str(ROOT))\nR = ROOT / 'results'\ndisplay(Markdown((ROOT / 'docs' / 'STUDY.md').read_text(encoding='utf-8')))"),
        md('## Cohorts and primary results'),
        code("display(pd.read_csv(R / 'cohorts.csv'))\ndisplay(pd.read_csv(R / 'primary_results.csv').round(3))\ndisplay(Image(filename=str(R / 'figures' / 'early_warning_tradeoff.png')))"),
        md('## Graduate analysis: common cohort, ablations, uncertainty'),
        code("display(Image(filename=str(R / 'figures' / 'common_cohort.png')))\nmetrics = pd.read_csv(R / 'metrics.csv')\ndisplay(metrics.loc[metrics.population.eq('dynamic')].pivot(index='model',columns='cutoff',values='recall_at_10pct').round(3))\ndisplay(pd.read_csv(R / 'paired_bootstrap.csv').round(3))"),
        md('## Explore the outreach budget\nChange day, cohort, and budget to see how many withdrawals are identified and how many alerts are false positives. The primary protocol remains 10%. Other budgets are retrospective sensitivity analyses with fixed scores. Aggregate results for every integer budget from 5% through 20% are saved in `results/budget_sensitivity.csv`.'),
        code("from withdrawal.submission import explore\nimport ipywidgets as widgets\ndef show_budget(day=28, population='dynamic', budget=10):\n    table = explore(day, population, budget)\n    table['false_alerts'] = table.alerts - table.true_positives\n    display(table[['model','alerts','true_positives','false_alerts','recall_at_10pct','precision_at_10pct','median_warning_days']].rename(columns={'recall_at_10pct':'recall','precision_at_10pct':'precision'}).round(3))\nshow_budget()\ncontrols = widgets.interactive(show_budget, day=widgets.Dropdown(options=[14,28,42], value=28), population=widgets.Dropdown(options=['dynamic','common']), budget=widgets.IntSlider(min=5,max=20,step=1,value=10,description='Budget %'))\ndisplay(controls)"),
        md('## Error audit\nCases are selected by the median predicted score within each error group, using fixed tie order. These observed features do not establish the cause of a withdrawal.'),
        code("display(pd.read_csv(R / 'error_analysis.csv').round(3))\ndisplay(pd.read_csv(R / 'error_examples.csv').round(3))"),
        md('## AI use and references'),
        code("display(Markdown((ROOT / 'docs' / 'AI_USE_AND_REFERENCES.md').read_text(encoding='utf-8')))"),
    ]
    nb.metadata['kernelspec'] = {'display_name':'Python 3', 'language':'python', 'name':'python3'}
    nb.metadata['language_info'] = {'name':'python', 'version':'3.12'}
    nbf.write(nb, ROOT / 'notebooks' / '01_project_analysis.ipynb')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    verify() if args.verify else build()
