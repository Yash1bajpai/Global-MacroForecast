"""Shared training entry point. Never writes deployed artifacts."""
from pathlib import Path
import json
import joblib
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX
from src.data.build_features import causal_features, COUNTRIES
from src.models.validation import ROOT, CONFIGS, ORDERS, fit_lgbm, evaluate


def train_country(country, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    master = pd.read_csv(ROOT / f'data/processed/{country}_master.csv', index_col=0, parse_dates=True)
    report, origins = evaluate(master)
    choice = report['choice']
    df = causal_features(master)
    model = fit_lgbm(df.drop(columns='gdp_growth'), df.gdp_growth, CONFIGS[choice['lgbm_config']])
    joblib.dump(model, output / f'{country}_lgbm.pkl')
    fitted = SARIMAX(df.gdp_growth.to_numpy(), order=ORDERS[choice['sarima_order']], trend='c',
                     enforce_stationarity=False, enforce_invertibility=False).fit(disp=False, maxiter=100)
    if choice['w_sarima'] and not fitted.mle_retvals.get('converged', False):
        raise ValueError('Full-history SARIMA failed to converge; no usable bundle')
    joblib.dump(fitted, output / f'{country}_sarima.pkl')
    origins.to_csv(output / f'{country}_origins.csv')
    # Manifest written last so partial fits cannot look ready.
    (output / f'{country}_manifest.json').write_text(json.dumps(dict(
        status='RESEARCH_ONLY_NOT_APPROVED', features=list(model.feature_name_),
        protocol='revised-data-t2-embargo-v1', report=report), indent=2, allow_nan=False))
    return report


def run(output):
    reports = {c: train_country(c, output) for c in COUNTRIES}
    (Path(output) / 'evaluation.json').write_text(json.dumps(reports, indent=2, allow_nan=False))
    return reports


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='candidate_artifacts')
    parser.add_argument('--country', choices=COUNTRIES)
    args = parser.parse_args()
    if args.country:
        train_country(args.country, args.output)
    else:
        run(args.output)
