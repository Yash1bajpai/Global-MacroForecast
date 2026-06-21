import os
import sys
import warnings
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, mean_absolute_error

warnings.filterwarnings("ignore")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from config.settings import DATA_PROCESSED_DIR, MODELS_DIR

FEATURES_DIR = os.path.join(PROJECT_ROOT, "data", "features")
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs("notebooks", exist_ok=True)

TRAIN_END  = "2019-10-01"
TEST_START = "2020-01-01"


def load_series(country):
    df = pd.read_csv(
        os.path.join(DATA_PROCESSED_DIR, f"{country}_master.csv"),
        index_col=0, parse_dates=True
    )
    series = df["gdp_growth"].dropna()
    series.index = pd.DatetimeIndex(series.index, freq="QS")
    return series


def load_features(country):
    df = pd.read_csv(
        os.path.join(FEATURES_DIR, f"{country}_features.csv"),
        index_col=0, parse_dates=True
    )
    drop = [c for c in ["gdp_level", "country", "country_id"] if c in df.columns]
    df   = df.drop(columns=drop)
    y    = df["gdp_growth"]
    X    = df.drop(columns=["gdp_growth"])
    return X, y


def sarima_preds(country, test_index):
    model_path = os.path.join(MODELS_DIR, f"{country}_sarima.pkl")
    if not os.path.exists(model_path):
        return None
    fitted = joblib.load(model_path)
    series = load_series(country)
    train  = series[:TRAIN_END]
    n_test = len(test_index)
    fc     = fitted.get_forecast(steps=n_test).predicted_mean
    fc.index = test_index
    return fc


def lgbm_preds(country, X_test):
    model_path = os.path.join(MODELS_DIR, f"{country}_lgbm.pkl")
    fitted     = joblib.load(model_path)
    preds      = fitted.predict(X_test)
    return pd.Series(preds, index=X_test.index)


def inverse_rmse_weights(rmse_a, rmse_b):
    w_a = (1 / rmse_a) / (1 / rmse_a + 1 / rmse_b)
    w_b = (1 / rmse_b) / (1 / rmse_a + 1 / rmse_b)
    return round(w_a, 3), round(w_b, 3)


print("=" * 60)
print("MASTER ENSEMBLE MODEL")
print("Strategy: Inverse-RMSE weighted average of SARIMA + LightGBM")
print("=" * 60)

countries  = ["us", "japan", "germany", "india"]
summary    = []
all_preds  = {}

for country in countries:
    print(f"\n{'='*60}")
    print(f"Country: {country.upper()}")

    X, y     = load_features(country)
    X_test   = X[X.index >= TEST_START]
    y_test   = y[y.index >= TEST_START]
    test_idx = y_test.index

    lgbm_fc  = lgbm_preds(country, X_test)

    if country == "india":
        ensemble = lgbm_fc
        w_sarima, w_lgbm = 0.0, 1.0
        sarima_rmse = None
        print("  SARIMA: skipped (India — annual data only)")
    else:
        sarima_fc = sarima_preds(country, test_idx)
        sarima_rmse = np.sqrt(mean_squared_error(y_test, sarima_fc))
        lgbm_rmse   = np.sqrt(mean_squared_error(y_test, lgbm_fc))

        w_sarima, w_lgbm = inverse_rmse_weights(sarima_rmse, lgbm_rmse)
        ensemble = w_sarima * sarima_fc + w_lgbm * lgbm_fc

        print(f"  SARIMA RMSE : {sarima_rmse:.4f}%  weight={w_sarima}")
        print(f"  LightGBM RMSE: {lgbm_rmse:.4f}%  weight={w_lgbm}")

    ens_rmse = np.sqrt(mean_squared_error(y_test, ensemble))
    ens_mae  = mean_absolute_error(y_test, ensemble)
    print(f"  Ensemble RMSE: {ens_rmse:.4f}%")
    print(f"  Ensemble MAE : {ens_mae:.4f}%")

    comparison = pd.DataFrame({
        "Actual"  : y_test.round(3),
        "Ensemble": ensemble.round(3),
        "Error"   : (y_test - ensemble).round(3),
    })
    print(f"\n  Actual vs Ensemble:")
    print(comparison.to_string())

    summary.append({
        "country"     : country.upper(),
        "sarima_rmse" : round(sarima_rmse, 4) if sarima_rmse else "skipped",
        "lgbm_rmse"   : round(np.sqrt(mean_squared_error(y_test, lgbm_fc)), 4),
        "ensemble_rmse": round(ens_rmse, 4),
        "ensemble_mae" : round(ens_mae, 4),
        "w_sarima"    : w_sarima,
        "w_lgbm"      : w_lgbm,
    })
    all_preds[country] = {"y_test": y_test, "ensemble": ensemble}

print("\n" + "=" * 60)
print("FINAL SUMMARY — ALL COUNTRIES")
print("=" * 60)
summary_df = pd.DataFrame(summary)
print(summary_df.to_string(index=False))

summary_path = os.path.join(DATA_PROCESSED_DIR, "model_summary.csv")
summary_df.to_csv(summary_path, index=False)
print(f"\nSaved: {summary_path}")

fig, axes = plt.subplots(2, 2, figsize=(16, 10))
axes = axes.flatten()
for i, country in enumerate(countries):
    X, y    = load_features(country)
    y_train = y[y.index <= TRAIN_END]
    y_test  = all_preds[country]["y_test"]
    ensemble = all_preds[country]["ensemble"]
    ax = axes[i]
    ax.plot(y_train.index, y_train,   label="Train",    color="steelblue", linewidth=1.5)
    ax.plot(y_test.index,  y_test,    label="Actual",   color="green",     linewidth=2)
    ax.plot(y_test.index,  ensemble,  label="Ensemble", color="red",       linestyle="--", linewidth=2)
    ax.axvline(pd.Timestamp(TEST_START), color="black", linestyle=":", linewidth=1)
    ax.set_title(f"{country.upper()} - Ensemble Forecast", fontsize=11)
    ax.set_ylabel("QoQ GDP Growth (%)")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
plt.suptitle("Master Ensemble Model (SARIMA + LightGBM) — All Countries", fontsize=14)
plt.tight_layout()
plt.savefig("notebooks/master_ensemble_forecast.png", dpi=150)
plt.close()
print("Plot saved: notebooks/master_ensemble_forecast.png")
print("\nDone.")
