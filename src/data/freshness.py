"""Stale-input check. Missing recent data stays missing; this only reports it."""
import pandas as pd

LEVEL_COLS = ('gdp_level', 'cpi_level', 'm2_level', 'indpro_level', 'unrate', 'fed_funds_rate',
              'interest_rate', 'brent_crude', 'sentiment', 'oecd_leading_index')


def freshness_report(master, max_lag_quarters=1):
    """Return {column: dict(last, lag_quarters, stale)} versus the last GDP quarter."""
    end = master.gdp_growth.last_valid_index()
    out = {}
    for col in master.columns:
        if col not in LEVEL_COLS:
            continue
        last = master[col].last_valid_index()
        lag = None if last is None else (end.year - last.year) * 4 + (end.quarter - last.quarter)
        out[col] = dict(last=None if last is None else last.date().isoformat(),
                        lag_quarters=lag, stale=last is None or lag > max_lag_quarters)
    return out


def stale_columns(master, max_lag_quarters=1):
    return sorted(c for c, v in freshness_report(master, max_lag_quarters).items() if v['stale'])


if __name__ == '__main__':
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    for country in ('us', 'india', 'japan', 'germany'):
        master = pd.read_csv(root / f'data/processed/{country}_master.csv', index_col=0, parse_dates=True)
        bad = stale_columns(master)
        print(f'{country}: last GDP quarter {master.gdp_growth.last_valid_index().date()}; stale inputs: {bad or "none"}')
