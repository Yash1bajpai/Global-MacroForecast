"""Causal invariance, split, model selection, baseline and promotion tests."""
import copy
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
from src.data.build_features import causal_features, COUNTRIES
from src.models.validation import train_indices, select, blend, metrics, quality_gate, evaluate

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    index = pd.date_range('2004-01-01', periods=84, freq='QS')
    x = np.arange(len(index))
    return pd.DataFrame(dict(gdp_growth=1+np.sin(x)*.2, cpi_growth=x*.01,
                             recession=x%2, covid_shock=x%2, wb_gdp_growth_pct=x*5), index=index)


class PipelineTests(unittest.TestCase):
    def test_current_and_previous_and_future_values_cannot_change_features(self):
        master = fixture()
        original = causal_features(master)
        for i in (20, 30, 60):
            changed = master.copy()
            changed.iloc[i-1:] += 999
            candidate = causal_features(changed)
            pd.testing.assert_series_equal(original.drop(columns='gdp_growth').iloc[i],
                                           candidate.drop(columns='gdp_growth').iloc[i])

    def test_feature_whitelist(self):
        cols = causal_features(fixture()).columns
        self.assertNotIn('recession', cols)
        self.assertNotIn('covid_shock', cols)
        self.assertFalse(any('wb_' in c for c in cols))
        self.assertNotIn('gdp_growth_lag1', cols)
        self.assertNotIn('cpi_growth', cols)

    def test_embargo(self):
        index = fixture().index
        origin = index[30]
        self.assertEqual(index[train_indices(index, origin)][-1], index[28])

    def test_gap_and_duplicate_fail(self):
        with self.assertRaises(ValueError):
            causal_features(fixture().drop(fixture().index[30]))
        with self.assertRaises(ValueError):
            causal_features(pd.concat([fixture(), fixture().iloc[[-1]]]))

    def test_metrics_known_values_and_invalid(self):
        result = metrics([1, -1], [2, -2])
        self.assertEqual(result['rmse'], 1.)
        self.assertEqual(result['sign_accuracy'], 100.)
        for a, p in [([], []), ([1], [np.nan]), ([1], [1, 2])]:
            with self.assertRaises(ValueError):
                metrics(a, p)

    def test_selection_uses_only_validation(self):
        v = pd.DataFrame(dict(actual=[1., 2.], lgbm_0=[1., 2.], lgbm_1=[4., 5.],
                              sarima_0=[8., 9.], sarima_1=[7., 8.]))
        selection = select(v)
        self.assertEqual(selection['w_sarima'], 0.)
        self.assertEqual(selection['lgbm_config'], 0)
        self.assertTrue(np.array_equal(blend(v, selection), [1., 2.]))

    def test_invalid_sarima_excluded(self):
        v = pd.DataFrame(dict(actual=[1., 2.], lgbm_0=[1., 2.], lgbm_1=[4., 5.],
                              sarima_0=[None, None], sarima_1=[None, None]))
        self.assertEqual(select(v)['w_sarima'], 0.)

    def test_gate_rejects_no_skill_missing_incumbent_changed_dates_regression_nan(self):
        metric = dict(rmse=1., mae=1.)
        c = dict(protocol='revised-data-t2-embargo-v1', test_start='2020', test_end='2026', test_n=26)
        for split in ['validation', 'test']:
            c[split] = {k: dict(metric) for k in ['ensemble', 'mean', 'last', 'seasonal']}
            c[split]['ensemble'] = dict(rmse=.5, mae=.5)
        candidate = {country: copy.deepcopy(c) for country in COUNTRIES}
        quality_gate(candidate, copy.deepcopy(candidate))
        for mode in ('baseline', 'nan', 'regression', 'date', 'protocol'):
            bad = copy.deepcopy(candidate)
            if mode == 'protocol':
                bad['us']['protocol'] = 'legacy'
            elif mode == 'date':
                bad['us']['test_end'] = '2027'
            else:
                bad['us']['test']['ensemble']['rmse'] = {'baseline': 1., 'nan': np.nan, 'regression': .6}[mode]
            with self.assertRaises(ValueError):
                quality_gate(bad, candidate)
        with self.assertRaises(ValueError):
            quality_gate(candidate)

    def test_real_country_features_and_finite_fit(self):
        from src.models.validation import fit_lgbm, CONFIGS
        for country in COUNTRIES:
            master = pd.read_csv(ROOT / f'data/processed/{country}_master.csv', index_col=0, parse_dates=True)
            df = causal_features(master)
            model = fit_lgbm(df.drop(columns='gdp_growth').iloc[:-2], df.gdp_growth.iloc[:-2], CONFIGS[0])
            self.assertTrue(np.isfinite(model.predict(df.drop(columns='gdp_growth').iloc[-2:])).all())

    def test_test_labels_do_not_change_validation_choice_or_first_test_prediction(self):
        master = fixture()
        first, predictions = evaluate(master)
        changed = master.copy()
        changed.loc[changed.index >= '2020-01-01', 'gdp_growth'] += 500
        second, changed_predictions = evaluate(changed)
        self.assertEqual(first['choice'], second['choice'])
        self.assertEqual(predictions.loc['2020-01-01T00:00:00', 'ensemble'],
                         changed_predictions.loc['2020-01-01T00:00:00', 'ensemble'])
        self.assertNotEqual(first['test']['mean']['rmse'], second['test']['mean']['rmse'])

    def test_saved_reports_have_consistent_predictions_and_dates(self):
        import json
        reports = json.loads((ROOT / 'reports/evaluation.json').read_text())
        for country in COUNTRIES:
            frame = pd.read_csv(ROOT / f'reports/{country}_origins.csv', index_col=0)
            test = frame[pd.to_datetime(frame.index) >= '2020-01-01']
            measured = metrics(test.actual, test.ensemble)
            self.assertEqual(len(test), reports[country]['test_n'])
            for metric in ['rmse', 'mae', 'sign_accuracy']:
                self.assertAlmostEqual(measured[metric], reports[country]['test']['ensemble'][metric], places=10)

    def test_full_synthetic_rolling_run(self):
        report, origins = evaluate(fixture())
        self.assertEqual(report['validation_n'], 16)
        self.assertTrue(np.isfinite(origins.ensemble).all())
        dates = pd.to_datetime(origins.index)
        train_ends = pd.to_datetime(origins.train_end)
        self.assertTrue((train_ends <= dates - pd.DateOffset(months=6)).all())


if __name__ == '__main__':
    unittest.main(verbosity=2)
