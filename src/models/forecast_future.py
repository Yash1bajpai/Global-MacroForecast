"""
forecast_future.py
8-quarter ahead GDP forecasts for US, India, Japan, Germany.

SARIMA  : apply() to extend to 2026 data, then get_forecast(steps=8)
LightGBM: recursive 1-step-ahead, GDP lags updated at each step,
          other features frozen at last known value
Ensemble: inverse-RMSE weighted average (weights from model_summary.csv)

Run from project root:
    python src/models/forecast_future.py
"""

import os
import sys
import warnings
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.metrics import mean_squared_error, mean_absolute_error
from statsmodels.tsa.statespace.sarimax import SARIMAX

warnings.filterwarnings("ignore")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from config.settings import DATA_PROCESSED_DIR, MODELS_DIR

FEATURES_DIR  = os.path.join(PROJECT_ROOT, "data", "features")
N_QUARTERS    = 8
TRAIN_END     = "2019-10-01"
TEST_START    = "2020-01-01"
SARIMA_ORDER  = (1, 0, 1)
SARIMA_SEAS   = (0, 0, 0, 4)
COUNTRIES     = ["us", "india", "japan", "germany"]


def load_series(country):
    df = pd.read_csv(
        os.path.join(DATA_PROCESSED_DIR, f"{country}_master.csv"),
        index_col=0, parse_dates=True
    )
    s = df["gdp_growth"].dropna()
    s.index = pd.DatetimeIndex(s.index, freq="QS")
    return s


def load_features(country):
    df = pd.read_csv(
        os.path.join(FEATURES_DIR, f"{country}_features.csv"),
        index_col=0, parse_dates=True
    )
    drop = [c for c in ["gdp_level", "country", "country_id"] if c in df.columns]
    df   = df.drop(columns=drop)
    X    = df.drop(columns=["gdp_growth"])
    y    = df["gdp_growth"]
    return X, y


def get_future_index(last_date, n=8):
    return pd.date_range(
        start=last_date + pd.DateOffset(months=3),
        periods=n,
        freq="QS"
    )


def load_ensemble_weights():
    path = os.path.join(DATA_PROCESSED_DIR, "model_summary.csv")
    df   = pd.read_csv(path)
    weights = {}
    for _, row in df.iterrows():
        c = row["country"].lower()
        weights[c] = {
            "sarima": float(row["w_sarima"]),
            "lgbm":   float(row["w_lgbm"]),
        }
    return weights


def sarima_forecast(country, series_full, n_steps, fitted_orig=None):
    """
    Extend saved SARIMA to full series via apply(), then forecast n_steps ahead.
    Falls back to full refit if apply() fails.
    """
    if fitted_orig is None:
        model_path = os.path.join(MODELS_DIR, f"{country}_sarima.pkl")
        if not os.path.exists(model_path):
            return None, None
        fitted_orig = joblib.load(model_path)
    last_date   = series_full.index[-1]
    future_idx  = get_future_index(last_date, n_steps)

    try:
        result_full = fitted_orig.apply(series_full, refit=False)
        fc          = result_full.get_forecast(steps=n_steps)
    except Exception:
        model = SARIMAX(
            series_full,
            order=SARIMA_ORDER,
            seasonal_order=SARIMA_SEAS,
            enforce_stationarity=False,
            enforce_invertibility=False
        )
        result_full = model.fit(disp=False)
        fc          = result_full.get_forecast(steps=n_steps)

    pred_mean = fc.predicted_mean.values
    ci        = fc.conf_int(alpha=0.05).values

    sarima_fc = pd.Series(pred_mean[:n_steps], index=future_idx)
    conf_int  = pd.DataFrame(ci[:n_steps], index=future_idx, columns=["lower_95", "upper_95"])
    return sarima_fc, conf_int


