"""Expanding-origin, embargoed validation. No test labels select a model."""
from pathlib import Path
import json
import warnings
import numpy as np
import pandas as pd
import lightgbm as lgb
from statsmodels.tsa.statespace.sarimax import SARIMAX
from src.data.build_features import causal_features, COUNTRIES

ROOT = Path(__file__).resolve().parents[2]
VALIDATION_START = pd.Timestamp('2016-01-01')
TEST_START = pd.Timestamp('2020-01-01')
CONFIGS = [dict(num_leaves=4, max_depth=2, n_estimators=60),
           dict(num_leaves=8, max_depth=3, n_estimators=100)]
ORDERS = [(1, 0, 0), (1, 0, 1)]


def metrics(actual, prediction):
    a, p = np.asarray(actual, float), np.asarray(prediction, float)
    if len(a) == 0 or a.shape != p.shape or not np.isfinite(a).all() or not np.isfinite(p).all():
        raise ValueError('Empty, mismatched or nonfinite evaluation')
    return dict(rmse=float(np.sqrt(np.mean((a-p)**2))),
                mae=float(np.mean(np.abs(a-p))),
                sign_accuracy=float(np.mean(np.sign(a) == np.sign(p))*100))


def train_indices(index, origin):
    # t-1 GDP is not assumed published at the end of t-1.
    return index <= origin - pd.DateOffset(months=6)


def fit_lgbm(X, y, config):
    return lgb.LGBMRegressor(**config, learning_rate=.03, min_child_samples=10,
                            reg_alpha=.5, reg_lambda=.5, verbosity=-1,
                            random_state=42, n_jobs=1).fit(X, y)


def sarima_prediction(y, order, steps=2):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        model = SARIMAX(y.to_numpy(), order=order, trend='c',
                        enforce_stationarity=False, enforce_invertibility=False).fit(disp=False, maxiter=100)
    # Do not silently promote a nonconverged fit.
    if not model.mle_retvals.get('converged', False):
        raise ValueError('SARIMA did not converge')
    return float(np.asarray(model.forecast(steps))[-1])


def origin_predictions(master):
    df = causal_features(master)
    X, y = df.drop(columns='gdp_growth'), df.gdp_growth
    rows = []
    for origin in df.index[df.index >= VALIDATION_START]:
        mask = train_indices(df.index, origin)
        train_y = y[mask]
        if len(train_y) < 24:
            raise ValueError('Insufficient training history')
        # Available last GDP is t-2; seasonal naive is y[t-4].
        row = dict(date=origin.isoformat(), actual=float(y.loc[origin]),
                   train_end=df.index[mask][-1].isoformat(), mean=float(train_y.mean()),
                   last=float(train_y.iloc[-1]), seasonal=float(y.loc[origin-pd.DateOffset(months=12)]))
        for i, config in enumerate(CONFIGS):
            model = fit_lgbm(X[mask], train_y, config)
            row[f'lgbm_{i}'] = float(model.predict(X.loc[[origin]])[0])
        for i, order in enumerate(ORDERS):
            try:
                row[f'sarima_{i}'] = sarima_prediction(train_y, order)
            except (ValueError, np.linalg.LinAlgError):
                row[f'sarima_{i}'] = None
        rows.append(row)
    return pd.DataFrame(rows).set_index('date')


def select(validation):
    # Validation only: all parameters and blend weights frozen before test.
    options = []
    for i in range(len(CONFIGS)):
        for j in range(len(ORDERS)):
            for w in (0., .25, .5, .75, 1.):
                if w and validation[f'sarima_{j}'].isna().any():
                    continue
                p = validation[f'lgbm_{i}'].to_numpy() * (1-w)
                if w:
                    p += validation[f'sarima_{j}'].to_numpy() * w
                options.append((metrics(validation.actual, p)['rmse'], i, j, w))
    _, i, j, w = min(options)
    return dict(lgbm_config=i, sarima_order=j, w_sarima=w, w_lgbm=1-w)


def blend(frame, choice):
    pred = frame[f'lgbm_{choice["lgbm_config"]}'].to_numpy() * choice['w_lgbm']
    if choice['w_sarima']:
        pred += frame[f'sarima_{choice["sarima_order"]}'].to_numpy() * choice['w_sarima']
    return pred


def evaluate(master):
    predictions = origin_predictions(master)
    dates = pd.to_datetime(predictions.index)
    validation, test = predictions[dates < TEST_START], predictions[dates >= TEST_START]
    if len(validation) < 12 or len(test) < 8:
        raise ValueError('Not enough validation/test origins')
    choice = select(validation)
    report = dict(protocol='revised-data-t2-embargo-v1', choice=choice, validation_n=len(validation), test_n=len(test),
                  test_start=test.index[0], test_end=test.index[-1],
                  validation={}, test={})
    for name, frame in [('validation', validation), ('test', test)]:
        frame = frame.copy()
        frame['ensemble'] = blend(frame, choice)
        for method in ['ensemble', 'mean', 'last', 'seasonal']:
            report[name][method] = metrics(frame.actual, frame[method])
        report[name]['always_positive'] = float((frame.actual > 0).mean()*100)
    predictions['ensemble'] = blend(predictions, choice)
    return report, predictions


def quality_gate(candidate, incumbent=None):
    """Fail closed. Same dates/protocol required. Both RMSE and MAE must improve.

    Test is an operational regression gate, not a fresh scientific holdout once
    inspected/reused. Automatic publishing is disabled even after this gate.
    """
    for country in COUNTRIES:
        c = candidate[country]
        for split in ['validation', 'test']:
            for metric in ['rmse', 'mae']:
                value = c[split]['ensemble'][metric]
                refs = [c[split][b][metric] for b in ['mean', 'last', 'seasonal']]
                if not np.isfinite(value) or any(not np.isfinite(r) for r in refs) or value >= min(refs):
                    raise ValueError(f'{country}: no strict {split} {metric} skill vs all baselines')
        if incumbent is None:
            raise ValueError('No causal incumbent approved yet; manual review required')
        old = incumbent[country]
        if c.get('protocol') != 'revised-data-t2-embargo-v1' or old.get('protocol') != c.get('protocol'):
            raise ValueError('Incumbent protocol missing or different')
        if (c['test_start'], c['test_end'], c['test_n']) != (old['test_start'], old['test_end'], old['test_n']):
            raise ValueError('Incumbent dates differ; same-origin reevaluation required')
        for metric in ['rmse', 'mae']:
            if not np.isfinite(old['test']['ensemble'][metric]) or c['test']['ensemble'][metric] > old['test']['ensemble'][metric]:
                raise ValueError(f'{country}: worse than incumbent on {metric}')


def run(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    reports = {}
    for country in COUNTRIES:
        master = pd.read_csv(ROOT / f'data/processed/{country}_master.csv', index_col=0, parse_dates=True)
        reports[country], predictions = evaluate(master)
        predictions.to_csv(output / f'{country}_origins.csv')
        print(country, reports[country], flush=True)
    (output / 'evaluation.json').write_text(json.dumps(reports, indent=2, allow_nan=False))
    return reports


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='candidate_artifacts')
    args = parser.parse_args()
    run(args.output)
