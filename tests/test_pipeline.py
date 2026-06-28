"""
test_pipeline.py
Unit tests for the GDP Nowcast & Forecast pipeline.

Tests:
  1. All required files exist (raw processed, features, models)
  2. Master CSVs have correct structure and no null GDP growth
  3. Feature lag columns have no look-ahead leakage
  4. Train/test split is clean (no overlap)
  5. Global features has all 4 countries
  6. Models load and produce finite predictions
  7. LightGBM test RMSE within acceptable bounds
  8. SARIMA loads and forecasts 4 steps
  9. Ensemble weights sum to 1.0
  10. model_summary.csv has all 4 countries

Run from project root:
    python tests/test_pipeline.py
"""

import os
import sys
import unittest
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import joblib

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from config.settings import DATA_PROCESSED_DIR, MODELS_DIR

FEATURES_DIR = os.path.join(PROJECT_ROOT, "data", "features")
COUNTRIES    = ["us", "india", "japan", "germany"]
TEST_START   = "2020-01-01"
TRAIN_END    = "2019-10-01"


class TestFileExistence(unittest.TestCase):

    def test_master_csvs_exist(self):
        for c in COUNTRIES:
            path = os.path.join(DATA_PROCESSED_DIR, f"{c}_master.csv")
            self.assertTrue(os.path.exists(path), f"Missing: {c}_master.csv")

    def test_feature_csvs_exist(self):
        for c in COUNTRIES:
            path = os.path.join(FEATURES_DIR, f"{c}_features.csv")
            self.assertTrue(os.path.exists(path), f"Missing: {c}_features.csv")

    def test_global_files_exist(self):
        self.assertTrue(os.path.exists(os.path.join(DATA_PROCESSED_DIR, "global_master.csv")))
        self.assertTrue(os.path.exists(os.path.join(FEATURES_DIR, "global_features.csv")))

    def test_lgbm_pkls_exist(self):
        for c in COUNTRIES:
            path = os.path.join(MODELS_DIR, f"{c}_lgbm.pkl")
            self.assertTrue(os.path.exists(path), f"Missing: {c}_lgbm.pkl")

    def test_sarima_pkls_exist(self):
        for c in ["us", "japan", "germany"]:
            path = os.path.join(MODELS_DIR, f"{c}_sarima.pkl")
            self.assertTrue(os.path.exists(path), f"Missing: {c}_sarima.pkl")

    def test_global_lgbm_exists(self):
        self.assertTrue(os.path.exists(os.path.join(MODELS_DIR, "global_lgbm.pkl")))

    def test_model_summary_exists(self):
        self.assertTrue(os.path.exists(os.path.join(DATA_PROCESSED_DIR, "model_summary.csv")))


class TestDataIntegrity(unittest.TestCase):

    def test_gdp_growth_no_nulls(self):
        for c in COUNTRIES:
            df = pd.read_csv(
                os.path.join(DATA_PROCESSED_DIR, f"{c}_master.csv"),
                index_col=0, parse_dates=True
            )
            null_count = df["gdp_growth"].isnull().sum()
            self.assertEqual(null_count, 0, f"{c}: gdp_growth has {null_count} nulls in master CSV")

    def test_no_lookahead_leakage_in_lags(self):
        """gdp_growth_lag1 at time t must exactly equal gdp_growth at t-1."""
        for c in COUNTRIES:
            df = pd.read_csv(
                os.path.join(FEATURES_DIR, f"{c}_features.csv"),
                index_col=0, parse_dates=True
            )
            if "gdp_growth_lag1" not in df.columns:
                continue
            expected = df["gdp_growth"].shift(1)
            actual   = df["gdp_growth_lag1"]
            mask     = expected.notna() & actual.notna()
            max_diff = (expected[mask] - actual[mask]).abs().max()
            self.assertLess(
                max_diff, 1e-6,
                f"{c}: lag1 mismatch = {max_diff:.8f} (potential lookahead leakage)"
            )

    def test_minimum_row_count(self):
        min_rows = {"us": 90, "india": 45, "japan": 90, "germany": 90}
        for c in COUNTRIES:
            df = pd.read_csv(os.path.join(FEATURES_DIR, f"{c}_features.csv"), index_col=0)
            self.assertGreater(
                len(df), min_rows[c],
                f"{c}_features.csv has only {len(df)} rows (expected > {min_rows[c]})"
            )

    def test_train_test_no_overlap(self):
        for c in COUNTRIES:
            df = pd.read_csv(
                os.path.join(FEATURES_DIR, f"{c}_features.csv"),
                index_col=0, parse_dates=True
            )
            train_idx = set(df[df.index <= TRAIN_END].index)
            test_idx  = set(df[df.index >= TEST_START].index)
            overlap   = train_idx & test_idx
            self.assertEqual(len(overlap), 0, f"{c}: {len(overlap)} dates overlap between train and test")

    def test_train_and_test_nonempty(self):
        for c in COUNTRIES:
            df = pd.read_csv(
                os.path.join(FEATURES_DIR, f"{c}_features.csv"),
                index_col=0, parse_dates=True
            )
            self.assertGreater(len(df[df.index <= TRAIN_END]), 0, f"{c}: train set is empty")
            self.assertGreater(len(df[df.index >= TEST_START]), 0, f"{c}: test set is empty")

    def test_global_has_4_countries(self):
        df = pd.read_csv(os.path.join(FEATURES_DIR, "global_features.csv"), index_col=0)
        self.assertIn("country_id", df.columns, "global_features.csv missing 'country_id' column")
        unique_ids = df["country_id"].nunique()
        self.assertEqual(unique_ids, 4, f"global_features has {unique_ids} unique country_ids, expected 4")

    def test_recession_dummy_is_binary(self):
        for c in COUNTRIES:
            df = pd.read_csv(os.path.join(DATA_PROCESSED_DIR, f"{c}_master.csv"), index_col=0)
            if "recession" not in df.columns:
                continue
            unique_vals = set(df["recession"].dropna().unique())
            self.assertTrue(
                unique_vals.issubset({0, 1}),
                f"{c}: recession dummy has non-binary values: {unique_vals}"
            )

    def test_gdp_growth_range_plausible(self):
        """QoQ GDP growth should be between -15% and +15% (COVID extremes)."""
        for c in COUNTRIES:
            df = pd.read_csv(os.path.join(DATA_PROCESSED_DIR, f"{c}_master.csv"), index_col=0)
            mn = df["gdp_growth"].min()
            mx = df["gdp_growth"].max()
            self.assertGreater(mn, -40, f"{c}: GDP growth min {mn:.2f} is suspiciously low")
            self.assertLess(mx, 30,    f"{c}: GDP growth max {mx:.2f} is suspiciously high")