def lgbm_forecast_recursive(country, n_steps, fitted=None, X=None, y=None):
    """
    Recursive 1-step LightGBM forecast.
    GDP lags updated with predictions at each step.
    All other features frozen at last known value (persistence assumption).
    """
    if fitted is None:
        model_path = os.path.join(MODELS_DIR, f"{country}_lgbm.pkl")
        fitted     = joblib.load(model_path)

    if X is None or y is None:
        X, y = load_features(country)
    
    last_date  = X.index[-1]
    future_idx = get_future_index(last_date, n_steps)

    gdp_history = list(y.values)
    last_row    = X.iloc[-1].copy()
    predictions = []

    for step in range(n_steps):
        row = last_row.copy()

        for lag in [1, 2, 3, 4]:
            col = f"gdp_growth_lag{lag}"
            if col in row.index and len(gdp_history) >= lag:
                row[col] = gdp_history[-lag]

        if len(gdp_history) >= 2:
            row["gdp_growth_roll2_mean"] = float(np.mean(gdp_history[-2:]))
            row["gdp_growth_roll2_std"]  = float(np.std(gdp_history[-2:], ddof=1))
        if len(gdp_history) >= 4:
            row["gdp_growth_roll4_mean"] = float(np.mean(gdp_history[-4:]))
            row["gdp_growth_roll4_std"]  = float(np.std(gdp_history[-4:], ddof=1))
            row["gdp_growth_yoy"]        = float(np.sum(gdp_history[-4:]))

        if "quarter" in row.index:
            row["quarter"] = int(future_idx[step].quarter)
        if "recession" in row.index:
            row["recession"] = 0
        if "covid_shock" in row.index:
            row["covid_shock"] = 0

        pred = float(fitted.predict(row.values.reshape(1, -1))[0])
        predictions.append(pred)
        gdp_history.append(pred)

    return pd.Series(predictions, index=future_idx)


def compute_accuracy_metrics(y_true, y_pred, label=""):
    """RMSE, MAE, MAPE, SMAPE, Directional Accuracy, R2, Theil U."""
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    n      = len(y_true)

    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae  = mean_absolute_error(y_true, y_pred)

    nonzero = y_true != 0
    mape  = np.mean(np.abs((y_true[nonzero] - y_pred[nonzero]) / y_true[nonzero])) * 100
    smape = np.mean(2 * np.abs(y_true - y_pred) / (np.abs(y_true) + np.abs(y_pred) + 1e-8)) * 100

    dir_acc = np.mean(np.sign(y_true[1:]) == np.sign(y_pred[1:])) * 100

    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - y_true.mean()) ** 2)
    r2     = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0

    naive     = y_true[:-1]
    theil_num = np.sqrt(np.mean((y_true[1:] - y_pred[1:]) ** 2))
    theil_den = np.sqrt(np.mean((y_true[1:] - naive) ** 2))
    theil_u   = theil_num / theil_den if theil_den > 0 else np.nan

    return {
        "label":       label,
        "n":           n,
        "RMSE":        round(rmse, 4),
        "MAE":         round(mae, 4),
        "MAPE":        round(mape, 2),
        "SMAPE":       round(smape, 2),
        "Dir_Acc":     round(dir_acc, 1),
        "R2":          round(r2, 4),
        "Theil_U":     round(theil_u, 4) if not np.isnan(theil_u) else "N/A",
    }


def print_accuracy_table(metrics_list):
    cols = ["label", "n", "RMSE", "MAE", "MAPE", "SMAPE", "Dir_Acc", "R2", "Theil_U"]
    header = f"  {'Model':<14} {'N':>4} {'RMSE':>7} {'MAE':>7} {'MAPE':>7} {'SMAPE':>7} {'DirAcc':>7} {'R2':>7} {'TheilU':>8}"
    print(header)
    print(f"  {'-'*76}")
    for m in metrics_list:
        print(
            f"  {m['label']:<14} {m['n']:>4} {m['RMSE']:>7} {m['MAE']:>7} "
            f"{m['MAPE']:>6}% {m['SMAPE']:>6}% {m['Dir_Acc']:>6}% {m['R2']:>7} {str(m['Theil_U']):>8}"
        )


