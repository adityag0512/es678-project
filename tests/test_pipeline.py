import unittest
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
from withdrawal.data import snapshot, GROUPS, select_offerings, load_tables
from withdrawal.modeling import budget_metrics, top_indices, paired_bootstrap, fit_model

def fixture():
    info = pd.DataFrame({'id_student': [1, 2, 3, 4, 5], 'code_module': ['AAA']*5,
        'code_presentation': ['2013B']*5, 'final_result': ['Withdrawn', 'Fail', 'Withdrawn', 'Pass', 'Withdrawn'],
        'num_of_prev_attempts': [0]*5, 'studied_credits': [60]*5, 'highest_education': ['A Level']*5})
    registration = info[['id_student', 'code_module', 'code_presentation']].copy()
    registration['date_registration'] = [-10, -5, -5, 20, -5]
    registration['date_unregistration'] = [30, np.nan, 14, np.nan, np.nan]
    assessments = pd.DataFrame({'id_assessment': [10, 11, 12], 'code_module': ['AAA']*3,
        'code_presentation': ['2013B']*3, 'assessment_type': ['TMA']*3, 'date': [7, 14, 21]})
    submissions = pd.DataFrame({'id_student': [1, 1, 2], 'id_assessment': [10, 11, 10],
                               'date_submitted': [7, 20, 16], 'is_banked': [0]*3})
    activity = pd.DataFrame({'id_student': [1, 1, 1], 'code_module': ['AAA']*3,
        'code_presentation': ['2013B']*3, 'date': [-2, 14, 20], 'sum_click': [2, 3, 99]})
    return {'studentInfo': info, 'studentRegistration': registration,
            'assessments': assessments, 'studentAssessment': submissions}, activity

class SnapshotTests(unittest.TestCase):
    def test_uci_question_mark_missing_values(self):
        with tempfile.TemporaryDirectory() as directory:
            for name in ['courses', 'studentInfo', 'studentRegistration', 'assessments', 'studentAssessment']:
                (Path(directory) / f'{name}.csv').write_text('date\n14\n?\n', encoding='utf-8')
            tables = load_tables(directory)
            self.assertEqual(tables['studentRegistration'].date.iloc[0], 14)
            self.assertTrue(pd.isna(tables['studentRegistration'].date.iloc[1]))

    def test_eligibility_and_inactive_retention(self):
        tables, activity = fixture()
        frame, counts = snapshot(tables, activity, 'AAA', '2013B', 14)
        self.assertEqual(frame.id_student.tolist(), [1, 2])
        self.assertEqual(frame.target.tolist(), [1, 0])
        self.assertEqual(frame.total_clicks.tolist(), [5, 0])
        self.assertEqual(frame.no_activity.tolist(), [0, 1])
        self.assertEqual(counts['excluded_invalid'], 1)

    def test_future_records_do_not_change_features(self):
        tables, activity = fixture()
        original, _ = snapshot(tables, activity, 'AAA', '2013B', 14)
        tables['studentAssessment'] = tables['studentAssessment'].loc[lambda x: x.date_submitted.le(14)]
        earlier, _ = snapshot(tables, activity.loc[activity.date.le(14)], 'AAA', '2013B', 14)
        assert_frame_equal(original, earlier)

    def test_overdue_requires_passed_deadline_and_observed_submission(self):
        tables, activity = fixture()
        frame, _ = snapshot(tables, activity, 'AAA', '2013B', 14)
        self.assertEqual(frame.assignments_due.tolist(), [1, 1])
        self.assertEqual(frame.overdue.tolist(), [0, 1])
        self.assertEqual(frame.submissions.tolist(), [1, 0])

    def test_feature_allowlist_excludes_outcomes(self):
        for features in GROUPS.values():
            self.assertFalse(set(features) & {'target', 'final_result', 'date_unregistration',
                                             'warning_days', 'id_student', 'score'})

class MetricsTests(unittest.TestCase):
    def test_exact_budget_and_ties(self):
        scores = np.ones(29)
        ix = top_indices(scores)
        self.assertEqual(len(ix), 2)
        np.testing.assert_array_equal(ix, top_indices(scores))

    def test_known_metrics(self):
        y = np.array([1, 1] + [0]*18)
        m = budget_metrics(y, np.arange(20, 0, -1))
        self.assertEqual(m['recall_at_10pct'], 1)
        self.assertEqual(m['precision_at_10pct'], 1)

    def test_paired_identity(self):
        frame = pd.DataFrame({'id_student': range(30), 'target': [0, 1]*15})
        scores = np.linspace(0, 1, 30)
        result = paired_bootstrap(frame, scores, scores,
            {'seed': 678, 'bootstrap_replicates': 50, 'alert_fraction': .1})
        self.assertTrue(all(r['ci_low'] == r['ci_high'] == 0 for r in result))

class ChronologyTests(unittest.TestCase):
    def test_overlapping_offering_rejected(self):
        tables = {'courses': pd.DataFrame({'code_module': ['AAA', 'AAA'],
            'code_presentation': ['2013B', '2014B'], 'module_presentation_length': [400, 240]}),
            'studentInfo': pd.DataFrame({'code_module': ['AAA'], 'code_presentation': ['2013B']})}
        config = {'cutoffs': [14, 28, 42], 'outcome_availability_lag_days': 30,
                  'minimum_development_enrollments': 1}
        with self.assertRaises(ValueError):
            select_offerings(tables, config)
        tables['courses'].loc[0, 'module_presentation_length'] = 240
        selection, _ = select_offerings(tables, config)
        self.assertEqual(selection['development'], '2013B')
        self.assertEqual(selection['test'], '2014B')

class ModelIntegrationTests(unittest.TestCase):
    def test_models_accept_unseen_categories_and_empty_numeric_feature(self):
        rng = np.random.default_rng(678)
        frame = pd.DataFrame({'id_student': range(100), 'target': [0, 1]*50,
            'highest_education': ['A', 'B']*50, 'total_clicks': rng.uniform(0, 10, 100),
            'submission_rate': np.full(100, np.nan)})
        features = ['highest_education', 'total_clicks', 'submission_rate']
        later = frame[features].iloc[:10].copy()
        later['highest_education'] = 'UNSEEN'
        later['total_clicks'] = np.nan
        config = {'seed': 678, 'cv_folds': 2, 'alert_fraction': .1}
        from threadpoolctl import threadpool_limits
        for kind in ['logistic', 'boosted']:
            model = fit_model(frame, features, kind, config)
            with threadpool_limits(limits=2):
                probabilities = model.predict_proba(later)[:, 1]
            self.assertTrue(np.isfinite(probabilities).all())
            self.assertTrue(((probabilities >= 0) & (probabilities <= 1)).all())

if __name__ == '__main__':
    unittest.main()
