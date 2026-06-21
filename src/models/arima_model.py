import os
import sys
import warnings
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from sklearn.metrics import mean_squared_error, mean_absolute_error

warnings.filterwarnings("ignore")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from config.settings import DATA_PROCESSED_DIR, MODELS_DIR

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs("notebooks", exist_ok=True)

df = pd.read_csv(
    os.path.join(DATA_PROCESSED_DIR, "us_master.csv"),
    index_col=0,
    parse_dates=True
)

series = df["gdp_growth"].dropna()
series.index = pd.DatetimeIndex(series.index, freq="QS")

print("=" * 55)
print("US GDP Growth - SARIMA Model")
print("=" * 55)
print(f"Total observations : {len(series)}")
print(f"Date range         : {series.index[0].date()} to {series.index[-1].date()}")
print(f"Mean               : {series.mean():.3f}%")
print(f"Std                : {series.std():.3f}%")
print(f"Min                : {series.min():.3f}%  (COVID Q2-2020)")
print(f"Max                : {series.max():.3f}%  (COVID rebound Q3-2020)")

fig, axes = plt.subplots(1, 2, figsize=(14, 4))
plot_acf(series, lags=16, ax=axes[0], title="ACF - US GDP Growth")
plot_pacf(series, lags=16, ax=axes[1], title="PACF - US GDP Growth")
plt.tight_layout()
plt.savefig("notebooks/us_acf_pacf.png", dpi=150)
plt.close()

TRAIN_END  = "2019-10-01"
TEST_START = "2020-01-01"

train = series[:TRAIN_END]
test  = series[TEST_START:]

print(f"\nTrain : {train.index[0].date()} to {train.index[-1].date()} | {len(train)} obs")
print(f"Test  : {test.index[0].date()}  to {test.index[-1].date()}  | {len(test)} obs")

print("\nFitting SARIMA(1,0,1)(0,0,0,4)...")

model = SARIMAX(
    train,
    order=(1, 0, 1),
    seasonal_order=(0, 0, 0, 4),
    enforce_stationarity=False,
    enforce_invertibility=False
)

fitted_model = model.fit(disp=False)

print("\n" + "=" * 55)
print("MODEL SUMMARY")
print("=" * 55)
print(fitted_model.summary())

forecast_obj = fitted_model.get_forecast(steps=len(test))
forecast     = forecast_obj.predicted_mean
conf_int     = forecast_obj.conf_int(alpha=0.05)

forecast.index     = test.index
conf_int.index     = test.index

rmse = np.sqrt(mean_squared_error(test, forecast))
mae  = mean_absolute_error(test, forecast)
mape = np.mean(np.abs((test - forecast) / test)) * 100

print("\n" + "=" * 55)
print("TEST SET PERFORMANCE (2020-Q1 to 2026-Q1)")
print("=" * 55)
print(f"RMSE : {rmse:.4f}%")
print(f"MAE  : {mae:.4f}%")
print(f"MAPE : {mape:.2f}%")

print("\nActual vs Forecast (quarter by quarter):")
comparison = pd.DataFrame({
    "Actual"  : test.round(3),
    "Forecast": forecast.round(3),
    "Error"   : (test - forecast).round(3)
})
print(comparison.to_string())

fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(train.index, train, label="Train (actual)", color="steelblue")
ax.plot(test.index,  test,  label="Test (actual)",  color="green",  linewidth=2)
ax.plot(forecast.index, forecast, label="SARIMA Forecast", color="red", linestyle="--", linewidth=2)
ax.fill_between(
    conf_int.index,
    conf_int.iloc[:, 0],
    conf_int.iloc[:, 1],
    color="red", alpha=0.15, label="95% Confidence Interval"
)
ax.axvline(pd.Timestamp(TEST_START), color="black", linestyle=":", linewidth=1.5, label="Train/Test cutoff")
ax.set_title("US GDP Growth - SARIMA(1,0,1) Forecast vs Actual", fontsize=13)
ax.set_xlabel("Quarter")
ax.set_ylabel("QoQ GDP Growth (%)")
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("notebooks/us_sarima_forecast.png", dpi=150)
plt.close()
print("\nForecast plot saved: notebooks/us_sarima_forecast.png")

model_path = os.path.join(MODELS_DIR, "us_sarima.pkl")
joblib.dump(fitted_model, model_path)
print(f"Model saved       : {model_path}")

print("\n" + "=" * 55)
print("SARIMA COEFFICIENTS - KEY NUMBERS")
print("=" * 55)
params = fitted_model.params
pvalues = fitted_model.pvalues
for name in params.index:
    sig = "SIGNIFICANT" if pvalues[name] < 0.05 else "not significant"
    print(f"  {name:<20} coef={params[name]:>8.4f}   p={pvalues[name]:.4f}   [{sig}]")

print("\nAIC :", round(fitted_model.aic, 2))
print("BIC :", round(fitted_model.bic, 2))
print("\nDone.")