def run():
    weights_map = load_ensemble_weights()

    print("=" * 70)
    print("GDP NOWCAST & FORECAST SYSTEM")
    print(f"Generated : {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Horizon   : {N_QUARTERS} quarters ahead")
    print(f"Method    : Inverse-RMSE weighted SARIMA + LightGBM Ensemble")
    print("=" * 70)

    all_forecasts   = {}
    all_conf_ints   = {}
    all_metrics     = {}

    for country in COUNTRIES:
        print(f"\n{'='*70}")
        print(f"  {country.upper()}")
        print(f"{'='*70}")

        series_full = load_series(country)
        X, y        = load_features(country)
        X_test      = X[X.index >= TEST_START]
        y_test      = y[y.index >= TEST_START]
        weights     = weights_map.get(country, {"sarima": 0.0, "lgbm": 1.0})

        # --- Test-set accuracy ---
        lgbm_model  = joblib.load(os.path.join(MODELS_DIR, f"{country}_lgbm.pkl"))
        lgbm_test   = lgbm_model.predict(X_test)

        metrics_list = []
        metrics_list.append(compute_accuracy_metrics(y_test.values, lgbm_test, "LightGBM"))

        if country != "india":
            sarima_fitted = joblib.load(os.path.join(MODELS_DIR, f"{country}_sarima.pkl"))
            sarima_test   = sarima_fitted.get_forecast(steps=len(y_test)).predicted_mean.values
            w_s, w_l      = weights["sarima"], weights["lgbm"]
            ens_test      = w_s * sarima_test + w_l * lgbm_test
            metrics_list.append(compute_accuracy_metrics(y_test.values, sarima_test, "SARIMA"))
            metrics_list.append(compute_accuracy_metrics(y_test.values, ens_test,    "Ensemble"))
        else:
            ens_test = lgbm_test
            metrics_list.append(compute_accuracy_metrics(y_test.values, ens_test, "Ensemble"))

        print(f"\n  Test-Set Accuracy (2020-Q1 to {y_test.index[-1].strftime('%Y-Q') + str(y_test.index[-1].quarter)})")
        print(f"  Theil U < 1 = better than naive random walk  |  Dir Acc = direction correct %")
        print_accuracy_table(metrics_list)
        all_metrics[country] = metrics_list

        # --- Future forecast ---
        lgbm_fc = lgbm_forecast_recursive(country, N_QUARTERS)

        if country != "india":
            sarima_fc, conf_int = sarima_forecast(country, series_full, N_QUARTERS)
            if sarima_fc is not None:
                ensemble = weights["sarima"] * sarima_fc + weights["lgbm"] * lgbm_fc
            else:
                sarima_fc, conf_int, ensemble = None, None, lgbm_fc
        else:
            sarima_fc, conf_int, ensemble = None, None, lgbm_fc

        all_forecasts[country]  = ensemble
        all_conf_ints[country]  = conf_int

        print(f"\n  8-Quarter Forward Forecast (QoQ log-%, annualized approx = x4)")
        hdr = f"  {'Quarter':<10} {'SARIMA':>10} {'LightGBM':>10} {'Ensemble':>10} {'Annualized':>12} {'CI_Low':>8} {'CI_High':>8}"
        print(hdr)
        print(f"  {'-'*74}")

        for date, ens_val in ensemble.items():
            qstr  = f"Q{date.quarter}-{date.year}"
            l_val = f"{lgbm_fc[date]:+.3f}%"
            e_val = f"{ens_val:+.3f}%"
            ann   = f"~{ens_val * 4:+.2f}%"
            s_val = f"{sarima_fc[date]:+.3f}%" if sarima_fc is not None else "    N/A"
            if conf_int is not None:
                ci_lo = f"{conf_int.loc[date, 'lower_95']:+.3f}%"
                ci_hi = f"{conf_int.loc[date, 'upper_95']:+.3f}%"
            else:
                ci_lo = ci_hi = "    N/A"
            print(f"  {qstr:<10} {s_val:>10} {l_val:>10} {e_val:>10} {ann:>12} {ci_lo:>8} {ci_hi:>8}")

        avg_q  = ensemble.mean()
        avg_a  = avg_q * 4
        trend  = "EXPANSION" if avg_q > 0 else "CONTRACTION"
        print(f"\n  Avg QoQ: {avg_q:+.3f}%  |  Avg Annualized: {avg_a:+.2f}%  |  Trend: {trend}")

    # --- Cross-country summary ---
    print(f"\n{'='*70}")
    print("  CROSS-COUNTRY FORECAST SUMMARY")
    print(f"{'='*70}")
    hdr = f"  {'Quarter':<10}"
    for c in COUNTRIES:
        hdr += f"  {c.upper():>10}"
    print(hdr)
    print(f"  {'-'*55}")
    all_dates = sorted(list(set().union(*[all_forecasts[c].index for c in COUNTRIES])))
    for date in all_dates:
        qstr = f"Q{date.quarter}-{date.year}"
        row  = f"  {qstr:<10}"
        for c in COUNTRIES:
            v = all_forecasts[c].get(date, np.nan)
            if pd.isna(v):
                row += "       N/A"
            else:
                row += f"  {v:>+9.3f}%"
        print(row)

    print(f"\n  Notes:")
    print(f"  - QoQ = quarter-on-quarter log-% change")
    print(f"  - Annualized = QoQ x 4 (rough approximation)")
    print(f"  - Confidence intervals from SARIMA component only")
    print(f"  - Forecast uncertainty compounds significantly beyond Q2")
    print(f"  - India SARIMA skipped (annual data repeated quarterly)")


if __name__ == "__main__":
    run()
