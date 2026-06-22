# 📜 Changelog — Global MacroForecast (GDP Nowcasting Engine)

All notable changes, decisions, and resolved issues are documented here.
Format: **What changed → Why it was changed → Issue it solved.**

---

## [1.2.0] — 2026-06-22

### Changed
- **README title fixed:** "National Economic Intelligence" → "Global MacroForecast"
  - *Why:* The project covers 4 global economies (US, India, Japan, Germany). "National" was a misnomer. Repository is named `Global-MacroForecast` so the README title must match.
- **`src/__init__.py` fixed:** Removed broken `from . import settings`
  - *Why:* `settings.py` lives in `config/`, not `src/`. This import caused `ImportError` on server startup, blocking the entire API from loading.
- **CHANGELOG upgraded:** Added "why" context to every entry, not just "what"
  - *Why:* A CHANGELOG without reasoning is just a git log. Reviewers need to understand decisions, not just diffs.

### Removed from Git tracking
- `project_context_prompt.txt` — AI session context file, not project code
- `src/models/lgbm_model.py` — Empty stub file (never implemented)
- `src/features/engineer.py` — Empty stub file (never implemented)
- `src/features/features.py` — Empty stub file (never implemented)
- `src/models/var_model.py` — VAR model was considered but abandoned; leaving an empty file implies incomplete work

---

## [1.1.0] — 2026-06-21

### Added
- **`CHANGELOG.md`** — Project development history with version tracking
- **`ISSUES.md`** — Transparent tracking of known limitations and technical debt
- **`project_context_prompt.txt`** — *(Later removed from Git — see v1.2.0)*

### Changed
- **Terminology corrected across all docs:** "Inverse Variance Weighting" → "Inverse RMSE Weighting (`weight = 1/RMSE`)"
  - *Why:* The implementation literally computes `w = 1/RMSE`, not `1/variance`. Using wrong terminology in documentation is a credibility issue for technical reviewers.
- **Function names corrected in context docs:** `forecast_next_8_quarters()` → actual names `lgbm_forecast_recursive()`, `sarima_forecast()`, `ensemble_forecast()`, `run()`
  - *Why:* The documented function names didn't match the actual codebase. Any AI or developer using those docs would get `ImportError`.
- **Model count corrected:** "7 models" → "8 models (including `global_lgbm.pkl`)"
  - *Why:* `global_lgbm.pkl` was being excluded from counts. Inaccurate stats in documentation.
- **Data paths corrected:** `us_macro_features.csv` → actual paths `data/processed/us_master.csv`, `data/features/us_features.csv`
  - *Why:* The file `us_macro_features.csv` never existed in the project. Hallucinated path from early documentation.

---

## [1.0.0] — 2026-06-21 (Initial GitHub Release)

### Added — Backend
- **FastAPI server** (`src/api/main.py`) with 3 endpoints:
  - `GET /api/history/{country}` — last 20 quarters of historical GDP
  - `GET /api/forecast/{country}` — 8-quarter ensemble forecast with confidence intervals
  - `GET /api/metrics/{country}` — RMSE, MAE, ensemble weights
- **`@asynccontextmanager lifespan` caching** — All 8 `.pkl` models and 4 DataFrames loaded into RAM at server startup
  - *Why:* Without caching, every API call would read disk (100-300ms per call). With in-memory cache, response is <5ms. GDP data doesn't change mid-session.
- **Pydantic models** (`ForecastPoint`, `MetricsResponse`, `HealthResponse`) for request/response validation
- **`CountryCode` Enum** for path parameter validation — prevents arbitrary strings from reaching model inference
- **CORS configured via environment variable** `ALLOWED_ORIGINS`
  - *Why:* Hardcoding `allow_origins=["*"]` (open to all origins) is a security risk. Env-variable-driven CORS allows production deployment to restrict to specific domains.

### Added — Machine Learning
- **LightGBM models** for all 4 countries with chronological train/test split (cutoff: 2019 Q4 → 2020 Q1)
  - *Why:* Standard `train_test_split(shuffle=True)` causes data leakage in time series. Chronological split simulates real forecasting where future is unknown.
