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
    os.path.join(FEATURES_DIR, "global_features.csv"),
    index_col=0,
    parse_dates=True
)

TARGET    = "gdp_growth"
DROP_COLS = [c for c in ["gdp_level", "country"] if c in df.columns]
df        = df.drop(columns=DROP_COLS)

y = df[TARGET]
X = df.drop(columns=[TARGET])

print("=" * 55)
print("GLOBAL GDP - LightGBM Model (All 4 Countries)")
print("=" * 55)
print(f"Total rows    : {len(df)}")
print(f"Features      : {X.shape[1]}")
print(f"Date range    : {df.index.min().date()} to {df.index.max().date()}")
print(f"country_id    : 0=US, 1=India, 2=Japan, 3=Germany")
print(f"NaN in X      : {X.isnull().sum().sum()} (expected - union schema of 4 countries)")

TRAIN_END  = "2019-10-01"
TEST_START = "2020-01-01"

X_train = X[df.index <= TRAIN_END]
X_test  = X[df.index >= TEST_START]
y_train = y[df.index <= TRAIN_END]
y_test  = y[df.index >= TEST_START]

print(f"\nTrain : {X_train.index.min().date()} to {X_train.index.max().date()} | {len(X_train)} rows")
print(f"Test  : {X_test.index.min().date()}  to {X_test.index.max().date()}  | {len(X_test)} rows")

params = {
    "objective":        "regression",
    "metric":           "rmse",
    "learning_rate":    0.03,
    "num_leaves":       15,
    "max_depth":        4,
    "min_child_samples":10,
    "subsample":        0.8,
    "colsample_bytree": 0.7,
    "reg_alpha":        0.3,
    "reg_lambda":       0.3,
    "verbose":         -1,
    "random_state":     42,
}

print("\nTraining Global LightGBM...")

fitted_model = lgb.train(
    params,
    lgb.Dataset(X_train, label=y_train),
    num_boost_round=150,
)

train_pred = fitted_model.predict(X_train)
test_pred  = fitted_model.predict(X_test)

train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
test_rmse  = np.sqrt(mean_squared_error(y_test,  test_pred))
test_mae   = mean_absolute_error(y_test, test_pred)

print("\n" + "=" * 55)
print("GLOBAL PERFORMANCE")
print("=" * 55)
print(f"Train RMSE : {train_rmse:.4f}%")
print(f"Test  RMSE : {test_rmse:.4f}%")
print(f"Test  MAE  : {test_mae:.4f}%")
print(f"Gap        : {test_rmse - train_rmse:.4f}%")

print("\nPerformance by country (test set):")
results = pd.DataFrame({
    "Actual"    : y_test,
    "Predicted" : pd.Series(test_pred, index=y_test.index),
    "country_id": X_test["country_id"],
})
country_names = {0: "US", 1: "India", 2: "Japan", 3: "Germany"}
for cid, cname in country_names.items():
    subset = results[results["country_id"] == cid]
    if len(subset) == 0:
        continue
    rmse = np.sqrt(mean_squared_error(subset["Actual"], subset["Predicted"]))
    mae  = mean_absolute_error(subset["Actual"], subset["Predicted"])
    print(f"  {cname:<10} RMSE={rmse:.4f}%  MAE={mae:.4f}%  n={len(subset)}")

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
ax.barh(top15["feature"][::-1], top15["importance"][::-1], color="darkorange")
ax.set_title("Global LightGBM - Feature Importance (Gain)", fontsize=13)
ax.set_xlabel("Importance (Gain)")
plt.tight_layout()
plt.savefig("notebooks/global_lgbm_importance.png", dpi=150)
plt.close()

fig, axes = plt.subplots(2, 2, figsize=(16, 10))
axes = axes.flatten()
for i, (cid, cname) in enumerate(country_names.items()):
    train_mask = X_train["country_id"] == cid
    test_mask  = X_test["country_id"]  == cid
    ax = axes[i]
    if train_mask.sum() > 0:
        ax.plot(y_train[train_mask].index, y_train[train_mask], label="Train", color="steelblue")
    if test_mask.sum() > 0:
        ax.plot(y_test[test_mask].index, y_test[test_mask], label="Actual", color="green", linewidth=2)
        ax.plot(y_test[test_mask].index,
                results[results["country_id"] == cid]["Predicted"],
                label="Forecast", color="red", linestyle="--", linewidth=2)
    ax.axvline(pd.Timestamp(TEST_START), color="black", linestyle=":", linewidth=1)
    ax.set_title(f"{cname} - Global Model Forecast", fontsize=11)
    ax.set_ylabel("QoQ GDP Growth (%)")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
plt.suptitle("Global LightGBM - All Countries", fontsize=14)
plt.tight_layout()
plt.savefig("notebooks/global_lgbm_forecast.png", dpi=150)
plt.close()
print("\nPlots saved: notebooks/global_lgbm_forecast.png, notebooks/global_lgbm_importance.png")

model_path = os.path.join(MODELS_DIR, "global_lgbm.pkl")
joblib.dump(fitted_model, model_path)
print(f"Model saved : {model_path}")
print("\nDone.")
