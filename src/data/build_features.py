"""
build_features.py
-----------------
Builds model-ready feature tables for all four countries plus the global
panel, from the processed master CSVs.

Feature recipe (identical per country):
  - gdp_growth lags 1-4
  - lag 1-2 for every "signal" column (growth / rate / survey columns).
    Level columns (gdp_level, cpi_level, m2_level, indpro_level) are
    excluded because their QoQ growth variants are already present.
  - rolling mean/std of gdp_growth over 2 and 4 quarters, and a rolling
    4-quarter YoY sum -- ALL shifted by one quarter so no target
    information leaks into the features.
  - quarter-over-quarter diff for rate columns (unrate, interest rate,
    policy/leading indices, oil, sentiment) where present.

Per-country signal columns follow the spec below. The US deliberately
excludes the World Bank annual indicators (forward-filled to quarterly):
its FRED monthly block already covers the same signal at higher frequency.
Outputs:
  data/features/<country>_features.csv
  data/features/global_features.csv

Run from project root:
    python src/data/build_features.py
"""

import os
import sys
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
FEATURES_DIR  = os.path.join(PROJECT_ROOT, "data", "features")

COUNTRIES = ["us", "india", "japan", "germany"]
COUNTRY_ID_MAP = {c: i for i, c in enumerate(COUNTRIES)}

GDP_LAGS = [f"gdp_growth_lag{i}" for i in range(1, 5)]

# Signal columns that receive lag1/lag2, in exact output column order.
OTHER_VARS = {
    "us": [
        "cpi_growth", "indpro_growth", "m2_growth",
        "unrate", "fed_funds_rate",
    ],
    "india": [
        "cpi_growth",
        "wb_gdp_growth_pct", "wb_cpi_inflation_pct",
        "wb_unemployment_pct", "wb_trade_bal_gdp_pct", "wb_gross_savings_pct",
    ],
    "japan": [
        "cpi_growth", "indpro_growth", "unrate", "interest_rate",
        "oecd_leading_index",
        "wb_gdp_growth_pct", "wb_cpi_inflation_pct",
        "wb_unemployment_pct", "wb_trade_bal_gdp_pct", "wb_gross_savings_pct",
    ],
    "germany": [
        "cpi_growth", "indpro_growth", "unrate", "interest_rate",
        "oecd_leading_index",
        "wb_gdp_growth_pct", "wb_cpi_inflation_pct",
        "wb_unemployment_pct", "wb_trade_bal_gdp_pct", "wb_gross_savings_pct",
        "brent_crude", "sentiment",
    ],
}

# Columns that also receive a QoQ diff (current minus previous quarter).
DIFF_VARS = [
    "unrate", "fed_funds_rate", "interest_rate",
    "oecd_leading_index", "brent_crude", "sentiment",
]

# Column families dropped entirely from a country's feature table.
# The US omits the World Bank annual block (see docstring).
EXCLUDE_PREFIXES = {
    "us": ["wb_"],
}


def add_lags(df: pd.DataFrame, other_vars: list) -> pd.DataFrame:
    # Target lags
    for i in range(1, 5):
        df[f"gdp_growth_lag{i}"] = df["gdp_growth"].shift(i)

    # Signal lags (only for columns that exist in this country's master)
    for var in other_vars:
        if var in df.columns:
            for i in range(1, 3):
                df[f"{var}_lag{i}"] = df[var].shift(i)

    # Rolling stats -- shifted by 1 quarter to prevent data leakage
    df["gdp_growth_roll2_mean"] = df["gdp_growth"].shift(1).rolling(2).mean()
    df["gdp_growth_roll2_std"]  = df["gdp_growth"].shift(1).rolling(2).std()
    df["gdp_growth_roll4_mean"] = df["gdp_growth"].shift(1).rolling(4).mean()
    df["gdp_growth_roll4_std"]  = df["gdp_growth"].shift(1).rolling(4).std()

    # YoY approx (sum of the 4 quarters ENDING at t-1 -- shift(1) guards
    # against leaking the current quarter's target into the feature)
    df["gdp_growth_yoy"] = df["gdp_growth"].shift(1).rolling(4).sum()

    # QoQ diffs for rate-style columns
    for var in DIFF_VARS:
        if var in df.columns:
            df[f"{var}_diff"] = df[var] - df[var].shift(1)

    return df


def build_country_features(country: str) -> pd.DataFrame:
    master_path = os.path.join(PROCESSED_DIR, f"{country}_master.csv")
    df = pd.read_csv(master_path, index_col=0, parse_dates=True)

    for prefix in EXCLUDE_PREFIXES.get(country, []):
        df = df.drop(columns=[c for c in df.columns if c.startswith(prefix)])

    df = add_lags(df, OTHER_VARS[country])

    out_path = os.path.join(FEATURES_DIR, f"{country}_features.csv")
    df.to_csv(out_path)
    print(f"  Saved {os.path.relpath(out_path, PROJECT_ROOT)}  |  "
          f"{len(df)} rows  |  {len(df.columns)} columns")
    return df


def build_global_features(frames: dict) -> pd.DataFrame:
    parts = []
    for country, df in frames.items():
        g = df.copy()
        g["country"]    = country
        g["country_id"] = COUNTRY_ID_MAP[country]
        parts.append(g)

    global_df = pd.concat(parts, axis=0).sort_index()
    out_path = os.path.join(FEATURES_DIR, "global_features.csv")
    global_df.to_csv(out_path)
    print(f"  Saved {os.path.relpath(out_path, PROJECT_ROOT)}  |  "
          f"{len(global_df)} rows  |  {len(global_df.columns)} columns")


def run():
    os.makedirs(FEATURES_DIR, exist_ok=True)
    print("Building country features...")
    frames = {}
    for country in COUNTRIES:
        frames[country] = build_country_features(country)
    print("Building global panel...")
    build_global_features(frames)
    print("Done.")


if __name__ == "__main__":
    run()
