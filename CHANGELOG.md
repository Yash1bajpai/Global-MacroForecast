# 📜 Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2026-06-21
### Added
- **Production FastAPI Backend:** Implemented `@asynccontextmanager lifespan` caching for zero-latency ML model inferences.
- **REST APIs:** Established `/api/history`, `/api/forecast`, and `/api/metrics` endpoints.
- **Premium Frontend:** Completely overhauled the UI from a basic dashboard to a "Data Journalism" landing page aesthetic.
- **Interactive UI:** Added dynamically expanding Country Cards with `Chart.js` rendering historical and forecast data.
- **Ensemble Validation:** Added Accuracy Proof methodologies and transparent Data Source tracking to the frontend.

## [0.9.0] - 2026-06-20
### Added
- **Ensemble Weighting:** Implemented Inverse RMSE Weighting to combine SARIMA and LightGBM models dynamically.
- **Model Deployment:** Exported 8 finalized `.pkl` models to `models_saved/` directory.
- **India Baseline:** Added LightGBM baseline forecasting for the Indian economy.

## [0.5.0] - 2026-06-18
### Added
- **Macro Feature Engineering:** Created strict lagged datasets (`us_features.csv`, etc.) ensuring zero future-data leakage.
- **EDA Pipelines:** Performed Stationarity checks (ADF Tests), PACF/ACF plotting, and distribution analysis for all four economies.
- **Data Ingestion:** Fully automated data extraction pipelines from FRED API and World Bank open data.
