"""Frontend public-claims consistency tests.

The country cards once carried hardcoded accuracy, confidence and
model-composition claims that drifted away from (or flattered) the served
models. These tests keep stale claims out, keep the composition pill tied to
the served metrics, require the experimental-status notice, and keep the
static snapshot consistent with data/processed/model_summary.csv.
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "frontend" / "index.html"
STATIC = ROOT / "frontend" / "data" / "forecasts.json"
JS = ROOT / "frontend" / "js" / "dashboard.js"
API = ROOT / "src" / "api" / "main.py"
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
        cls.js = JS.read_text(encoding="utf-8")
        cls.api = API.read_text(encoding="utf-8")
        cls.static = json.loads(STATIC.read_text(encoding="utf-8"))

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

    def test_paused_notice_and_provenance_link(self):
        self.assertIn("forecast-paused-notice", self.html)
        self.assertIn("Forecasts are paused while the models are under repair", self.html)
        self.assertIn("github.com/Yash1bajpai/Global-MacroForecast", self.html)

    def test_page_shows_no_forecast_or_accuracy_language(self):
        for phrase in ("8-Quarter Forecast", "NEXT QTR FORECAST", "Ensemble Forecast",
                       "Model Composition", "Confidence", "accuracy of"):
            self.assertNotIn(phrase, self.html)

    def test_static_snapshot_is_history_only(self):
        self.assertEqual(self.static["status"], "forecasts_paused")
        for c in COUNTRIES:
            self.assertEqual(set(self.static[c]), {"history"})
            self.assertGreaterEqual(len(self.static[c]["history"]), 12)
            self.assertTrue(all(isinstance(v, float) for v in self.static[c]["history"].values()))

    def test_frontend_never_calls_forecast_endpoints(self):
        for token in ("/api/", "ensemble_pred", "ci_low", "ci_high", "w_lgbm", "API_BASE_URL"):
            self.assertNotIn(token, self.js)

    def test_api_forecast_metric_endpoints_are_paused_history_stays(self):
        import re
        for name in ("get_metrics", "get_forecast", "get_dashboard_data"):
            body = re.search(rf"def {name}\(.*?\n\n\n", self.api, re.S).group(0)
            self.assertIn("_forecasts_paused()", body, name)
            self.assertNotIn("ensemble", body, name)
        self.assertIn("status_code=503", self.api)
        hist = re.search(r"def get_history\(.*?\n\n\n", self.api, re.S).group(0)
        self.assertNotIn("_forecasts_paused", hist)


if __name__ == "__main__":
    unittest.main()
