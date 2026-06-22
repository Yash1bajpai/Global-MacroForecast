# 📈 Global MacroForecast | GDP Nowcasting Engine

An end-to-end, full-stack macroeconomic forecasting system designed to predict Quarter-on-Quarter (QoQ) GDP growth for four major global economies: **United States, Germany, Japan, and India**. 

Built with an ultra-premium "Data Journalism" aesthetic, this system utilizes a dynamically weighted **Machine Learning Ensemble** to forecast up to 8 quarters into the future.

---

## 🎯 Model Performance & Accuracy

Our rigorous chronological hold-out validation ensures zero future-data leakage. The ensemble model (combining LightGBM and SARIMA) achieves the following metrics on unseen test data (**Test period: 2020 Q1 → Present**):

### 📊 Initial Baseline (v1.0 — Default Parameters)

| Economy | Directional Acc | RMSE | MSE | MAE | Ensemble |
| :--- | :---: | :---: | :---: | :---: | :--- |
| 🇺🇸 **United States** | **87.5%** | 2.3009 | 5.2940 | 1.1249 | LGBM 51% + SARIMA 49% |
| 🇯🇵 **Japan** | 75.0% | 1.6300 | 2.6569 | ~0.97 | LGBM 53% + SARIMA 47% |
| 🇩🇪 **Germany** | 70.8% | 2.5100 | 6.3001 | ~1.10 | LGBM 51% + SARIMA 49% |
| 🇮🇳 **India** | **84.2%** | 4.6015 | 21.174 | 2.7392 | LGBM 100% (no SARIMA) |

### 🏆 Final Tuned (v1.3 — After Optuna Hyperparameter Tuning)

| Economy | Directional Acc | RMSE | MAE | Improvement | Ensemble |
| :--- | :---: | :---: | :---: | :---: | :--- |
| 🇺🇸 **United States** | **87.5%** | 2.3009 | 1.1249 | — (kept baseline) | LGBM 51% + SARIMA 49% |
| 🇯🇵 **Japan** | 75.0% | **1.6153** | **0.9673** | ↓ 0.9% | LGBM 56% + SARIMA 44% |
| 🇩🇪 **Germany** | 70.8% | **2.4179** | **1.1262** | ↓ 3.7% | LGBM 53% + SARIMA 47% |
| 🇮🇳 **India** | **84.2%** | **4.2507** | **2.4191** | ↓ 7.6% | LGBM 100% (no SARIMA) |

*Directional Accuracy = model's ability to correctly predict GDP expansion vs contraction relative to the prior quarter.*

---

## ⚙️ Hyperparameter Tuning — Optuna (Kaggle)

Models were tuned using **Optuna v4.2 (TPE Sampler, `multivariate=True`)** on Kaggle's free GPU environment, running **30 trials per country** with a strictly constrained search space designed for small datasets (~80–100 rows):

| Country | `learning_rate` | `max_depth` | `num_leaves` | `n_estimators` | `subsample` | `colsample_bytree` |
|---------|:---:|:---:|:---:|:---:|:---:|:---:|
| 🇺🇸 US | 0.030 | 3 | 8 | 100 | 0.70 | 0.70 |
| 🇯🇵 Japan | 0.091 | 3 | 12 | 150 | 0.72 | 0.92 |
| 🇩🇪 Germany | 0.054 | 4 | 17 | 200 | 0.72 | 0.73 |
| 🇮🇳 India | 0.034 | 3 *(fixed)* | 8 *(fixed)* | 200 | 0.57 | 0.78 |

> **India note:** Optuna suggested `max_depth=6` but this was manually overridden to `3` — India's GDP data is annual World Bank data forward-filled to quarterly (~25 unique values across 100 rows). Deep trees memorize noise, not patterns.

---

## ✨ Key Features

- **Live Macroeconomic Forecasting:** Generates 8-quarter (2-year) forward-looking predictions for GDP growth.
- **Ensemble ML Architecture:** Combines the non-linear relationship capturing power of **LightGBM** with the strong linear trend and seasonality tracking of **SARIMA**. Inverse RMSE Weighting (`weight = 1/RMSE`) automatically favors the model with the lowest historical error per country.
- **Optuna Hyperparameter Tuning:** Country-specific LightGBM parameters tuned via Bayesian optimization (TPE) on Kaggle, with search space explicitly constrained to prevent overfitting on small macroeconomic datasets.
- **High-Performance FastAPI Backend:** Models and processed DataFrames are cached in-memory upon server lifespan startup, eliminating disk I/O bottlenecks and ensuring sub-millisecond API response times.
- **Premium Fintech UI/UX:** A responsive, dark "Deep Space" themed landing page built in Vanilla HTML/CSS/JS. Features interactive expanding country cards, smooth-tension `Chart.js` rendering, and floating geometric backgrounds.
- **Zero Data Leakage:** Strict chronological train/test split (cutoff: 2019 Q4). All lag features use `.shift()` validated by unit tests with 1e-6 tolerance.

---

## 🛠️ Technology Stack

**Backend (Machine Learning & API):**
* Python 3.10+
* FastAPI & Uvicorn (High-performance Async API)
* LightGBM (Gradient Boosted Decision Trees)
* Statsmodels (SARIMA)
* Optuna (Bayesian Hyperparameter Optimization)
* Pandas & Scikit-Learn (Data Preprocessing & Feature Engineering)

**Frontend (Dashboard):**
* HTML5 (Semantic Structure)
* CSS3 (Grid/Flexbox, Glassmorphism, CSS Variables)
* Vanilla JavaScript (ES6+ Asynchronous Fetching & DOM Manipulation)
* Chart.js (Data Visualization)

**Data Sources:**
* FRED (Federal Reserve Economic Data) API
* World Bank Open Data
* OECD Leading Indicators

---

## 🚀 How to Run Locally

### 1. Clone the Repository
```bash
git clone https://github.com/Yash1bajpai/Global-MacroForecast.git
cd Global-MacroForecast
```

### 2. Set Up the Python Environment
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Mac/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Start the FastAPI Backend
Start the high-performance API server. The models will cache into memory on startup.
```bash
python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload
```

### 4. Start the Frontend Dashboard
In a **new terminal window**, navigate to the project root and serve the static files:
```bash
python -m http.server 8080 --directory frontend
```
*Open your browser and navigate to `http://127.0.0.1:8080/index.html` to view the application.*

---

## 👨‍💻 Author

**Built by Yash Bajpai**
* 💼 **LinkedIn:** [Yash Bajpai](https://linkedin.com/in/yash-bajpai-b5a86332a)

---
*© 2026 Global MacroForecast. All rights reserved.*
