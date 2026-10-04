# Measured October 4, 2026

Inputs: checked-in processed masters from main e36fa5a4bbec4464f27bbc87b28366e979a9efe0.
No live source refresh was run. Evaluation is revised-data research with t-2
release embargo, not a vintage backtest. Each origins CSV contains all candidate
predictions, actuals, available training end and frozen validation-choice blend.
JSON contains exact validation and test baseline comparisons.

Legacy metrics are independently recomputed using stored model binaries, the
legacy feature tables and stored test-derived blend weights. That flawed old
protocol is not directly comparable with the new rolling two-step forecasts.

Local: clean Python 3.10 venv, pinned requirements-test.txt; 12 tests passed.
Four isolated candidate bundles trained and serialized; metric gate rejected
US test RMSE as expected. No candidate was promoted. Retained legacy FastAPI
TestClient smoke: health and all four dashboard endpoints HTTP 200.
GitHub CI runs the same tests and regenerates rolling reports on Python 3.11.

Not measured: source vintage availability, fresh API fetch, deployment, calibrated
uncertainty or 8-quarter forecast quality. Existing deployment binaries, feature
CSVs, summary CSV and frontend snapshot are intentionally retained unchanged.
