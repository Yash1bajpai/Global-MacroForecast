import os
from dotenv import load_dotenv

load_dotenv()

# -- API Keys
FRED_API_KEY = os.getenv("FRED_API_KEY")

# -- Date Range
START_DATE = "2000-01-01"
END_DATE   = None  # None = fetch up to today

# -- Directory Paths
BASE_DIR           = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_RAW_DIR       = os.path.join(BASE_DIR, "data", "raw")
DATA_PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
DB_DIR             = os.path.join(BASE_DIR, "data", "db")
MODELS_DIR         = os.path.join(BASE_DIR, "models_saved")
LOGS_DIR           = os.path.join(BASE_DIR, "logs")
DB_PATH            = os.path.join(DB_DIR, "gdp_nowcast.db")
DB_URL             = f"sqlite:///{DB_PATH}"

# -- Country-wise RAW dirs
COUNTRY_RAW_DIRS = {
    c: os.path.join(DATA_RAW_DIR, c)
    for c in ["us", "india", "japan", "germany"]
}

# -- FRED Series: US
FRED_SERIES = {
    "gdp":       "GDPC1",      # Real GDP, quarterly
    "cpi":       "CPIAUCSL",   # CPI, monthly
    "m2":        "M2SL",       # M2 Money Supply, monthly
    "fed_funds": "FEDFUNDS",   # Federal Funds Rate, monthly
    "unrate":    "UNRATE",     # Unemployment Rate, monthly
    "indpro":    "INDPRO",     # Industrial Production, monthly
}
FRED_SERIES_US = FRED_SERIES  # backward-compat alias

# -- FRED Series: Japan (OECD series mirrored on FRED)
FRED_SERIES_JAPAN = {
    "gdp":           "NAEXKP01JPQ657S",  # Real GDP vol index, quarterly SA
    "cpi":           "JPNCPIALLMINMEI",  # CPI all items, monthly
    "indpro":        "JPNPROINDMISMEI",  # Industrial production, monthly
    "unrate":        "LRUNTTTTJPM156S",   # Unemployment rate, monthly (OECD)
    "interest_rate": "IRSTCI01JPM156N",  # Short-term interest rate, monthly
}

# -- FRED Series: Germany (Eurostat/OECD series on FRED)
FRED_SERIES_GERMANY = {
    "gdp":           "CLVMNACSCAB1GQDE",   # Real GDP, quarterly SA
    "cpi":           "DEUCPIALLMINMEI",    # CPI all items, monthly
    "indpro":        "DEUPROINDQISMEI",    # Industrial production, quarterly (OECD)
    "unrate":        "LRHUTTTTDEM156S",    # Unemployment rate, monthly
    "interest_rate": "IRSTCI01DEM156N",    # Short-term interest rate, monthly
    "brent_crude":   "MCOILBRENTEU",       # Brent Crude Oil Prices (proxy for Energy Crisis), monthly
    "sentiment":     "BCCICP02DEM460S",    # Business Tendency Surveys: Composite Business Indicator, monthly
}

# -- FRED Series: India (limited coverage on FRED)
FRED_SERIES_INDIA = {
    "cpi":    "INDCPIALLMINMEI",  # CPI all items, monthly
    "unrate": "LRUNTTTTINQ156S",  # Unemployment rate, quarterly
}

# -- World Bank Indicators (wbdata, annual)
WB_INDICATORS = {
    "gdp_growth_pct":    "NY.GDP.MKTP.KD.ZG",  # GDP growth annual %
    "cpi_inflation_pct": "FP.CPI.TOTL.ZG",      # CPI inflation annual %
    "unemployment_pct":  "SL.UEM.TOTL.ZS",      # Unemployment % of labor force
    "trade_bal_gdp_pct": "NE.RSB.GNFS.ZS",      # Trade balance % of GDP
    "gross_savings_pct": "NY.GNS.ICTR.ZS",       # Gross savings % of GDP
    "gdp_usd":           "NY.GDP.MKTP.CD",        # GDP current USD
}

WB_COUNTRY_CODES = {
    "us":      "US",
    "india":   "IN",
    "japan":   "JP",
    "germany": "DE",
}

# -- OECD SDMX-JSON API (quarterly GDP + leading indicators)
OECD_BASE_URL  = "https://stats.oecd.org/sdmx-json/data"
OECD_COUNTRIES = {"japan": "JPN", "germany": "DEU"}
