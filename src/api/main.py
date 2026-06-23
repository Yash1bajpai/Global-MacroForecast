import os
import sys
import joblib
import pandas as pd
from contextlib import asynccontextmanager
from typing import Dict, List, Optional
from enum import Enum
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from config.settings import FRED_API_KEY
from src.models.forecast_future import (
    sarima_forecast,
    lgbm_forecast_recursive,
    load_series,
    load_features,
    load_ensemble_weights
)

MODEL_CACHE: Dict[str, object] = {}
DATA_CACHE: Dict[str, object] = {}


class CountryCode(str, Enum):
    us = "us"
    india = "india"
    japan = "japan"
    germany = "germany"


class ForecastPoint(BaseModel):
    date: str
    quarter: str
    ensemble_pred: float
    lgbm_pred: float
    sarima_pred: Optional[float] = None
    ci_low: Optional[float] = None
    ci_high: Optional[float] = None


class MetricsResponse(BaseModel):
    ensemble_rmse: float
    ensemble_mae: float
    w_sarima: float
    w_lgbm: float


class HealthResponse(BaseModel):
    status: str
    message: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Loading models and data into memory...")

    if not FRED_API_KEY:
        print("WARNING: FRED_API_KEY is not set. Data fetching will fail.")

    countries = [c.value for c in CountryCode]
    for country in countries:
        lgbm_path = os.path.join(PROJECT_ROOT, "models_saved", f"{country}_lgbm.pkl")
        if os.path.exists(lgbm_path):
            MODEL_CACHE[f"{country}_lgbm"] = joblib.load(lgbm_path)

        sarima_path = os.path.join(PROJECT_ROOT, "models_saved", f"{country}_sarima.pkl")
        if os.path.exists(sarima_path):
            MODEL_CACHE[f"{country}_sarima"] = joblib.load(sarima_path)

        DATA_CACHE[f"{country}_series"] = load_series(country)
        X, y = load_features(country)
        DATA_CACHE[f"{country}_X"] = X
        DATA_CACHE[f"{country}_y"] = y

    DATA_CACHE["weights"] = load_ensemble_weights()

    summary_path = os.path.join(PROJECT_ROOT, "data", "processed", "model_summary.csv")
    if os.path.exists(summary_path):
        df = pd.read_csv(summary_path)
        metrics_dict: Dict[str, Dict[str, float]] = {}
        for _, row in df.iterrows():
            c = row["country"].lower()
            metrics_dict[c] = {
                "ensemble_rmse": float(row["ensemble_rmse"]),
                "ensemble_mae": float(row["ensemble_mae"]),
                "w_sarima": float(row["w_sarima"]),
                "w_lgbm": float(row["w_lgbm"])
            }
        DATA_CACHE["metrics"] = metrics_dict

    print("Startup complete. All models and data cached.")
    yield
    MODEL_CACHE.clear()
    DATA_CACHE.clear()


app = FastAPI(
    title="GDP Nowcasting API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

origins_env = os.getenv("ALLOWED_ORIGINS", "")
if origins_env:
    allowed_origins = [o.strip() for o in origins_env.split(",") if o.strip()]
else:
    allowed_origins = ["http://localhost:8080", "http://127.0.0.1:8080"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse)
def health_check() -> Dict[str, str]:
    return {"status": "online", "message": "GDP Nowcasting API is running."}


@app.get("/api/history/{country}")
def get_history(country: CountryCode) -> Dict[str, float]:
    c = country.value
    if f"{c}_series" not in DATA_CACHE:
        raise HTTPException(status_code=404, detail="Country not found")

    series = DATA_CACHE[f"{c}_series"]
    recent = series.tail(20)
    return {date.strftime("%Y-%m-%d"): float(val) for date, val in recent.items()}


@app.get("/api/metrics/{country}", response_model=MetricsResponse)
def get_metrics(country: CountryCode) -> Dict[str, float]:
    c = country.value
    metrics = DATA_CACHE.get("metrics", {})
    if c not in metrics:
        raise HTTPException(status_code=404, detail="Metrics not found")
    return metrics[c]


@app.get("/api/forecast/{country}", response_model=List[ForecastPoint])
def get_forecast(country: CountryCode) -> List[Dict[str, Optional[float]]]:
    c = country.value
    if f"{c}_lgbm" not in MODEL_CACHE:
        raise HTTPException(status_code=404, detail="Model not found")

    weights = DATA_CACHE["weights"].get(c, {"sarima": 0.0, "lgbm": 1.0})

    lgbm_model = MODEL_CACHE[f"{c}_lgbm"]
    X = DATA_CACHE[f"{c}_X"]
    y = DATA_CACHE[f"{c}_y"]
    lgbm_fc = lgbm_forecast_recursive(c, 8, fitted=lgbm_model, X=X, y=y)

    sarima_fc = None
    conf_int = None
    if f"{c}_sarima" in MODEL_CACHE:
        sarima_model = MODEL_CACHE[f"{c}_sarima"]
        series = DATA_CACHE[f"{c}_series"]
        sarima_fc, conf_int = sarima_forecast(c, series, 8, fitted_orig=sarima_model)

    if sarima_fc is not None:
        ensemble = weights["sarima"] * sarima_fc + weights["lgbm"] * lgbm_fc
    else:
        ensemble = lgbm_fc

    response: List[Dict[str, Optional[float]]] = []
    for date, ens_val in ensemble.items():
        point: Dict[str, Optional[float]] = {
            "date": date.strftime("%Y-%m-%d"),
            "quarter": f"Q{date.quarter}-{date.year}",
            "ensemble_pred": float(ens_val),
            "lgbm_pred": float(lgbm_fc[date])
        }
        if sarima_fc is not None:
            point["sarima_pred"] = float(sarima_fc[date])
            if conf_int is not None:
                point["ci_low"] = float(conf_int.loc[date, "lower_95"])
                point["ci_high"] = float(conf_int.loc[date, "upper_95"])
        response.append(point)

    return response


# --- Serve Static Frontend ---
app.mount("/css", StaticFiles(directory=os.path.join(PROJECT_ROOT, "frontend", "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(PROJECT_ROOT, "frontend", "js")), name="js")

@app.get("/")
def serve_index():
    index_path = os.path.join(PROJECT_ROOT, "frontend", "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="Frontend index.html not found.")
    return FileResponse(index_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="127.0.0.1", port=8000, reload=True)
