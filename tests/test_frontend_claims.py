"""Frontend public-claims consistency tests.

The country cards once carried hardcoded accuracy, confidence and
model-composition claims that drifted away from (or flattered) the served
models. These tests keep stale claims out, keep the composition pill tied to
the served metrics, require the experimental-status notice, and keep the
static snapshot consistent with data/processed/model_summary.csv.
"""
import csv
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "frontend" / "index.html"
STATIC = ROOT / "frontend" / "data" / "forecasts.json"
SUMMARY = ROOT / "data" / "processed" / "model_summary.csv"
COUNTRIES = ["us", "india", "japan", "germany"]

STALE_CLAIMS = [
    # Pre-fix leaky accuracy figures and their labels
    "DIR ACCURACY", "87.5%", "84.2%", "70.8%", "75.0%",
    "TEST RMSE", "BACKTEST RMSE", "BACKTEST MAE",
    # Unsupported confidence and composition claims
    "High Confidence", "Medium Confidence", "Pure AI", "LightGBM 100%",
    # Other stale claims
    "40+", "Key Drivers", "Accuracy Proof", "API Asleep",
    "dynamically weighted", "Bundesbank", "Bank of Japan",
]


class FrontendClaimsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = INDEX.read_text(encoding="utf-8")
        cls.static = json.loads(STATIC.read_text(encoding="utf-8"))
        with SUMMARY.open(newline="", encoding="utf-8") as f:
            cls.summary = {r["country"].lower(): r for r in csv.DictReader(f)}

    def test_no_stale_hardcoded_claims(self):
        for claim in STALE_CLAIMS:
            self.assertNotIn(claim, self.html)

    def test_no_metric_elements_left_on_cards(self):
        for c in COUNTRIES:
            self.assertNotIn(f'id="rmse-{c}"', self.html)
            self.assertNotIn(f'id="mae-{c}"', self.html)
            self.assertIn(f'id="comp-{c}"', self.html)
            self.assertIn(f'id="val-{c}"', self.html)
            self.assertIn(f'id="trend-{c}"', self.html)

    def test_experimental_notice_and_provenance_link(self):
        self.assertIn("experiment-notice", self.html)
        self.assertIn("Experimental research project", self.html)
        self.assertIn("github.com/Yash1bajpai/Global-MacroForecast", self.html)

    def test_static_snapshot_matches_model_summary(self):
        for c in COUNTRIES:
            sm, st = self.summary[c], self.static[c]["metrics"]
            for key in ("ensemble_rmse", "ensemble_mae", "w_sarima", "w_lgbm"):
                self.assertAlmostEqual(float(sm[key]), float(st[key]), places=4,
                                       msg=f"{c} {key}")

    def test_served_metrics_are_finite_and_bounded(self):
        for c in COUNTRIES:
            m = self.static[c]["metrics"]
            self.assertGreater(m["ensemble_rmse"], 0)
            self.assertGreater(m["ensemble_mae"], 0)
            self.assertAlmostEqual(m["w_sarima"] + m["w_lgbm"], 1.0, places=6)


if __name__ == "__main__":
    unittest.main()
