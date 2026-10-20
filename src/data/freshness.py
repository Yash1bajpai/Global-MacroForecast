"""Input freshness and availability checks. Missing recent data stays missing.

Criterion (explicit): measured against the last quarter that has a GDP target (T),
an indicator is STALE if its last non-missing quarter is more than MAX_LAG_QUARTERS
(1) before T, or it has no values. Reason for 1: the model's features use quarter
t-2, so forecasting quarter T+1 needs data for T-1. A lag of 2 or more means that
forecast could not be made from that indicator.
Separately reported (not failing): quarters since AVAILABILITY_START with a missing
value, and the share of rolling-evaluation origins (from AVAILABILITY_START) at which
the t-2 value exists.
"""
import sys
import pandas as pd

LEVEL_COLS = ('gdp_level', 'cpi_level', 'm2_level', 'indpro_level', 'unrate', 'fed_funds_rate',
              'interest_rate', 'brent_crude', 'sentiment', 'oecd_leading_index')
MAX_LAG_QUARTERS = 1
AVAILABILITY_START = pd.Timestamp('2010-01-01')


def _lag(end, last):
    return (end.year - last.year) * 4 + (end.quarter - last.quarter)


def freshness_report(master, max_lag_quarters=MAX_LAG_QUARTERS):
    """Return {column: dict(last, lag_quarters, stale)} versus the last GDP quarter."""
    end = master.gdp_growth.last_valid_index()
    out = {}
    for col in master.columns:
        if col not in LEVEL_COLS:
            continue
        last = master[col].last_valid_index()
        lag = None if last is None else _lag(end, last)
        out[col] = dict(last=None if last is None else last.date().isoformat(),
                        lag_quarters=lag, stale=last is None or lag > max_lag_quarters)
    return out


def stale_columns(master, max_lag_quarters=MAX_LAG_QUARTERS):
    return sorted(c for c, v in freshness_report(master, max_lag_quarters).items() if v['stale'])


def availability_report(master, start=AVAILABILITY_START):
    """Missing quarters since `start` and share of origins with the t-2 value present."""
    window = master.loc[master.index >= start]
    out = {}
    for col in master.columns:
        if col not in LEVEL_COLS:
            continue
        s = master[col]
        missing = [f'{d.year}-Q{d.quarter}' for d in window.index[s.loc[window.index].isna()]]
        origins = window.index[window.index >= start]
        have = s.shift(2).loc[origins].notna()
        out[col] = dict(missing_quarters=missing, origins=int(len(origins)),
                        origin_availability=float(have.mean()) if len(origins) else None)
    return out


if __name__ == '__main__':
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    failed = False
    for country in ('us', 'india', 'japan', 'germany'):
        master = pd.read_csv(root / f'data/processed/{country}_master.csv', index_col=0, parse_dates=True)
        end = master.gdp_growth.last_valid_index()
        fr, av = freshness_report(master), availability_report(master)
        print(f'{country}: last GDP quarter {end.date()} (stale if lag > {MAX_LAG_QUARTERS} quarter)')
        for col, v in fr.items():
            a = av[col]
            print(f'   {col:20s} last={v["last"]} lag={v["lag_quarters"]} stale={v["stale"]} '
                  f'origin_availability={a["origin_availability"]:.2f} missing_since_2010={a["missing_quarters"] or "none"}')
        failed |= bool(stale_columns(master))
    if failed:
        sys.exit('STALE INPUTS: see lines above (fail-closed)')
