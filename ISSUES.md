# 🚧 Known Issues & Technical Debt

This document tracks current limitations, known bugs, and the roadmap for future enhancements. It demonstrates our commitment to transparency and continuous improvement.

## 🔴 Known Limitations

### 1. India SARIMA Model Omission
- **Description:** Currently, the Indian economy relies solely on a 100% LightGBM baseline model (`india_lgbm.pkl`).
- **Root Cause:** Lack of high-frequency (quarterly), historically deep macroeconomic indicators from public APIs compared to the US or Germany. Statistical models like SARIMA require strict seasonal continuous data which was heavily interpolated for India, causing unacceptable confidence intervals.
- **Workaround:** Exclusively using tree-based LightGBM for India until a better high-frequency data source (e.g., RBI direct APIs) is integrated.

### 2. Manual MOCK_DATA Synchronization
- **Description:** The frontend offline fallback mode relies on a hardcoded `MOCK_DATA` JavaScript object in `dashboard.js`.
- **Root Cause:** If the backend API schema changes, the frontend will crash when running in offline mode unless `dashboard.js` is manually updated.
- **Future Fix:** Write an automated python script or CI/CD hook that dumps the latest API payload into a `.json` file that the frontend consumes.

## 🔵 Roadmap & Future Enhancements

### 1. Docker Containerization
- **Goal:** Create a `Dockerfile` and `docker-compose.yml` to package the FastAPI backend and Nginx static frontend into a single deployable artifact.

### 2. Multi-Threading Data Ingestion
- **Goal:** Currently, the `fetch_all.py` script downloads FRED data sequentially. Upgrading to `asyncio` and `aiohttp` would reduce pipeline build time by ~70%.

### 3. Exogenous Shock Scenarios
- **Goal:** Add a "Scenario Testing" feature to the UI where users can input custom Interest Rate hikes or CPI spikes and watch how the ensemble models adjust the GDP forecast in real-time.
