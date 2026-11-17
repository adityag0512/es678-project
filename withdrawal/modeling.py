"""Fold-contained preprocessing, budget metrics, and paired uncertainty."""
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import GridSearchCV, StratifiedGroupKFold
from sklearn.metrics import average_precision_score, brier_score_loss
from threadpoolctl import threadpool_limits

def top_indices(scores, fraction=0.1, seed=678):
    scores = np.asarray(scores, dtype=float)
    if not np.isfinite(scores).all():
        raise ValueError('Scores must be finite')
    # Fixed random order is independent of the labels and shared across methods.
    tie = np.random.default_rng(seed).random(len(scores))
    return np.lexsort((tie, -scores))[:int(np.floor(len(scores) * fraction))]

def budget_metrics(y, scores, fraction=0.1, seed=678):
    y = np.asarray(y)
    flagged = top_indices(scores, fraction, seed)
    hits = int(y[flagged].sum())
    return {'n': len(y), 'positives': int(y.sum()), 'prevalence': float(y.mean()),
            'alerts': len(flagged), 'true_positives': hits,
            'random_expected_recall': len(flagged) / len(y),
            'random_expected_precision': float(y.mean()),
            'recall_at_10pct': hits / y.sum() if y.sum() else np.nan,
            'precision_at_10pct': hits / len(flagged) if len(flagged) else np.nan,
            'average_precision': average_precision_score(y, scores) if y.sum() else np.nan}

def evaluate(frame, scores, probabilities=False, fraction=0.1, seed=678):
    out = budget_metrics(frame.target, scores, fraction, seed)
    out['brier'] = brier_score_loss(frame.target, scores) if probabilities else np.nan
    flagged = top_indices(scores, fraction, seed)
    lead = frame.iloc[flagged].loc[lambda x: x.target.eq(1), 'warning_days']
    out['median_warning_days'] = float(lead.median()) if len(lead) else np.nan
    return out

def fit_model(frame, features, kind, config):
    categorical = [c for c in features if c == 'highest_education']
    numeric = [c for c in features if c not in categorical]
    num_steps = [('impute', SimpleImputer(strategy='median', keep_empty_features=True))]
    if kind == 'logistic':
        num_steps.append(('scale', StandardScaler()))
    transformers = [('numeric', Pipeline(num_steps), numeric)]
    if categorical:
        transformers.append(('categorical', Pipeline([
            ('impute', SimpleImputer(strategy='most_frequent')),
            ('encode', OneHotEncoder(handle_unknown='ignore', sparse_output=False))]), categorical))
    if kind == 'logistic':
        estimator = LogisticRegression(max_iter=2000, random_state=config['seed'])
        grid = {'model__C': [0.1, 1.0, 10.0]}
    else:
        estimator = HistGradientBoostingClassifier(random_state=config['seed'], early_stopping=False,
                                                   max_iter=100, learning_rate=0.05)
        grid = {'model__max_leaf_nodes': [7, 15], 'model__l2_regularization': [1.0, 10.0]}
    pipe = Pipeline([('preprocess', ColumnTransformer(transformers)), ('model', estimator)])
    def scorer(model, X, y):
        return budget_metrics(y, model.predict_proba(X)[:, 1], config['alert_fraction'],
                              config['seed'])['recall_at_10pct']
    folds = StratifiedGroupKFold(config['cv_folds'], shuffle=True, random_state=config['seed'])
    search = GridSearchCV(pipe, grid, scoring=scorer, cv=folds, n_jobs=1, error_score='raise')
    with threadpool_limits(limits=2):
        search.fit(frame[features], frame.target, groups=frame.id_student)
    return search

def paired_bootstrap(frame, scores, baseline, config):
    """One row per student; reuse each sample for both methods and rerank."""
    if frame.id_student.duplicated().any():
        raise ValueError('Bootstrap requires unique student rows')
    rng = np.random.default_rng(config['seed'])
    y = frame.target.to_numpy()
    metrics = ['recall_at_10pct', 'precision_at_10pct', 'average_precision']
    differences = {key: [] for key in metrics}
    for _ in range(config['bootstrap_replicates']):
        ix = rng.integers(0, len(y), len(y))
        if y[ix].sum() == 0:
            continue
        a = budget_metrics(y[ix], np.asarray(scores)[ix], config['alert_fraction'], config['seed'])
        b = budget_metrics(y[ix], np.asarray(baseline)[ix], config['alert_fraction'], config['seed'])
        for key in metrics:
            differences[key].append(a[key] - b[key])
    full_a = budget_metrics(y, scores, config['alert_fraction'], config['seed'])
    full_b = budget_metrics(y, baseline, config['alert_fraction'], config['seed'])
    return [{'metric': key, 'difference': full_a[key] - full_b[key],
             'ci_low': float(np.quantile(values, .025)), 'ci_high': float(np.quantile(values, .975)),
             'valid_replicates': len(values)} for key, values in differences.items()]