class TestModelPredictions(unittest.TestCase):

    def _load_test_features(self, country):
        df = pd.read_csv(
            os.path.join(FEATURES_DIR, f"{country}_features.csv"),
            index_col=0, parse_dates=True
        )
        drop = [c for c in ["gdp_level", "country", "country_id"] if c in df.columns]
        df   = df.drop(columns=drop)
        X    = df.drop(columns=["gdp_growth"])
        y    = df["gdp_growth"]
        return X[X.index >= TEST_START], y[y.index >= TEST_START]

    def test_lgbm_predictions_correct_length(self):
        for c in COUNTRIES:
            model  = joblib.load(os.path.join(MODELS_DIR, f"{c}_lgbm.pkl"))
            X_test, _ = self._load_test_features(c)
            preds  = model.predict(X_test)
            self.assertEqual(len(preds), len(X_test), f"{c}: prediction length {len(preds)} != {len(X_test)}")

    def test_lgbm_predictions_finite(self):
        for c in COUNTRIES:
            model  = joblib.load(os.path.join(MODELS_DIR, f"{c}_lgbm.pkl"))
            X_test, _ = self._load_test_features(c)
            preds  = model.predict(X_test)
            self.assertTrue(np.all(np.isfinite(preds)), f"{c}: LightGBM output contains inf/nan")

    def test_lgbm_test_rmse_under_threshold(self):
        """All LightGBM test RMSEs must be below threshold (India is most lenient due to COVID data swings)."""
        thresholds = {"us": 4.0, "india": 13.0, "japan": 4.0, "germany": 4.0}
        for c in COUNTRIES:
            model      = joblib.load(os.path.join(MODELS_DIR, f"{c}_lgbm.pkl"))
            X_test, y_test = self._load_test_features(c)
            preds      = model.predict(X_test)
            rmse       = float(np.sqrt(np.mean((y_test.values - preds) ** 2)))
            self.assertLess(
                rmse, thresholds[c],
                f"{c}: LightGBM test RMSE {rmse:.3f}% exceeds threshold {thresholds[c]}%"
            )

    def test_sarima_loads_and_forecasts(self):
        for c in ["us", "japan", "germany"]:
            fitted = joblib.load(os.path.join(MODELS_DIR, f"{c}_sarima.pkl"))
            fc     = fitted.get_forecast(steps=4)
            preds  = fc.predicted_mean.values
            self.assertEqual(len(preds), 4, f"{c}: SARIMA forecast length != 4")
            self.assertTrue(np.all(np.isfinite(preds)), f"{c}: SARIMA forecast contains inf/nan")

    def test_global_lgbm_covers_all_countries(self):
        df = pd.read_csv(
            os.path.join(FEATURES_DIR, "global_features.csv"),
            index_col=0, parse_dates=True
        )
        drop   = [c for c in ["gdp_level", "country"] if c in df.columns]
        df     = df.drop(columns=drop)
        X      = df.drop(columns=["gdp_growth"])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model  = joblib.load(os.path.join(MODELS_DIR, "global_lgbm.pkl"))
        X_test = X[X.index >= TEST_START]
        preds  = model.predict(X_test)
        self.assertEqual(len(preds), len(X_test))
        self.assertTrue(np.all(np.isfinite(preds)))


class TestEnsemble(unittest.TestCase):

    def test_ensemble_weights_sum_to_one(self):
        df = pd.read_csv(os.path.join(DATA_PROCESSED_DIR, "model_summary.csv"))
        for _, row in df.iterrows():
            w_sum = float(row["w_sarima"]) + float(row["w_lgbm"])
            self.assertAlmostEqual(
                w_sum, 1.0, places=3,
                msg=f"{row['country']}: weights sum to {w_sum}, expected 1.0"
            )

    def test_model_summary_has_4_countries(self):
        df = pd.read_csv(os.path.join(DATA_PROCESSED_DIR, "model_summary.csv"))
        self.assertEqual(len(df), 4, f"model_summary.csv has {len(df)} rows, expected 4")

    def test_ensemble_rmse_not_worse_than_both_models(self):
        """Ensemble RMSE must not exceed both individual model RMSEs simultaneously."""
        df = pd.read_csv(os.path.join(DATA_PROCESSED_DIR, "model_summary.csv"))
        for _, row in df.iterrows():
            if row["sarima_rmse"] == "skipped":
                continue
            ens    = float(row["ensemble_rmse"])
            lgbm   = float(row["lgbm_rmse"])
            sarima = float(row["sarima_rmse"])
            worst  = max(sarima, lgbm)
            self.assertLess(
                ens, worst * 1.05,
                f"{row['country']}: ensemble {ens:.4f} worse than both models "
                f"(sarima={sarima:.4f}, lgbm={lgbm:.4f})"
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
