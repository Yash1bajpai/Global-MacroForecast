import os
import sys
import warnings
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import lightgbm as lgb
from sklearn.metrics import mean_squared_error, mean_absolute_error

warnings.filterwarnings("ignore")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from config.settings import MODELS_DIR

FEATURES_DIR = os.path.join(PROJECT_ROOT, "data", "features")
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs("notebooks", exist_ok=True)

df = pd.read_csv(
    os.path.join(FEATURES_DIR, "india_features.csv"),
    index_col=0,
    parse_dates=True
)

TARGET    = "gdp_growth"
DROP_COLS = [c for c in ["gdp_level", "country", "country_id"] if c in df.columns]
df        = df.drop(columns=DROP_COLS)

y = df[TARGET]
X = df.drop(columns=[TARGET])

print("=" * 55)
print("INDIA GDP - LightGBM Model")
print("=" * 55)
print(f"Total rows    : {len(df)}")
print(f"Features      : {X.shape[1]}")
print(f"Date range    : {df.index[0].date()} to {df.index[-1].date()}")
print(f"\nNOTE: India GDP is now based on true quarterly MOSPI data (base 2011-12).")
print(f"LightGBM will learn from true quarterly variance, CPI, savings rate, etc.")

TRAIN_END  = "2019-10-01"
TEST_START = "2020-01-01"

X_train = X[:TRAIN_END]
X_test  = X[TEST_START:]
y_train = y[:TRAIN_END]
y_test  = y[TEST_START:]

print(f"\nTrain : {X_train.index[0].date()} to {X_train.index[-1].date()} | {len(X_train)} rows")
print(f"Test  : {X_test.index[0].date()}  to {X_test.index[-1].date()}  | {len(X_test)} rows")

# PARAMS — India (Relaxed now that we have true quarterly data)
# We allow deeper trees to learn from quarterly variance.
params = {
    "objective":         "regression",
    "metric":            "rmse",
    "learning_rate":     0.034,
    "num_leaves":        31,        # Relaxed
    "max_depth":         6,         # Relaxed
    "min_child_samples": 8,
    "min_child_weight":  0.01553,
    "subsample":         0.57,
    "colsample_bytree":  0.78,
    "reg_alpha":         0.1,
    "reg_lambda":        0.1,
    "verbose":          -1,
    "random_state":      42,
}

print("\nTraining LightGBM...")

fitted_model = lgb.train(
    params,
    lgb.Dataset(X_train, label=y_train),
    num_boost_round=200,  # Optuna: was 100
)

train_pred = fitted_model.predict(X_train)
test_pred  = fitted_model.predict(X_test)

train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
test_rmse  = np.sqrt(mean_squared_error(y_test,  test_pred))
test_mae   = mean_absolute_error(y_test, test_pred)

print("\n" + "=" * 55)
print("PERFORMANCE")
print("=" * 55)
print(f"Train RMSE : {train_rmse:.4f}%")
print(f"Test  RMSE : {test_rmse:.4f}%")
print(f"Test  MAE  : {test_mae:.4f}%")
print(f"Gap        : {test_rmse - train_rmse:.4f}%")

print("\nActual vs Predicted:")
comparison = pd.DataFrame({
    "Actual"   : y_test.round(3),
    "Predicted": pd.Series(test_pred, index=y_test.index).round(3),
    "Error"    : (y_test - test_pred).round(3)
})
print(comparison.to_string())

importance = pd.DataFrame({
    "feature":    fitted_model.feature_name(),
    "importance": fitted_model.feature_importance(importance_type="gain"),
}).sort_values("importance", ascending=False).reset_index(drop=True)

print("\n" + "=" * 55)
print("TOP 15 FEATURE IMPORTANCES (gain)")
print("=" * 55)
print(importance.head(15).to_string(index=False))

fig, ax = plt.subplots(figsize=(10, 6))
top15 = importance.head(15)
ax.barh(top15["feature"][::-1], top15["importance"][::-1], color="steelblue")
ax.set_title("India LightGBM - Feature Importance (Gain)", fontsize=13)
ax.set_xlabel("Importance (Gain)")
plt.tight_layout()
plt.savefig("notebooks/india_lgbm_importance.png", dpi=150)
plt.close()

fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(y_train.index, y_train,   label="Train (actual)",    color="steelblue")
ax.plot(y_test.index,  y_test,    label="Test (actual)",     color="green", linewidth=2)
ax.plot(y_test.index,  test_pred, label="LightGBM Forecast", color="red", linestyle="--", linewidth=2)
ax.axvline(pd.Timestamp(TEST_START), color="black", linestyle=":", linewidth=1.5, label="Train/Test cutoff")
ax.set_title("India GDP Growth - LightGBM Forecast vs Actual", fontsize=13)
ax.set_xlabel("Quarter")
ax.set_ylabel("Annual GDP Growth % (WB, forward-filled)", fontsize=11)
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("notebooks/india_lgbm_forecast.png", dpi=150)
plt.close()
print("\nPlots saved: notebooks/india_lgbm_forecast.png, notebooks/india_lgbm_importance.png")

model_path = os.path.join(MODELS_DIR, "india_lgbm.pkl")
joblib.dump(fitted_model, model_path)
print(f"Model saved : {model_path}")
print("\nDone.")
