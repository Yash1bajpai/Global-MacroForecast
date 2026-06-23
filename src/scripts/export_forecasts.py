import os
import sys
import json
import joblib
import pandas as pd
from typing import Dict, Any

# Ensure project root is in path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from src.models.forecast_future import (
    sarima_forecast,
    lgbm_forecast_recursive,
    load_series,
    load_features,
    load_ensemble_weights
)

def export_all_forecasts():
    print("Starting generation of static forecasts...")
    
    countries = ["us", "germany", "japan", "india"]
    weights_dict = load_ensemble_weights()
    
    # Load metrics
    metrics_dict = {}
    summary_path = os.path.join(PROJECT_ROOT, "data", "processed", "model_summary.csv")
    if os.path.exists(summary_path):
        df = pd.read_csv(summary_path)
        for _, row in df.iterrows():
            c = row["country"].lower()
            metrics_dict[c] = {
                "ensemble_rmse": float(row["ensemble_rmse"]),
                "ensemble_mae": float(row["ensemble_mae"]),
                "w_sarima": float(row["w_sarima"]),
                "w_lgbm": float(row["w_lgbm"])
            }
    
    final_data: Dict[str, Any] = {}
    
    for country in countries:
        print(f"Processing {country}...")
        country_data: Dict[str, Any] = {}
        
        # 1. History
        try:
            series = load_series(country)
            recent = series.tail(20)
            country_data["history"] = {date.strftime("%Y-%m-%d"): float(val) for date, val in recent.items()}
        except Exception as e:
            print(f"  Warning: Failed to load history for {country}: {e}")
            country_data["history"] = {}
            
        # 2. Metrics
        country_data["metrics"] = metrics_dict.get(country, {
            "ensemble_rmse": 0.0, "ensemble_mae": 0.0, "w_sarima": 0.0, "w_lgbm": 1.0
        })
        
        # 3. Forecast
        try:
            weights = weights_dict.get(country, {"sarima": 0.0, "lgbm": 1.0})
            
            # LGBM
            lgbm_path = os.path.join(PROJECT_ROOT, "models_saved", f"{country}_lgbm.pkl")
            lgbm_model = joblib.load(lgbm_path)
            X, y = load_features(country)
            lgbm_fc = lgbm_forecast_recursive(country, 8, fitted=lgbm_model, X=X, y=y)
            
            # SARIMA
            sarima_fc = None
            conf_int = None
            sarima_path = os.path.join(PROJECT_ROOT, "models_saved", f"{country}_sarima.pkl")
            if os.path.exists(sarima_path):
                sarima_model = joblib.load(sarima_path)
                sarima_fc, conf_int = sarima_forecast(country, series, 8, fitted_orig=sarima_model)
            
            if sarima_fc is not None:
                ensemble = weights["sarima"] * sarima_fc + weights["lgbm"] * lgbm_fc
            else:
                ensemble = lgbm_fc
                
            forecast_list = []
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
                        point["ci_low"] = float(conf_int.loc[date, "lower_95"])
                        point["ci_high"] = float(conf_int.loc[date, "upper_95"])
                forecast_list.append(point)
                
            country_data["forecast"] = forecast_list
        except Exception as e:
            print(f"  Warning: Failed to generate forecast for {country}: {e}")
            country_data["forecast"] = []
            
        final_data[country] = country_data
        
    # Save to frontend/data/forecasts.json
    out_dir = os.path.join(PROJECT_ROOT, "frontend", "data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "forecasts.json")
    
    with open(out_path, "w") as f:
        json.dump(final_data, f, indent=4)
        
    print(f"\nSuccess! Exported completely static forecasts to: {out_path}")
    print("You can now push this file to GitHub to update your Vercel deployment.")

if __name__ == "__main__":
    export_all_forecasts()
