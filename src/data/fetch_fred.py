"""
fetch_fred.py
-------------
Fetches FRED data for US, Japan, Germany, and India.
Saves each series as data/raw/<country>/<indicator>.csv
"""

import os
import sys
import logging
import pandas as pd
from fredapi import Fred
from datetime import datetime

from tenacity import retry, stop_after_attempt, wait_exponential

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from config.settings import (
    FRED_API_KEY, START_DATE, END_DATE, LOGS_DIR,
    FRED_SERIES_US, FRED_SERIES_JAPAN, FRED_SERIES_GERMANY, FRED_SERIES_INDIA,
    COUNTRY_RAW_DIRS,
)

# -- Logging
os.makedirs(LOGS_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, "fetch_fred.log"), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _fetch_single_series(fred: Fred, series_id: str):
    return fred.get_series(
        series_id,
        observation_start=START_DATE,
        observation_end=END_DATE,
    )


def fetch_country(fred: Fred, country: str, series_dict: dict) -> int:
    """Fetch all series for one country. Returns count of successful fetches."""
    out_dir = COUNTRY_RAW_DIRS[country]
    os.makedirs(out_dir, exist_ok=True)
    success = 0

    for name, series_id in series_dict.items():
        try:
            raw = _fetch_single_series(fred, series_id)
            df = raw.reset_index()
            df.columns = ["date", "value"]
            df["date"]  = pd.to_datetime(df["date"])
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            df.dropna(subset=["value"], inplace=True)

            out_path = os.path.join(out_dir, f"{name}.csv")
            df.to_csv(out_path, index=False)
            logger.info(
                "  [OK]  %s/%-14s (%s)  %d rows  %s -> %s",
                country, name, series_id, len(df),
                df["date"].min().date(), df["date"].max().date(),
            )
            success += 1
        except Exception as exc:
            logger.warning("  [SKIP] %s/%s (%s): %s", country, name, series_id, exc)

    return success


if __name__ == "__main__":
    if not FRED_API_KEY:
        logger.error("FRED_API_KEY missing from .env")
        sys.exit(1)

    fred = Fred(api_key=FRED_API_KEY)

    logger.info("=" * 55)
    logger.info("FRED Data Fetch  |  %s", datetime.now().strftime("%Y-%m-%d %H:%M"))
    logger.info("=" * 55)

    country_map = {
        "us":      FRED_SERIES_US,
        "japan":   FRED_SERIES_JAPAN,
        "germany": FRED_SERIES_GERMANY,
        "india":   FRED_SERIES_INDIA,
    }

    total = 0
    for country, series in country_map.items():
        logger.info("\n--- %s ---", country.upper())
        total += fetch_country(fred, country, series)

    logger.info("\nDone. %d series saved.", total)
