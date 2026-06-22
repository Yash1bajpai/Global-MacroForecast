# 📈 Global MacroForecast | GDP Nowcasting Engine

An end-to-end, full-stack macroeconomic forecasting system designed to predict Quarter-on-Quarter (QoQ) GDP growth for four major global economies: **United States, Germany, Japan, and India**. 

Built with an ultra-premium "Data Journalism" aesthetic, this system utilizes a dynamically weighted **Machine Learning Ensemble** to forecast up to 8 quarters into the future.

---

## 🎯 Model Performance & Accuracy

Our rigorous chronological hold-out validation ensures zero future-data leakage. The ensemble model (combining LightGBM and SARIMA) achieves the following metrics on unseen test data:

| Economy | Directional Accuracy (Hit Rate) | Test RMSE (Error Margin) | Dominant Model in Ensemble |
| :--- | :--- | :--- | :--- |
| **🇺🇸 United States** | **87.5%** | 2.30% | LightGBM (51%) |
| **🇮🇳 India** | **84.2%** | 4.60% | LightGBM (100%) |
| **🇯🇵 Japan** | **75.0%** | 1.73% | LightGBM (53%) |
| **🇩🇪 Germany** | **70.8%** | 2.54% | LightGBM (51%) |

*Note: Directional Accuracy represents the model's ability to correctly predict whether the GDP will expand or contract/slow down relative to the previous quarter.*

---

## ✨ Key Features

- **Live Macroeconomic Forecasting:** Generates 8-quarter (2-year) forward-looking predictions for GDP growth.
- **Ensemble ML Architecture:** Combines the non-linear relationship capturing power of **LightGBM** with the strong linear trend and seasonality tracking of **SARIMA**. Inverse RMSE Weighting (`weight = 1/RMSE`) automatically favors the model with the lowest historical error per country.
- **High-Performance FastAPI Backend:** Models and processed DataFrames are cached in-memory upon server lifespan startup, eliminating disk I/O bottlenecks and ensuring sub-millisecond API response times.
- **Premium Fintech UI/UX:** A responsive, dark "Deep Space" themed landing page built in Vanilla HTML/CSS/JS. Features interactive expanding country cards, smooth-tension `Chart.js` rendering, and floating geometric backgrounds.

---

## 🛠️ Technology Stack

**Backend (Machine Learning & API):**
* Python 3.10+
* FastAPI & Uvicorn (High-performance Async API)
* LightGBM (Gradient Boosted Decision Trees)
* Statsmodels (SARIMA)
* Pandas & Scikit-Learn (Data Preprocessing & Feature Engineering)

**Frontend (Dashboard):**
* HTML5 (Semantic Structure)
* CSS3 (Grid/Flexbox, Glassmorphism, CSS Variables)
* Vanilla JavaScript (ES6+ Asynchronous Fetching & DOM Manipulation)
* Chart.js (Data Visualization)

**Data Sources:**
* FRED (Federal Reserve Economic Data) API
* World Bank Open Data

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
*© 2026 EconEngine Intelligence. All rights reserved.*
