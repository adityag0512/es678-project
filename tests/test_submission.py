"""Regression checks for frozen-score budget exploration."""
import unittest
import pandas as pd
from withdrawal.submission import explore, R

class ExplorerTests(unittest.TestCase):
    def test_primary_budget_matches_saved_metrics(self):
        reference = pd.read_csv(R / 'reference_metrics.csv')
        for day in [14, 28, 42]:
            for population in ['dynamic', 'common']:
                table = explore(day, population, 10)
                for row in table.itertuples():
                    expected = reference.loc[reference.cutoff.eq(day) & reference.population.eq(population) & reference.model.eq(row.model)].iloc[0]
                    self.assertAlmostEqual(row.recall_at_10pct, expected.recall_at_10pct)
                    self.assertEqual(row.alerts, expected.alerts)

    def test_larger_budget_never_reduces_detected_withdrawals(self):
        for population in ['dynamic', 'common']:
            small = explore(28, population, 5).set_index('model')
            large = explore(28, population, 20).set_index('model')
            self.assertTrue((large.true_positives >= small.true_positives).all())
            self.assertTrue((large.alerts > small.alerts).all())

if __name__ == '__main__':
    unittest.main()
