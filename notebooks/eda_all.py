"""
eda_all.py
Runs ADF stationarity tests + summary stats for all 4 countries.
Saves results to data/processed/eda_adf_results.csv
        and     data/processed/eda_summary_stats.csv

Run: python notebooks/eda_all.py
"""

import os
import sys
import warnings
import pandas as pd
import numpy as np

warnings.filterwarnings("ignore")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from statsmodels.tsa.stattools import adfuller
from config.settings import DATA_PROCESSED_DIR

COUNTRIES = ["us", "india", "japan", "germany"]

# Columns to run ADF on (level series only -- growth rates expected I(0))
ADF_COLS_LEVELS = [
    "gdp_level", "cpi_level", "indpro_level", "m2_level",
    "unrate", "interest_rate", "fed_funds_rate",
    "oecd_leading_index",
]

ADF_COLS_GROWTH = [
    "gdp_growth", "cpi_growth", "indpro_growth", "m2_growth",
]


def run_adf(series: pd.Series) -> dict:
    s = series.dropna()
    if len(s) < 10:
        return {"adf_stat": None, "p_value": None, "result": "insufficient data"}
    stat, p, _, _, crit, _ = adfuller(s, autolag="AIC")
    result = "stationary (I(0))" if p < 0.05 else "non-stationary (I(1))"
    return {
        "adf_stat":   round(stat, 4),
        "p_value":    round(p, 4),
        "crit_1pct":  round(crit["1%"], 4),
        "crit_5pct":  round(crit["5%"], 4),
        "result":     result,
        "n_obs":      len(s),
    }


def main():
    adf_records   = []
    summary_parts = {}

    for country in COUNTRIES:
        path = os.path.join(DATA_PROCESSED_DIR, f"{country}_master.csv")
        if not os.path.exists(path):
            print(f"[SKIP] {country}_master.csv not found")
            continue

        df = pd.read_csv(path, index_col=0, parse_dates=True)
        summary_parts[country] = df.describe().round(4)

        target_cols = ADF_COLS_LEVELS + ADF_COLS_GROWTH
        for col in target_cols:
            if col not in df.columns:
                continue
            res = run_adf(df[col])
            res["country"] = country
            res["series"]  = col
            res["series_type"] = "level" if col in ADF_COLS_LEVELS else "growth/diff"
            adf_records.append(res)

    # Save ADF results
    adf_df = pd.DataFrame(adf_records)[
        ["country", "series", "series_type", "n_obs",
         "adf_stat", "p_value", "crit_5pct", "result"]
    ]
    adf_path = os.path.join(DATA_PROCESSED_DIR, "eda_adf_results.csv")
    adf_df.to_csv(adf_path, index=False)
    print("\nADF Results:")
    print(adf_df.to_string(index=False))
    print(f"\nSaved: {adf_path}")

    # Save summary stats
    all_summary = pd.concat(summary_parts, axis=1)
    summary_path = os.path.join(DATA_PROCESSED_DIR, "eda_summary_stats.csv")
    all_summary.to_csv(summary_path)
    print(f"Saved: {summary_path}")

    # Print correlations with gdp_growth per country
    print("\n--- Correlation with gdp_growth ---")
    for country in COUNTRIES:
        path = os.path.join(DATA_PROCESSED_DIR, f"{country}_master.csv")
        if not os.path.exists(path):
            continue
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        if "gdp_growth" not in df.columns:
            continue
        corr = df.corr(numeric_only=True)["gdp_growth"].drop("gdp_growth").sort_values(key=abs, ascending=False)
        print(f"\n{country.upper()} -- Top correlates with gdp_growth:")
        print(corr.head(8).round(3).to_string())


if __name__ == "__main__":
    main()
