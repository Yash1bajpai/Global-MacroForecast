"""
features.py
Adds lag, rolling, and derived features to each country master DataFrame.
Saves to data/features/<country>_features.csv and global_features.csv
"""

import os
import sys
import logging
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from config.settings import DATA_PROCESSED_DIR, LOGS_DIR

FEATURES_DIR = os.path.join(os.path.dirname(DATA_PROCESSED_DIR), "processed", "..", "data", "features")
FEATURES_DIR = os.path.join(os.path.dirname(os.path.dirname(DATA_PROCESSED_DIR)), "data", "features")
os.makedirs(FEATURES_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, "features.log"), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

GDP_LAGS         = [1, 2, 3, 4]
PREDICTOR_LAGS   = [1, 2]
ROLLING_WINDOWS  = [2, 4]

PREDICTOR_COLS = [
    "cpi_growth", "indpro_growth", "m2_growth",
    "unrate", "interest_rate", "fed_funds_rate",
    "oecd_leading_index",
    "wb_gdp_growth_pct", "wb_cpi_inflation_pct", "wb_unemployment_pct",
    "wb_trade_bal_gdp_pct", "wb_gross_savings_pct",
    "brent_crude", "sentiment",
]


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    # Lag features for target (gdp_growth)
    for lag in GDP_LAGS:
        out[f"gdp_growth_lag{lag}"] = out["gdp_growth"].shift(lag)

    # Lag features for predictors (only those present in df)
    for col in PREDICTOR_COLS:
        if col in out.columns:
            for lag in PREDICTOR_LAGS:
                out[f"{col}_lag{lag}"] = out[col].shift(lag)

    # Rolling statistics on gdp_growth (computed on lagged values to avoid leakage)
    for w in ROLLING_WINDOWS:
        rolled = out["gdp_growth"].shift(1).rolling(w)
        out[f"gdp_growth_roll{w}_mean"] = rolled.mean()
        out[f"gdp_growth_roll{w}_std"]  = rolled.std()

    # YoY GDP growth proxy (sum of last 4 quarters)
    out["gdp_growth_yoy"] = (
        out["gdp_growth"].shift(1)
        + out["gdp_growth"].shift(2)
        + out["gdp_growth"].shift(3)
        + out["gdp_growth"].shift(4)
    )

    # First-difference of rates/levels (useful for non-stationary series)
    for col in ["unrate", "interest_rate", "fed_funds_rate", "oecd_leading_index", "brent_crude", "sentiment"]:
        if col in out.columns:
            out[f"{col}_diff"] = out[col].diff()

    # Drop rows where all GDP lags are NaN (not enough history)
    out = out.dropna(subset=[f"gdp_growth_lag{GDP_LAGS[-1]}"])

    return out


def run():
    countries = ["us", "india", "japan", "germany"]

    all_dfs = []

    for country in countries:
        master_path = os.path.join(DATA_PROCESSED_DIR, f"{country}_master.csv")
        if not os.path.exists(master_path):
            logger.warning("Master not found for %s, skipping", country)
            continue

        df = pd.read_csv(master_path, index_col=0, parse_dates=True)
        df_feat = add_features(df)

        out_path = os.path.join(FEATURES_DIR, f"{country}_features.csv")
        df_feat.to_csv(out_path)

        logger.info(
            "Saved %s_features.csv  |  %d rows  |  %d columns  |  %s -> %s",
            country, len(df_feat), len(df_feat.columns),
            df_feat.index.min().date(), df_feat.index.max().date(),
        )

        # For global dataset
        df_feat_copy = df_feat.copy()
        if "country" not in df_feat_copy.columns:
            df_feat_copy["country"]    = country
            df_feat_copy["country_id"] = countries.index(country)
        all_dfs.append(df_feat_copy)

    global_df = pd.concat(all_dfs, axis=0).sort_index()
    global_path = os.path.join(FEATURES_DIR, "global_features.csv")
    global_df.to_csv(global_path)

    logger.info(
        "Saved global_features.csv  |  %d rows  |  %d columns",
        len(global_df), len(global_df.columns),
    )


if __name__ == "__main__":
    run()
