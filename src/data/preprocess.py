"""
preprocess.py
Builds one master quarterly DataFrame per country from raw CSVs.
Saves to data/processed/<country>_master.csv and global_master.csv
"""

import os
import sys
import logging
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from config.settings import DATA_RAW_DIR, DATA_PROCESSED_DIR, COUNTRY_RAW_DIRS, LOGS_DIR

os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, "preprocess.log"), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# NBER + major recession quarters (QS dates)
RECESSION_QTRS = {
    "us": [
        "2001-01-01", "2001-04-01", "2001-07-01", "2001-10-01",
        "2007-10-01", "2008-01-01", "2008-04-01", "2008-07-01",
        "2008-10-01", "2009-01-01", "2009-04-01",
        "2020-01-01", "2020-04-01",
    ],
    "india":   ["2020-04-01"],
    "japan":   [
        "2001-01-01", "2001-04-01",
        "2008-07-01", "2008-10-01", "2009-01-01", "2009-04-01",
        "2011-01-01",
        "2020-01-01", "2020-04-01",
    ],
    "germany": [
        "2008-07-01", "2008-10-01", "2009-01-01", "2009-04-01",
        "2020-01-01", "2020-04-01",
    ],
}


def load_csv(path):
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path, parse_dates=["date"])
    s = df.set_index("date")["value"]
    s.index = pd.to_datetime(s.index)
    return s


def to_quarterly(series, method="mean"):
    if method == "mean":
        return series.resample("QS").mean()
    return series.resample("QS").last()


def annual_to_quarterly(series):
    end = series.index.max() + pd.offsets.MonthEnd(12)
    q_idx = pd.date_range(series.index.min(), end, freq="QS")
    return series.reindex(series.index.union(q_idx)).sort_index().ffill().reindex(q_idx)


def log_diff_pct(series):
    return (np.log(series) - np.log(series.shift(1))) * 100


def build_country_master(country):
    raw_dir = COUNTRY_RAW_DIRS[country]
    frames = {}

    # GDP: quarterly level + QoQ log-diff growth
    gdp = load_csv(os.path.join(raw_dir, "gdp.csv"))
    if gdp is not None:
        gdp_q = to_quarterly(gdp, "last")
        # Detect if series is already a growth rate (contains negative values)
        # e.g. NAEXKP01JPQ657S for Japan is QoQ % change, not a level
        is_growth_rate = (gdp_q < 0).any()
        if is_growth_rate:
            frames["gdp_growth"] = gdp_q
        else:
            frames["gdp_level"]  = gdp_q
            frames["gdp_growth"] = log_diff_pct(gdp_q)
    else:
        # India: no quarterly GDP on FRED, use WB annual growth rate
        wb_gdp = load_csv(os.path.join(raw_dir, "wb_gdp_growth_pct.csv"))
        if wb_gdp is not None:
            frames["gdp_growth"] = annual_to_quarterly(wb_gdp)

    # Monthly FRED series -> quarterly mean
    monthly_cols = {
        "cpi":           "cpi_level",
        "m2":            "m2_level",
        "fed_funds":     "fed_funds_rate",
        "unrate":        "unrate",
        "indpro":        "indpro_level",
        "interest_rate": "interest_rate",
        "brent_crude":   "brent_crude",
        "sentiment":     "sentiment",
    }
    for fname, col in monthly_cols.items():
        s = load_csv(os.path.join(raw_dir, f"{fname}.csv"))
        if s is not None:
            frames[col] = to_quarterly(s)

    # QoQ log-diff for price/production level series
    for src, dst in [
        ("cpi_level",   "cpi_growth"),
        ("indpro_level","indpro_growth"),
        ("m2_level",    "m2_growth"),
    ]:
        if src in frames:
            frames[dst] = log_diff_pct(frames[src])

    # World Bank annual -> quarterly forward-fill
    wb_cols = [
        "wb_gdp_growth_pct", "wb_cpi_inflation_pct", "wb_unemployment_pct",
        "wb_trade_bal_gdp_pct", "wb_gross_savings_pct",
    ]
    for wb in wb_cols:
        s = load_csv(os.path.join(raw_dir, f"{wb}.csv"))
        if s is not None:
            frames[wb] = annual_to_quarterly(s)

    # OECD leading index: multiple sub-series stored per date -> group mean -> quarterly
    oecd_path = os.path.join(raw_dir, "oecd_leading_index.csv")
    if os.path.exists(oecd_path):
        oecd_df = pd.read_csv(oecd_path, parse_dates=["date"])
        oecd_monthly = oecd_df.groupby("date")["value"].mean()
        oecd_monthly.index = pd.to_datetime(oecd_monthly.index)
        frames["oecd_leading_index"] = to_quarterly(oecd_monthly)

    # Build master DataFrame on quarterly index
    idx = pd.date_range("2000-01-01", "2026-07-01", freq="QS")
    master = pd.DataFrame(index=idx)
    for name, s in frames.items():
        master[name] = s

    # Recession dummy
    master["recession"] = 0
    for d in RECESSION_QTRS.get(country, []):
        ts = pd.Timestamp(d)
        if ts in master.index:
            master.loc[ts, "recession"] = 1

    # COVID shock dummy
    master["covid_shock"] = 0
    covid_ts = pd.Timestamp("2020-04-01")
    if covid_ts in master.index:
        master.loc[covid_ts, "covid_shock"] = 1

    # Calendar quarter (1-4) as a feature
    master["quarter"] = master.index.quarter

    # Keep only rows where GDP growth is available
    master = master.loc[master["gdp_growth"].notna()].copy()

    return master


def run():
    countries = ["us", "india", "japan", "germany"]
    country_id_map = {c: i for i, c in enumerate(countries)}
    all_masters = []

    for country in countries:
        logger.info("Processing: %s", country.upper())
        master = build_country_master(country)
        out_path = os.path.join(DATA_PROCESSED_DIR, f"{country}_master.csv")
        master.to_csv(out_path)
        logger.info(
            "  Saved %s_master.csv  |  %d rows  |  %d columns  |  %s -> %s",
            country, len(master), len(master.columns),
            master.index.min().date(), master.index.max().date(),
        )

        master_copy = master.copy()
        master_copy["country"]    = country
        master_copy["country_id"] = country_id_map[country]
        all_masters.append(master_copy)

    global_master = pd.concat(all_masters, axis=0).sort_index()
    global_path = os.path.join(DATA_PROCESSED_DIR, "global_master.csv")
    global_master.to_csv(global_path)
    logger.info(
        "Saved global_master.csv  |  %d rows  |  %d columns",
        len(global_master), len(global_master.columns),
    )


if __name__ == "__main__":
    run()
