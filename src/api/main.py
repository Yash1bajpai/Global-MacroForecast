import os
import sys
import joblib
import pandas as pd
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Adjust path so we can import src.models
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from src.models.forecast_future import (
    sarima_forecast,
    lgbm_forecast_recursive,
    load_series,
    load_features,
    load_ensemble_weights
)

MODEL_CACHE = {}
DATA_CACHE = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Loading models and data into memory...")
    # Load Models and Data
    countries = ["us", "india", "japan", "germany"]
    for country in countries:
        # LGBM
        lgbm_path = os.path.join(PROJECT_ROOT, "models_saved", f"{country}_lgbm.pkl")
        if os.path.exists(lgbm_path):
            MODEL_CACHE[f"{country}_lgbm"] = joblib.load(lgbm_path)
        
        # SARIMA (India might not have it)
        sarima_path = os.path.join(PROJECT_ROOT, "models_saved", f"{country}_sarima.pkl")
        if os.path.exists(sarima_path):
            MODEL_CACHE[f"{country}_sarima"] = joblib.load(sarima_path)
            
        # Load Data
        DATA_CACHE[f"{country}_series"] = load_series(country)
        X, y = load_features(country)
        DATA_CACHE[f"{country}_X"] = X
        DATA_CACHE[f"{country}_y"] = y
        
    # Load Weights
    DATA_CACHE["weights"] = load_ensemble_weights()
    
    # Load Metrics (from model_summary.csv)
    summary_path = os.path.join(PROJECT_ROOT, "data", "processed", "model_summary.csv")
    if os.path.exists(summary_path):
        df = pd.read_csv(summary_path)
        # Store as dict per country
        metrics_dict = {}
        for _, row in df.iterrows():
            c = row['country'].lower()
            metrics_dict[c] = {
                "ensemble_rmse": float(row["ensemble_rmse"]),
                "ensemble_mae": float(row["ensemble_mae"]),
                "w_sarima": float(row["w_sarima"]),
                "w_lgbm": float(row["w_lgbm"])
            }
        DATA_CACHE["metrics"] = metrics_dict
    
    print("Startup complete. All models and data cached.")
    yield
    # Cleanup
    MODEL_CACHE.clear()
    DATA_CACHE.clear()

app = FastAPI(title="GDP Nowcasting API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "online", "message": "GDP Nowcasting API is running."}

@app.get("/api/history/{country}")
def get_history(country: str):
    country = country.lower()
    if f"{country}_series" not in DATA_CACHE:
        raise HTTPException(status_code=404, detail="Country not found")
        
    series = DATA_CACHE[f"{country}_series"]
    # Return last 20 quarters (5 years)
    recent = series.tail(20)
    
    # Format for JSON: {"2021-01-01": 1.2, ...}
    return {date.strftime("%Y-%m-%d"): float(val) for date, val in recent.items()}

@app.get("/api/metrics/{country}")
def get_metrics(country: str):
    country = country.lower()
    metrics = DATA_CACHE.get("metrics", {})
    if country not in metrics:
        raise HTTPException(status_code=404, detail="Metrics not found")
    return metrics[country]

@app.get("/api/forecast/{country}")
def get_forecast(country: str):
    country = country.lower()
    if f"{country}_lgbm" not in MODEL_CACHE:
        raise HTTPException(status_code=404, detail="Model not found")
        
    weights = DATA_CACHE["weights"].get(country, {"sarima": 0.0, "lgbm": 1.0})
    
    # LGBM Forecast
    lgbm_model = MODEL_CACHE[f"{country}_lgbm"]
    X = DATA_CACHE[f"{country}_X"]
    y = DATA_CACHE[f"{country}_y"]
    lgbm_fc = lgbm_forecast_recursive(country, 8, fitted=lgbm_model, X=X, y=y)
    
    # SARIMA Forecast
    sarima_fc = None
    conf_int = None
    if f"{country}_sarima" in MODEL_CACHE:
        sarima_model = MODEL_CACHE[f"{country}_sarima"]
        series = DATA_CACHE[f"{country}_series"]
        sarima_fc, conf_int = sarima_forecast(country, series, 8, fitted_orig=sarima_model)
        
    # Ensemble
    if sarima_fc is not None:
        ensemble = weights["sarima"] * sarima_fc + weights["lgbm"] * lgbm_fc
    else:
        ensemble = lgbm_fc
        
    # Format response
    response = []
    for date, ens_val in ensemble.items():
        point = {
            "date": date.strftime("%Y-%m-%d"),
            "quarter": f"Q{date.quarter}-{date.year}",
            "ensemble_pred": float(ens_val),
            "lgbm_pred": float(lgbm_fc[date])
        }
        if sarima_fc is not None:
            point["sarima_pred"] = float(sarima_fc[date])
            if conf_int is not None:
                point["ci_low"] = float(conf_int.loc[date, 'lower_95'])
                point["ci_high"] = float(conf_int.loc[date, 'upper_95'])
        response.append(point)
        
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="127.0.0.1", port=8000, reload=True)