- **SARIMA(1,0,1)(0,0,0,4) models** for US, Japan, Germany
  - India excluded — *Why:* India only had annual World Bank GDP data (no quarterly FRED series). Annual data forward-filled to quarterly creates identical consecutive values, which SARIMA interprets as zero-variance and produces degenerate confidence intervals.
- **Inverse RMSE Weighting Ensemble**: `weight = 1/RMSE`, normalized so `w_sarima + w_lgbm = 1.0`
  - *Why:* Simple average ensemble ignores model quality differences. Giving more weight to the lower-error model produces a better combined forecast.
- **Recursive 1-step-ahead LightGBM forecasting** — GDP lags updated at each step with the previous step's prediction
  - *Why:* Naively feeding the same feature row for all 8 quarters ignores the fact that GDP lags (lag1, lag2, etc.) change as forecasts extend. Recursive updating correctly simulates real forecasting uncertainty growth.
- **Global LightGBM** (`global_lgbm.pkl`) — single model trained on all 4 countries with `country_id` as a feature
- **COVID shock + recession dummies** added as binary features
  - *Why:* Tree-based models cannot extrapolate beyond training data. A COVID dummy signals to the model that 2020 Q1-Q2 was structurally different, preventing those outliers from distorting normal period predictions.
- **23 unit tests** in `tests/test_pipeline.py` — all passing
  - Coverage: file existence, data integrity, zero data leakage validation, train/test non-overlap, model RMSE bounds, ensemble weight sum

### Added — Frontend
- **Premium "Data Journalism" Landing Page** replacing a basic admin dashboard
- **4 expanding Country Cards** (US, India, Germany, Japan) — click to expand 8-quarter chart
- **Chart.js integration** — dual-dataset chart (Historical solid blue / Forecast dashed yellow) with gradient fill, zero-line highlight, and custom tooltips
- **Offline MOCK_DATA fallback** in `dashboard.js` — allows frontend development/testing without backend
  - *Why:* During development, repeatedly starting the Python backend to test frontend changes is slow. Hardcoded real API data allows instant frontend iteration.
- **Mobile-responsive CSS** — `@media` breakpoints at 1024px (2-column) and 640px (1-column)
- **Safe DOM manipulation** — `textContent` and `createElement` used throughout (no `innerHTML`)
  - *Why:* `innerHTML` is an XSS attack vector if any API data is ever compromised. `textContent` prevents script injection.

### Added — Repository
- `.gitignore` — blocks `.venv/`, `__pycache__/`, `.env`, `logs/`, temp scripts
- `requirements.txt` — all dependencies pinned to exact versions
- `README.md` — setup instructions, API docs, model performance table, author links

---

## [0.5.0] — 2026-06-18 (Feature Engineering & EDA)

### Added
- **Automated FRED data pipeline** (`src/data/fetch_fred.py`) — CPI, M2, Fed Funds, Industrial Production, Unemployment
- **World Bank data pipeline** (`src/data/fetch_worldbank.py`) — annual GDP growth, trade balance, gross savings
- **OECD Leading Indicator pipeline** (`src/data/fetch_oecd.py`)
- **Stationarity testing** — ADF tests automated and results saved to `data/processed/eda_adf_results.csv`
- **Feature Engineering** (`data/features/`) — lag features (lag1-lag4), rolling means/std (2q, 4q), YoY growth
  - *Critical design decision:* All lag features computed using `.shift()` ensuring feature at time `t` only uses data from `t-1` and earlier. Validated by unit test `test_no_lookahead_leakage_in_lags` (tolerance: 1e-6).

---

## [0.1.0] — 2026-06-15 (Project Architecture)

### Added
- Project directory structure: `src/`, `data/`, `models_saved/`, `frontend/`, `tests/`, `config/`, `notebooks/`
- `config/settings.py` — centralized path management and FRED API key loading
- Initial ARIMA/VAR model exploration (later replaced by SARIMA + LightGBM ensemble)
  - *Why replaced:* Pure ARIMA ignores macroeconomic predictors (CPI, M2, Industrial Production). LightGBM ensemble captures non-linear relationships between macro indicators and GDP that ARIMA cannot model.
