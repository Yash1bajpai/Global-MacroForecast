"""
fetch_worldbank.py
------------------
Fetches annual macro indicators from the World Bank API (wbdata)
for US, India, Japan, Germany.
Saves per-country CSVs to data/raw/<country>/wb_<indicator>.csv

Install: pip install wbdata
"""

import os
import sys
import logging
import datetime
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from config.settings import (
    LOGS_DIR, START_DATE, WB_INDICATORS, WB_COUNTRY_CODES, COUNTRY_RAW_DIRS,
)

os.makedirs(LOGS_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, "fetch_worldbank.log"), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def fetch_worldbank() -> None:
    try:
        import wbdata
    except ImportError:
        logger.error("wbdata not installed. Run: pip install wbdata")
        sys.exit(1)

    start_dt = datetime.datetime.strptime(START_DATE, "%Y-%m-%d")
    end_dt   = datetime.datetime.now()
    date_range = (start_dt, end_dt)

    iso2_list = list(WB_COUNTRY_CODES.values())   # ["US","IN","JP","DE"]

    for ind_name, ind_code in WB_INDICATORS.items():
        logger.info("Fetching WB: %s (%s) ...", ind_name, ind_code)
        try:
            df = wbdata.get_dataframe(
                {ind_code: ind_name},
                country=iso2_list,
                date=date_range,
                parse_dates=True,
            )
            df = df.reset_index()

            # Normalise column names to lowercase
            df.columns = [c.lower() for c in df.columns]

            # Identify the country and date columns
            # wbdata may name them 'country' and 'date'
            country_col = [c for c in df.columns if "country" in c][0]
            date_col    = [c for c in df.columns if "date" in c][0]

            # Save per country
            name_map = {
                "US": "United States",
                "IN": "India",
                "JP": "Japan",
                "DE": "Germany",
            }
            for country_key, iso2 in WB_COUNTRY_CODES.items():
                country_name = name_map.get(iso2, iso2)
                mask = df[country_col].str.contains(country_name, case=False, na=False)
                sub  = df[mask][[date_col, ind_name]].copy()
                sub.columns = ["date", "value"]
                sub = sub.dropna(subset=["value"]).sort_values("date")

                if sub.empty:
                    logger.warning("  No data for %s / %s", country_key, ind_name)
                    continue

                out_dir = COUNTRY_RAW_DIRS[country_key]
                os.makedirs(out_dir, exist_ok=True)
                out_path = os.path.join(out_dir, f"wb_{ind_name}.csv")
                sub.to_csv(out_path, index=False)
                logger.info(
                    "  [OK]  %s/wb_%-22s  %d rows  %s -> %s",
                    country_key, ind_name, len(sub),
                    sub["date"].min(), sub["date"].max(),
                )

        except Exception as exc:
            logger.warning("  [SKIP] %s: %s", ind_name, exc)


if __name__ == "__main__":
    logger.info("=" * 55)
    logger.info("World Bank Data Fetch  |  %s", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    logger.info("=" * 55)
    fetch_worldbank()
    logger.info("World Bank fetch complete.")
