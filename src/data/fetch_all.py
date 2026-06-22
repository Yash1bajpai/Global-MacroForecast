"""
fetch_all.py
------------
Master runner: fetches data from all sources for all 4 countries.
Run this once to populate data/raw/<country>/ folders.

Usage:
    python src/data/fetch_all.py
"""

import sys
import os
import logging
import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from config.settings import LOGS_DIR

os.makedirs(LOGS_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, "fetch_all.log"), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def run_step(label: str, func) -> bool:
    logger.info("\n%s", "=" * 55)
    logger.info("STEP: %s", label)
    logger.info("=" * 55)
    try:
        func()
        logger.info("[DONE] %s", label)
        return True
    except SystemExit as exc:
        logger.error("[FAILED] %s exited with code %s", label, exc.code)
        return False
    except Exception as exc:
        logger.error("[FAILED] %s: %s", label, exc)
        return False


if __name__ == "__main__":
    logger.info("GDP Nowcast -- Full Data Fetch  |  %s",
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))

    from src.data.fetch_worldbank  import fetch_worldbank
    from src.data.fetch_oecd       import fetch_oecd

    from fredapi import Fred
    from config.settings import (
        FRED_API_KEY,
        FRED_SERIES_US, FRED_SERIES_JAPAN, FRED_SERIES_GERMANY, FRED_SERIES_INDIA,
    )
    from src.data.fetch_fred import fetch_country

    fred = Fred(api_key=FRED_API_KEY)

    def run_fred():
        for country, series in [
            ("us",      FRED_SERIES_US),
            ("japan",   FRED_SERIES_JAPAN),
            ("germany", FRED_SERIES_GERMANY),
            ("india",   FRED_SERIES_INDIA),
        ]:
            logger.info("  -- FRED: %s", country.upper())
            fetch_country(fred, country, series)

    results = {
        "FRED (US + Japan + Germany + India)": run_step("FRED", run_fred),
        "World Bank (all 4 countries)":        run_step("World Bank", fetch_worldbank),
        "OECD (Japan + Germany quarterly)":    run_step("OECD", fetch_oecd),
    }

    logger.info("\n%s", "=" * 55)
    logger.info("SUMMARY")
    logger.info("=" * 55)
    for name, ok in results.items():
        status = "OK   " if ok else "FAIL "
        logger.info("  [%s] %s", status, name)

    logger.info("\nData saved to data/raw/<country>/")
    logger.info("Next step: run ADF tests in notebook, then preprocess.py")
