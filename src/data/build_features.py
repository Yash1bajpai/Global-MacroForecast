"""Causal, revised-data research features, not a point-in-time vintage backtest.

Origin is the end of t-1. Use t-2 GDP/indicators to allow a full quarter of
release delay. Annual WB data and hindsight shock/recession flags are excluded.
The fixed embargo is conservative, not proof of historical availability.
"""
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / 'data/processed'
FEATURES_DIR = PROJECT_ROOT / 'data/features'
COUNTRIES = ['us', 'india', 'japan', 'germany']
COUNTRY_ID_MAP = {c: i for i, c in enumerate(COUNTRIES)}
SIGNALS = ['cpi_growth', 'indpro_growth', 'm2_growth', 'unrate',
           'fed_funds_rate', 'interest_rate', 'brent_crude', 'sentiment']


def causal_features(master):
    if not master.index.is_monotonic_increasing or master.index.has_duplicates:
        raise ValueError('Expected ordered, unique quarters')
    expected = pd.date_range(master.index.min(), master.index.max(), freq='QS')
    if not master.index.equals(expected):
        raise ValueError('Quarterly gaps must be repaired, not compressed into lags')
    out = pd.DataFrame(index=master.index)
    out['gdp_growth'] = master['gdp_growth']
    out['quarter'] = master.index.quarter
    for lag in range(2, 6):
        out[f'gdp_growth_lag{lag}'] = master.gdp_growth.shift(lag)
    for window in (2, 4):
        past = master.gdp_growth.shift(2).rolling(window)
        out[f'gdp_growth_roll{window}_mean'] = past.mean()
        out[f'gdp_growth_roll{window}_std'] = past.std()
    out['gdp_growth_yoy'] = master.gdp_growth.shift(2).rolling(4).sum()
    for col in SIGNALS:
        if col in master:
            out[f'{col}_lag2'] = master[col].shift(2)
            out[f'{col}_lag3'] = master[col].shift(3)
            out[f'{col}_diff_lag2'] = master[col].diff().shift(2)
    return out.replace([np.inf, -np.inf], np.nan)


def build_country_features(country):
    df = causal_features(pd.read_csv(PROCESSED_DIR / f'{country}_master.csv',
                                   index_col=0, parse_dates=True))
    df.to_csv(FEATURES_DIR / f'{country}_features.csv')
    return df


def run():
    FEATURES_DIR.mkdir(parents=True, exist_ok=True)
    frames = []
    for country in COUNTRIES:
        df = build_country_features(country)
        df['country'], df['country_id'] = country, COUNTRY_ID_MAP[country]
        frames.append(df)
    pd.concat(frames).sort_index().to_csv(FEATURES_DIR / 'global_features.csv')


if __name__ == '__main__':
    run()
