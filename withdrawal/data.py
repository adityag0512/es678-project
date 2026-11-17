"""Raw data auditing, chronology-based offering selection, cutoff features."""
import calendar
from pathlib import Path
import numpy as np
import pandas as pd

KEY = ['code_module', 'code_presentation', 'id_student']
BACKGROUND = ['num_of_prev_attempts', 'studied_credits', 'highest_education']
ENGAGEMENT = ['total_clicks', 'active_days', 'days_since_last_activity',
              'no_activity', 'clicks_last_7', 'clicks_previous_7', 'click_change']
SUBMISSION = ['submissions', 'assignments_due', 'overdue', 'submission_rate']
GROUPS = {'background': BACKGROUND, 'engagement': ENGAGEMENT,
          'engagement_submission': ENGAGEMENT + SUBMISSION,
          'all': BACKGROUND + ENGAGEMENT + SUBMISSION}

def load_tables(raw):
    return {name: pd.read_csv(Path(raw) / f'{name}.csv', na_values=['?']) for name in
            ['courses', 'studentInfo', 'studentRegistration', 'assessments', 'studentAssessment']}

def audit(tables):
    keys = {'courses': KEY[:2], 'studentInfo': KEY, 'studentRegistration': KEY,
            'assessments': ['id_assessment'], 'studentAssessment': ['id_student', 'id_assessment']}
    rows = []
    for name, frame in tables.items():
        duplicates = int(frame.duplicated(keys[name]).sum())
        if duplicates:
            raise ValueError(f'{name}: {duplicates} duplicate keys')
        rows.append({'table': name, 'rows': len(frame), 'duplicate_keys': duplicates,
                     'missing_cells': int(frame.isna().sum().sum())})
    return pd.DataFrame(rows)

def offering_bounds(code):
    year, month = int(code[:4]), {'B': 2, 'J': 10}[code[-1]]
    return (pd.Timestamp(year, month, 1),
            pd.Timestamp(year, month, calendar.monthrange(year, month)[1]))

def select_offerings(tables, config):
    """Select by development cohort size, never later-offering outcomes."""
    courses, info = tables['courses'], tables['studentInfo']
    counts = info.groupby(KEY[:2]).size()
    candidates = []
    for a in courses.itertuples():
        for b in courses.itertuples():
            if a.code_module != b.code_module or a.code_presentation == b.code_presentation:
                continue
            # Same seasonal start limits avoidable curriculum/season differences.
            if a.code_presentation[-1] != b.code_presentation[-1]:
                continue
            _, latest_start = offering_bounds(a.code_presentation)
            earliest_test, _ = offering_bounds(b.code_presentation)
            available = latest_start + pd.Timedelta(days=int(a.module_presentation_length)
                          + config['outcome_availability_lag_days'])
            safe = available < earliest_test + pd.Timedelta(days=min(config['cutoffs']))
            n = int(counts.get((a.code_module, a.code_presentation), 0))
            if safe and n >= config['minimum_development_enrollments']:
                candidates.append({'module': a.code_module, 'development': a.code_presentation,
                    'test': b.code_presentation, 'development_enrollments': n,
                    'conservative_outcomes_available': str(available.date()),
                    'earliest_test_cutoff': str((earliest_test + pd.Timedelta(days=14)).date())})
    if not candidates:
        raise ValueError('No eligible chronological offering pair')
    candidates = sorted(candidates, key=lambda c: (-c['development_enrollments'], c['module']))
    return candidates[0], pd.DataFrame(candidates)

def load_activity(raw, module, offerings):
    chunks = []
    for frame in pd.read_csv(Path(raw) / 'studentVle.csv', chunksize=500_000):
        selected = frame.loc[(frame.code_module == module) & frame.code_presentation.isin(offerings)]
        chunks.append(selected)
    return pd.concat(chunks, ignore_index=True)

def enrollment_table(tables, module, offering):
    info = tables['studentInfo']
    info = info.loc[(info.code_module == module) & (info.code_presentation == offering)]
    return info.merge(tables['studentRegistration'], on=KEY, how='left', validate='one_to_one', indicator=True)

