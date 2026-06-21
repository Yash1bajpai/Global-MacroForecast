# 📈 National Economic Intelligence | GDP Nowcasting Engine

![Dashboard Preview](frontend/css/dashboard-preview.png) *(Note: You can add a screenshot of your dashboard here later)*

An end-to-end, full-stack macroeconomic forecasting system designed to predict Quarter-on-Quarter (QoQ) GDP growth for four major global economies: **United States, Germany, Japan, and India**. 

Built with an ultra-premium "Data Journalism" aesthetic, this system utilizes a dynamically weighted **Machine Learning Ensemble** to forecast up to 8 quarters into the future.

---

## ✨ Key Features

- **Live Macroeconomic Forecasting:** Generates 8-quarter (2-year) forward-looking predictions for GDP growth.
- **Ensemble ML Architecture:** Combines the non-linear relationship capturing power of **LightGBM** with the strong linear trend and seasonality tracking of **SARIMA**. Inverse RMSE Weighting (`weight = 1/RMSE`) automatically favors the model with the lowest historical error per country.
- **Strict Data Integrity:** Built with zero-future-leakage principles. Features rely strictly on lagged, past-dated macroeconomic indicators. Validated using chronological hold-out validation.
- **High-Performance FastAPI Backend:** Models and processed DataFrames are cached in-memory upon server lifespan startup, eliminating disk I/O bottlenecks and ensuring sub-millisecond API response times.
- **Premium Fintech UI/UX:** A responsive, dark "Deep Space" themed landing page built in Vanilla HTML/CSS/JS. Features interactive expanding country cards, smooth-tension `Chart.js` rendering, and floating geometric backgrounds.
- **Offline / Mock Mode:** Built-in UI toggle allows seamless switching between live FastAPI data and hardcoded fallback data for frontend UI testing.

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
git clone https://github.com/Yash1bajpai/GDP_Project.git
cd GDP_Project
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
*The API will be available at `http://127.0.0.1:8000/docs` (Swagger UI).*

### 4. Start the Frontend Dashboard
In a **new terminal window**, navigate to the project root and serve the static files:
```bash
python -m http.server 8080 --directory frontend
```
*Open your browser and navigate to `http://127.0.0.1:8080/index.html` to view the application.*

---

## 📊 API Endpoints

The backend exposes three primary REST API endpoints:
* `GET /api/history/{country}` - Returns 20 quarters of historical GDP growth data.
* `GET /api/forecast/{country}` - Returns an 8-quarter forecast combining SARIMA, LightGBM, and Ensemble predictions with 95% Confidence Intervals.
* `GET /api/metrics/{country}` - Returns model validation metrics (RMSE, MAE) and the final ensemble weighting distribution.

*(Supported country parameters: `us`, `germany`, `japan`, `india`)*

---

## 👨‍💻 Author

**Built by Yash Bajpai**
* 💼 **LinkedIn:** [Yash Bajpai](https://linkedin.com/in/yash-bajpai-b5a86332a)
* 🐙 **GitHub:** [Yash1bajpai](https://github.com/Yash1bajpai)
* 📧 **Email:** bajpaiyash2003@gmail.com

---
*© 2026 EconEngine Intelligence. All rights reserved.*
