"""
fetch_oecd.py
-------------
Fetches quarterly GDP and leading indicators from OECD SDMX-JSON API
for Japan and Germany (no API key required).
Saves to data/raw/<country>/oecd_<indicator>.csv

No extra install needed beyond requests.
"""

import os
import sys
import logging
import datetime
import requests
import pandas as pd

from tenacity import retry, stop_after_attempt, wait_exponential

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from config.settings import LOGS_DIR, COUNTRY_RAW_DIRS, OECD_BASE_URL, OECD_COUNTRIES

os.makedirs(LOGS_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, "fetch_oecd.log"), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# OECD QNA dataset: quarterly GDP at market prices, volume, SA
# Filter: {country}.B1_GE.VPVOBARSA.Q
# Docs: https://stats.oecd.org/sdmx-json/data/QNA/...

OECD_DATASETS = {
    "gdp_qna": {
        "dataset": "QNA",
        "measure": "B1_GE",
        "subject": "VPVOBARSA",   # volume, SA
        "frequency": "Q",
        "filename": "oecd_gdp_quarterly",
    },
    "leading_index": {
        "dataset": "MEI_CLI",
        "measure": "LOLITOAASTSAM",
        "subject": None,
        "frequency": "M",
        "filename": "oecd_leading_index",
    },
}


def build_url(dataset: str, country_code: str, measure: str, subject: str, freq: str) -> str:
    """Build OECD SDMX-JSON data URL."""
    if subject:
        filter_str = f"{country_code}.{measure}.{subject}.{freq}"
    else:
        filter_str = f"{country_code}.{measure}.{freq}"
    start = "2000-Q1" if freq == "Q" else "2000-01"
    return (
        f"{OECD_BASE_URL}/{dataset}/{filter_str}/all"
        f"?startTime={start}&dimensionAtObservation=allDimensions"
    )


def parse_oecd_json(resp_json: dict, freq: str = "Q") -> pd.DataFrame:
    """Parse OECD SDMX-JSON response (2024+ format) into a tidy date/value DataFrame."""
    try:
        data_node  = resp_json.get("data", resp_json)
        ds         = data_node["dataSets"][0]
        st         = data_node["structures"][0]
        obs_dims   = st["dimensions"]["observation"]
        time_dim   = next(d for d in obs_dims if d["id"] == "TIME_PERIOD")
        time_vals  = [v["id"] for v in time_dim["values"]]

        records = []
        for series_val in ds["series"].values():
            for time_idx_str, obs_vals in series_val.get("observations", {}).items():
                value = obs_vals[0]
                if value is not None:
                    records.append({
                        "date":  time_vals[int(time_idx_str)],
                        "value": float(value),
                    })

        df = pd.DataFrame(records).sort_values("date").reset_index(drop=True)
        if freq == "Q":
            df["date"] = pd.PeriodIndex(df["date"], freq="Q").to_timestamp()
        else:
            df["date"] = pd.to_datetime(df["date"])
        return df
    except Exception as exc:
        raise RuntimeError(f"Failed to parse OECD JSON: {exc}") from exc


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _get_oecd(url: str) -> requests.Response:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp


def fetch_oecd() -> None:
    for country_key, oecd_code in OECD_COUNTRIES.items():
        out_dir = COUNTRY_RAW_DIRS[country_key]
        os.makedirs(out_dir, exist_ok=True)

        for ds_name, ds_cfg in OECD_DATASETS.items():
            try:
                url = build_url(
                    ds_cfg["dataset"], oecd_code,
                    ds_cfg["measure"], ds_cfg["subject"],
                    ds_cfg["frequency"],
                )
                logger.info("Fetching OECD %s / %s ...", country_key, ds_name)
                logger.info("  URL: %s", url)

                resp = _get_oecd(url)

                df = parse_oecd_json(resp.json(), freq=ds_cfg["frequency"])
                if df.empty:
                    logger.warning("  [EMPTY] %s / %s", country_key, ds_name)
                    continue

                out_path = os.path.join(out_dir, f"{ds_cfg['filename']}.csv")
                df.to_csv(out_path, index=False)
                logger.info(
                    "  [OK]  %s/%-28s  %d rows  %s -> %s",
                    country_key, ds_cfg["filename"], len(df),
                    df["date"].min().date(), df["date"].max().date(),
                )

            except Exception as exc:
                logger.warning("  [SKIP] %s / %s: %s", country_key, ds_name, exc)


if __name__ == "__main__":
    logger.info("=" * 55)
    logger.info("OECD Data Fetch  |  %s", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    logger.info("=" * 55)
    fetch_oecd()
    logger.info("OECD fetch complete.")
