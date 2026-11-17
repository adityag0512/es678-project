"""Independently trace sampled processed rows back to raw records."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def main():
    raw = ROOT / 'data' / 'raw'
    selection = json.loads((ROOT / 'results' / 'selection.json').read_text())
    module = selection['module']
    rows = []
    for split in ['development', 'test']:
        for cutoff in [14, 28, 42]:
            frame = pd.read_csv(ROOT / 'data' / 'processed' / f'{split}_day{cutoff}.csv')
            # Include inactive, active, withdrawing and non-withdrawing records where available.
            chosen = pd.concat([frame.groupby(['no_activity', 'target']).head(2), frame.head(2)]).drop_duplicates('id_student')
            rows.append(chosen)
    samples = pd.concat(rows, ignore_index=True)
    students = set(samples.id_student)
    activity = pd.concat([c.loc[c.id_student.isin(students) & c.code_module.eq(module)]
                         for c in pd.read_csv(raw / 'studentVle.csv', chunksize=500_000)], ignore_index=True)
    metadata = pd.read_csv(raw / 'assessments.csv', na_values=['?'])
    submissions = pd.read_csv(raw / 'studentAssessment.csv', na_values=['?'])
    registration = pd.read_csv(raw / 'studentRegistration.csv', na_values=['?'])
    traces = []
    for row in samples.itertuples():
        events = activity.loc[activity.id_student.eq(row.id_student) &
            activity.code_presentation.eq(row.code_presentation) & activity.date.le(row.cutoff) & activity.sum_click.gt(0)]
        assignments = metadata.loc[metadata.code_module.eq(module) &
            metadata.code_presentation.eq(row.code_presentation) & metadata.assessment_type.ne('Exam')]
        observed = submissions.loc[submissions.id_student.eq(row.id_student) &
            submissions.id_assessment.isin(assignments.id_assessment) &
            submissions.date_submitted.le(row.cutoff) & submissions.is_banked.eq(0)]
        due = set(assignments.loc[assignments.date.lt(row.cutoff), 'id_assessment'])
        missing = due - set(observed.id_assessment)
        reg = registration.loc[registration.code_module.eq(module) &
            registration.code_presentation.eq(row.code_presentation) & registration.id_student.eq(row.id_student)].iloc[0]
        assert reg.date_registration <= row.cutoff
        assert pd.isna(reg.date_unregistration) or reg.date_unregistration > row.cutoff
        assert row.total_clicks == events.sum_click.sum()
        assert row.active_days == events.date.nunique()
        assert row.submissions == observed.id_assessment.nunique()
        assert row.overdue == len(missing)
        assert row.target == int(pd.notna(reg.date_unregistration))
        traces.append({'id_student': row.id_student, 'offering': row.code_presentation,
                       'cutoff': row.cutoff, 'target': row.target,
                       'raw_activity_rows': len(events), 'last_activity_date': events.date.max(),
                       'raw_click_sum': events.sum_click.sum(), 'observed_submissions': len(observed),
                       'overdue_assessment_ids': ','.join(map(str, sorted(missing))), 'checks_passed': True})
    pd.DataFrame(traces).to_csv(ROOT / 'results' / 'predictions' / 'row_audit.csv', index=False)
    print(f'Independent raw-record audit passed for {len(traces)} cutoff rows.')

if __name__ == '__main__':
    main()