def snapshot(tables, activity, module, offering, cutoff):
    base = enrollment_table(tables, module, offering)
    if not base['_merge'].eq('both').all():
        raise ValueError('Missing registration row')
    # A missing withdrawal date for a withdrawal cannot establish cutoff eligibility.
    valid_outcome = base.final_result.isin(['Withdrawn', 'Pass', 'Distinction', 'Fail'])
    consistent = ((base.final_result.eq('Withdrawn') & base.date_unregistration.notna()) |
                  (~base.final_result.eq('Withdrawn') & base.date_unregistration.isna()))
    valid = valid_outcome & consistent & base.date_registration.notna()
    eligible = valid & base.date_registration.le(cutoff) & (
        base.date_unregistration.isna() | base.date_unregistration.gt(cutoff))
    audit_counts = {'cutoff': cutoff, 'offering': offering, 'total': len(base),
                    'excluded_invalid': int((~valid).sum()), 'eligible': int(eligible.sum())}
    result = base.loc[eligible, KEY + BACKGROUND + ['date_registration', 'date_unregistration', 'final_result']].copy()
    result['target'] = result.final_result.eq('Withdrawn').astype(int)
    result['cutoff'] = cutoff
    result = result.set_index('id_student', drop=False)
    a = activity.loc[(activity.code_module == module) & (activity.code_presentation == offering)
                     & activity.date.le(cutoff) & activity.sum_click.gt(0)
                     & activity.id_student.isin(result.index)]
    # Negative dates represent observed pre-course activity and are deliberately retained.
    grouped = a.groupby('id_student')
    result['total_clicks'] = grouped.sum_click.sum().reindex(result.index, fill_value=0)
    result['active_days'] = grouped.date.nunique().reindex(result.index, fill_value=0)
    last = grouped.date.max().reindex(result.index)
    result['no_activity'] = last.isna().astype(int)
    result['days_since_last_activity'] = cutoff - last
    # Finite training feature; separate no_activity indicator carries the missing-history meaning.
    result['days_since_last_activity'] = result.days_since_last_activity.fillna(
        cutoff - result.date_registration.clip(upper=0) + 1)
    for name, lower, upper in [('clicks_last_7', cutoff - 6, cutoff),
                               ('clicks_previous_7', cutoff - 13, cutoff - 7)]:
        result[name] = a.loc[a.date.between(lower, upper)].groupby('id_student').sum_click.sum().reindex(result.index, fill_value=0)
    result['click_change'] = result.clicks_last_7 - result.clicks_previous_7
    metadata = tables['assessments']
    metadata = metadata.loc[(metadata.code_module == module) & (metadata.code_presentation == offering)
                            & metadata.assessment_type.ne('Exam')]
    submissions = tables['studentAssessment'].merge(metadata[['id_assessment', 'date']],
                    on='id_assessment', how='inner', validate='many_to_one')
    # Carried-forward marks have no trustworthy new submission timestamp: exclude them.
    submissions = submissions.loc[submissions.date_submitted.le(cutoff) & submissions.is_banked.eq(0)]
    result['submissions'] = submissions.groupby('id_student').id_assessment.nunique().reindex(result.index, fill_value=0)
    due_ids = metadata.loc[metadata.date.lt(cutoff), 'id_assessment']
    due_submitted = submissions.loc[submissions.id_assessment.isin(due_ids)].groupby('id_student').id_assessment.nunique()
    # Conservative policy: banked records are not assumed observable by cutoff; report this limitation.
    result['assignments_due'] = len(due_ids)
    result['overdue'] = len(due_ids) - due_submitted.reindex(result.index, fill_value=0)
    result['submission_rate'] = ((len(due_ids) - result.overdue) / len(due_ids)) if len(due_ids) else np.nan
    # Ranking sentinel places never-active students first without contaminating ML features.
    result['inactivity_score'] = result.days_since_last_activity.where(result.no_activity.eq(0), 1e9)
    result['warning_days'] = result.date_unregistration - cutoff
    assert result.index.is_unique
    assert result.overdue.ge(0).all()
    return result.reset_index(drop=True), audit_counts
