"""Official OECD SDMX source for series whose FRED mirrors froze.

Replaces FRED copies of OECD MEI series that stopped updating (JP/IN/DE CPI,
JP/DE industrial production). Same OECD series family (base 2015=100, seasonally
adjusted for production). Each refresh is checked for continuity against the file
it replaces and recorded in data/raw/SOURCES.json. Missing data stays missing.
"""
import io
import json
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
BASE = 'https://sdmx.oecd.org/public/rest/data/'
G20 = 'OECD.SDD.TPS,DSD_G20_PRICES@DF_G20_PRICES,1.0'
CPI_ALL = 'OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0'
KEI = 'OECD.SDD.STES,DSD_KEI@DF_KEI,4.0'
# (country, raw file name) -> (dataflow, key, description)
SPECS = {
    ('japan', 'cpi'): (G20, 'JPN.M.N.CPI.IX._T.N._Z', 'CPI all items, index 2015=100, monthly'),
    ('india', 'cpi'): (G20, 'IND.M.N.CPI.IX._T.N._Z', 'CPI all items, index 2015=100, monthly'),
    ('germany', 'cpi'): (CPI_ALL, 'DEU.M.N.CPI.IX._T.N._Z', 'CPI all items, index 2015=100, monthly'),
    ('japan', 'indpro'): (KEI, 'JPN.M.PRVM.IX.BTE.Y._Z', 'Production volume, industry excl. construction, SA, 2015=100, monthly'),
    ('germany', 'indpro'): (KEI, 'DEU.M.PRVM.IX.BTE.Y._Z', 'Production volume, industry excl. construction, SA, 2015=100, monthly'),
}
MAX_LEVEL_DEVIATION = 0.015   # max |new/old - 1| on overlapping months
MIN_GROWTH_CORR = 0.95        # month-over-month growth correlation on overlap


def parse_sdmx_csv(text):
    df = pd.read_csv(io.StringIO(text))
    if not {'TIME_PERIOD', 'OBS_VALUE'} <= set(df.columns):
        raise ValueError('Unexpected SDMX payload: missing TIME_PERIOD/OBS_VALUE')
    df = df[['TIME_PERIOD', 'OBS_VALUE']].dropna()
    if df.TIME_PERIOD.duplicated().any():
        raise ValueError('Duplicate periods: key is not a single series')
    s = pd.Series(df.OBS_VALUE.astype(float).to_numpy(), index=pd.to_datetime(df.TIME_PERIOD + '-01'), name='value')
    return s.sort_index()


def continuity_report(new, old):
    """Compare a replacement to the series it replaces on overlapping periods."""
    old = old.copy(); old.index = pd.to_datetime(old.index)
    joined = pd.concat([new, old], axis=1, keys=['new', 'old']).dropna()
    # monthly files only; quarterly legacy files are compared after quarterly averaging
    if len(joined) < 24:
        raise ValueError(f'Overlap too short to verify continuity ({len(joined)} periods)')
    ratio = joined.new / joined.old
    corr = float(joined.pct_change().dropna().corr().iloc[0, 1])
    return dict(overlap=len(joined), overlap_start=joined.index[0].date().isoformat(),
                overlap_end=joined.index[-1].date().isoformat(),
                max_level_deviation=float((ratio - 1).abs().max()), growth_corr=corr)


def check_continuity(report):
    if report['max_level_deviation'] > MAX_LEVEL_DEVIATION or report['growth_corr'] < MIN_GROWTH_CORR:
        raise ValueError(f'Replacement series does not continue the old one: {report}')


def fetch_text(dataflow, key, session=None):
    import requests
    r = (session or requests).get(f'{BASE}{dataflow}/{key}', params={'startPeriod': '2000-01'},
                                  headers={'Accept': 'application/vnd.sdmx.data+csv'}, timeout=90)
    r.raise_for_status()
    return r.text


def _legacy_monthly(path):
    old = pd.read_csv(path, parse_dates=['date']).set_index('date')['value']
    return old


def refresh(raw_dir=None, specs=SPECS, fetcher=fetch_text):
    raw_dir = Path(raw_dir or ROOT / 'data/raw')
    sources_path = raw_dir / 'SOURCES.json'
    sources = json.loads(sources_path.read_text()) if sources_path.exists() else {}
    for (country, name), (flow, key, desc) in specs.items():
        new = parse_sdmx_csv(fetcher(flow, key))
        path = raw_dir / country / f'{name}.csv'
        entry = dict(source='OECD SDMX API', url=f'{BASE}{flow}/{key}', description=desc,
                     fetched=date.today().isoformat(), first=new.index[0].date().isoformat(),
                     last=new.index[-1].date().isoformat(), rows=int(len(new)))
        if path.exists():
            old = _legacy_monthly(path)
            monthly = len(old) < 2 or old.index.to_series().diff().median() < pd.Timedelta(days=40)
            if not monthly:
                # a quarterly file (the original FRED Germany IP): compare on means of complete quarters
                counts = new.resample('QS').count()
                qm = new.resample('QS').mean()[counts == 3]
                rep = continuity_report(qm, old)
            else:
                rep = continuity_report(new, old)
            check_continuity(rep)
            entry['continuity_vs_replaced_file'] = rep
        new.rename('value').rename_axis('date').reset_index().to_csv(path, index=False)
        sources[f'{country}/{name}'] = entry
    sources_path.write_text(json.dumps(sources, indent=2, sort_keys=True))
    return sources


if __name__ == '__main__':
    for k, v in refresh().items():
        print(k, v['last'], v.get('continuity_vs_replaced_file'))
