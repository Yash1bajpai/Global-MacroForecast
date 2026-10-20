"""Pre-declared simple-model evaluation (research only, never writes deployed artifacts).

Protocol (declared before running):
- origin t uses data through t-2 only (same 6-month embargo as validation.py)
- candidates: mean | ar1 | ridge_gdp | ridge_ind (GDP lags + only indicators fully covered through the last GDP quarter)
- stale series (JP/IN/DE CPI, JP/DE industrial production) are excluded, not filled
- selection window: origins 2010Q1-2019Q4, rule: a non-mean model is chosen only if its RMSE is
  >=3% lower than the mean baseline AND its MAE is not higher; best RMSE among those, else mean
- evaluation window 2020Q1+ is reported once, never used to select
"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.linear_model import RidgeCV
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
ROOT = Path(__file__).resolve().parents[2]
COUNTRIES = ['us', 'india', 'japan', 'germany']
SEL_START, TEST_START = pd.Timestamp('2010-01-01'), pd.Timestamp('2020-01-01')
STALE = {'india': ['cpi_level', 'cpi_growth'], 'japan': ['cpi_level', 'cpi_growth', 'indpro_level', 'indpro_growth'],
         'germany': ['cpi_level', 'cpi_growth', 'indpro_level', 'indpro_growth']}
IND = ['cpi_growth', 'indpro_growth', 'm2_growth', 'unrate', 'fed_funds_rate', 'interest_rate', 'brent_crude', 'sentiment', 'oecd_leading_index']

def build(c):
    m = pd.read_csv(ROOT / f'data/processed/{c}_master.csv', index_col=0, parse_dates=True)
    y = m.gdp_growth
    X = pd.DataFrame(index=m.index)
    X['y2'] = y.shift(2); X['y3'] = y.shift(3); X['r4'] = y.shift(2).rolling(4).mean()
    ind = pd.DataFrame(index=m.index)
    for k in IND:
        if k in m and k not in STALE.get(c, []) and m[k].last_valid_index() >= m.index[-1]:
            ind[k + '_l2'] = m[k].shift(2)
    return y, X, ind

def predict(kind, y, X, ind, origin):
    tr = y.index <= origin - pd.DateOffset(months=6)
    ytr = y[tr]
    if kind == 'mean': return ytr.mean()
    cols = {'ar1': X[['y2']], 'ridge_gdp': X, 'ridge_ind': pd.concat([X, ind], axis=1)}[kind]
    ok = cols[tr].notna().all(axis=1) & ytr.notna()
    if ok.sum() < 20: return np.nan
    mdl = make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-1, 3, 12)))
    mdl.fit(cols[tr][ok], ytr[ok])
    row = cols.loc[[origin]]
    if row.isna().any(axis=None): return np.nan
    return float(mdl.predict(row)[0])

def run():
    kinds = ['mean', 'ar1', 'ridge_gdp', 'ridge_ind']
    out = {}
    for c in COUNTRIES:
        y, X, ind = build(c)
        rows = {k: {} for k in kinds}
        origins = [d for d in y.index if d >= SEL_START and pd.notna(y[d])]
        for d in origins:
            for k in kinds: rows[k][d] = predict(k, y, X, ind, d)
        P = pd.DataFrame(rows).dropna(); a = y.loc[P.index]
        def met(mask):
            return {k: dict(rmse=float(np.sqrt(((a[mask]-P[k][mask])**2).mean())), mae=float((a[mask]-P[k][mask]).abs().mean())) for k in kinds}
        sel, tst = met(P.index < TEST_START), met(P.index >= TEST_START)
        base = sel['mean']; cands = [k for k in kinds[1:] if sel[k]['rmse'] <= .97*base['rmse'] and sel[k]['mae'] <= base['mae']]
        choice = min(cands, key=lambda k: sel[k]['rmse']) if cands else 'mean'
        out[c] = dict(choice=choice, features_ind=list(ind.columns), n_sel=int((P.index < TEST_START).sum()), n_test=int((P.index >= TEST_START).sum()), selection=sel, test=tst)
    return out

if __name__ == '__main__':
    r = run(); Path(sys.argv[1] if len(sys.argv) > 1 else 'reports/simple_eval.json').write_text(json.dumps(r, indent=2))
    for c, v in r.items():
        print(c, 'CHOICE', v['choice'], v['features_ind'], v['n_sel'], v['n_test'])
        for s in ('selection', 'test'): print('  ', s, {k: round(x['rmse'], 3) for k, x in v[s].items()})
