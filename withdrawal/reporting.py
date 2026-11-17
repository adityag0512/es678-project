"""Generate figures and a factual results summary from saved metrics."""
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def make_outputs(results):
    metrics = pd.read_csv(results / 'metrics.csv')
    main = metrics.loc[(metrics.population == 'dynamic') & metrics.model.isin(
        ['inactivity', 'random', 'all_logistic', 'all_boosted'])]
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for name, frame in main.groupby('model', sort=False):
        axes[0].plot(frame.cutoff, frame.recall_at_10pct, marker='o', label=name)
        axes[1].plot(frame.cutoff, frame.median_warning_days, marker='o', label=name)
    axes[0].set(ylabel='Recall at 10% alert budget', xlabel='Prediction day', ylim=(0, 1))
    axes[1].set(ylabel='Median warning days (true positives)', xlabel='Prediction day')
    for ax in axes:
        ax.set_xticks([14, 28, 42])
    axes[0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(results / 'figures' / 'early_warning_tradeoff.png', dpi=180)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
    for ax, population in zip(axes, ['dynamic', 'common']):
        for name in ['inactivity', 'all_logistic', 'all_boosted']:
            frame = metrics.loc[(metrics.population == population) & (metrics.model == name)]
            ax.plot(frame.cutoff, frame.recall_at_10pct, marker='o', label=name)
        ax.set(title=f'{population.title()} cohort', xlabel='Prediction day', ylabel='Recall at 10%')
        ax.set_xticks([14, 28, 42])
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(results / 'figures' / 'common_cohort.png', dpi=180)
    plt.close(fig)
    ablations = metrics.loc[(metrics.population == 'dynamic') & metrics.model.str.endswith('_logistic')]
    pivot = ablations.pivot(index='cutoff', columns='feature_group', values='recall_at_10pct')
    ax = pivot.plot.bar(figsize=(9, 4), rot=0)
    ax.set(ylabel='Recall at 10% alert budget', xlabel='Prediction day', title='Logistic regression feature ablation')
    ax.figure.tight_layout()
    ax.figure.savefig(results / 'figures' / 'feature_ablation.png', dpi=180)
    plt.close(ax.figure)
    columns = ['cutoff', 'model', 'n', 'positives', 'alerts', 'true_positives',
               'recall_at_10pct', 'precision_at_10pct', 'average_precision', 'brier', 'median_warning_days']
    main[columns].to_csv(results / 'primary_results.csv', index=False)
    lines = ['# First reproducible experiment', '',
             'These are computed held-out results, not a completed course report.', '',
             '| Day | Method | N | Alerts | Recall | Precision | Median warning days |',
             '|---|---|---:|---:|---:|---:|---:|']
    for row in main.itertuples():
        lines.append(f'| {row.cutoff} | {row.model} | {row.n} | {row.alerts} | '
                     f'{row.recall_at_10pct:.3f} | {row.precision_at_10pct:.3f} | {row.median_warning_days:.1f} |')
    lines += ['', '## Paired recall differences versus inactivity (95% bootstrap intervals)', '']
    ci = pd.read_csv(results / 'paired_bootstrap.csv')
    for row in ci.loc[(ci.population == 'dynamic') & (ci.metric == 'recall_at_10pct')].itertuples():
        lines.append(f'- Day {row.cutoff}, {row.model}: {row.difference:+.3f} '
                     f'[{row.ci_low:+.3f}, {row.ci_high:+.3f}].')
    lines += ['', '## Interpretation limits', '',
              '- Single-module, single-held-out-offering evidence; transfer across all courses is not established.',
              '- Bootstrap intervals condition on fitted models and this offering; they do not include retraining uncertainty.',
              '- Common-cohort comparisons condition retrospectively on remaining enrolled at day 42.',
              '- Chronology uses conservative start-month bounds plus an assumed 30-day outcome availability lag; actual release timestamps are unavailable.',
              '- Banked assessments are excluded from submissions; assessment exemptions are not observed reliably and can affect overdue counts.',
              '- Random ranking is one seeded realization; its expected recall is alerts/N and expected precision is cohort prevalence.',
              '- Predictive usefulness is not evidence that contacting students prevents withdrawal.',
              '- The official-template paper and source ZIP are in paper/; the repository URL and course submission remain to be completed.']
    (results / 'RESULTS.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
