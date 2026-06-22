import pandas as pd, numpy as np, joblib, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, mean_absolute_error
import warnings
warnings.filterwarnings('ignore')

FEATURES_DIR  = 'data/features'
PROCESSED_DIR = 'data/processed'
MODELS_DIR    = 'models_saved'
TEST_START    = '2020-01-01'
TRAIN_END     = '2019-10-01'
COUNTRIES     = ['us', 'japan', 'germany', 'india']
FLAGS         = {'us': '🇺🇸 United States', 'japan': '🇯🇵 Japan',
                 'germany': '🇩🇪 Germany', 'india': '🇮🇳 India'}

results = {}
for c in COUNTRIES:
    df   = pd.read_csv(f'{FEATURES_DIR}/{c}_features.csv', index_col=0, parse_dates=True)
    drop = [col for col in ['gdp_level', 'country', 'country_id'] if col in df.columns]
    df   = df.drop(columns=drop)
    X    = df.drop(columns=['gdp_growth'])
    y    = df['gdp_growth']

    X_train = X[X.index <= TRAIN_END]
    X_test  = X[X.index >= TEST_START]
    y_train = y[y.index <= TRAIN_END]
    y_test  = y[y.index >= TEST_START]

    lgbm       = joblib.load(f'{MODELS_DIR}/{c}_lgbm.pkl')
    lgbm_test  = lgbm.predict(X_test)
    lgbm_train = lgbm.predict(X_train)

    sarima_test = None
    if c != 'india':
        sarima      = joblib.load(f'{MODELS_DIR}/{c}_sarima.pkl')
        sarima_test = sarima.get_forecast(steps=len(y_test)).predicted_mean.values

    summary = pd.read_csv(f'{PROCESSED_DIR}/model_summary.csv')
    row     = summary[summary['country'].str.lower() == c].iloc[0]
    w_l     = float(row['w_lgbm'])
    w_s     = float(row['w_sarima'])

    ens_test = (w_s * sarima_test + w_l * lgbm_test) if sarima_test is not None else lgbm_test

    r_lgbm  = np.sqrt(mean_squared_error(y_test, lgbm_test))
    r_ens   = np.sqrt(mean_squared_error(y_test, ens_test))
    m_lgbm  = mean_squared_error(y_test, lgbm_test)
    m_ens   = mean_squared_error(y_test, ens_test)
    mae_ens = mean_absolute_error(y_test, ens_test)
    dacc    = np.mean(np.sign(y_test.values[1:]) == np.sign(ens_test[1:])) * 100

    results[c] = {
        'y_train': y_train, 'y_test': y_test,
        'lgbm_test': lgbm_test, 'ens_test': ens_test,
        'sarima_test': sarima_test,
        'rmse_lgbm': r_lgbm, 'rmse_ens': r_ens,
        'mse_lgbm': m_lgbm, 'mse_ens': m_ens,
        'mae_ens': mae_ens, 'dir_acc': dacc,
        'w_l': w_l, 'w_s': w_s,
        'n_features': X.shape[1]
    }

# ─── FIGURE 1: Actual vs Predicted ───────────────────────────────────────────
fig, axes = plt.subplots(2, 2, figsize=(18, 12))
fig.patch.set_facecolor('#0d1117')
axes = axes.flatten()

for i, c in enumerate(COUNTRIES):
    ax = axes[i]
    ax.set_facecolor('#161b22')
    r  = results[c]

    ax.plot(r['y_train'].index, r['y_train'].values,
            color='#58a6ff', linewidth=1.0, alpha=0.45, label='Train (actual)')
    ax.plot(r['y_test'].index, r['y_test'].values,
            color='#3fb950', linewidth=2.2, label='Test (actual)')
    ax.plot(r['y_test'].index, r['ens_test'],
            color='#ff7b72', linewidth=2.2, linestyle='--', label='Ensemble Forecast')
    if r['sarima_test'] is not None:
        ax.plot(r['y_test'].index, r['sarima_test'],
                color='#d2a8ff', linewidth=1.2, linestyle=':', alpha=0.7, label='SARIMA only')

    ax.axvline(pd.Timestamp(TEST_START),
               color='#f0e68c', linestyle=':', linewidth=1.5, alpha=0.8, label='Train/Test cutoff')
    ax.axhline(0, color='white', linewidth=0.6, alpha=0.25)

    title_str = FLAGS[c]
    ax.set_title(title_str, color='white', fontsize=13, fontweight='bold', pad=10)

    info = ('RMSE: {:.4f}   MSE: {:.4f}   MAE: {:.4f}   Dir Acc: {:.1f}%'
            '   Features: {}   Ensemble: LGBM {:.0f}% + SARIMA {:.0f}%'.format(
                r['rmse_ens'], r['mse_ens'], r['mae_ens'],
                r['dir_acc'], r['n_features'],
                r['w_l']*100, r['w_s']*100))
    ax.set_xlabel(info, color='#8b949e', fontsize=8)
    ax.set_ylabel('QoQ GDP Growth (raw)', color='#8b949e', fontsize=10)
    ax.tick_params(colors='#8b949e', labelsize=8)
    for sp in ax.spines.values():
        sp.set_edgecolor('#30363d')
    ax.grid(True, color='#21262d', linewidth=0.8, alpha=0.6)
    ax.legend(fontsize=8, facecolor='#0d1117', edgecolor='#30363d', labelcolor='#c9d1d9')

fig.suptitle('Global MacroForecast — Actual vs Predicted (Test: 2020 Q1 onward)',
             color='white', fontsize=16, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig('notebooks/dashboard_accuracy_chart.png', dpi=150,
            bbox_inches='tight', facecolor='#0d1117')
plt.close()
print('Chart 1 done.')

# ─── FIGURE 2: Metrics comparison bar chart ───────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.patch.set_facecolor('#0d1117')

metric_names  = ['RMSE', 'MSE', 'MAE']
metric_keys   = ['rmse_ens', 'mse_ens', 'mae_ens']
bar_colors    = ['#3b82f6', '#f59e0b', '#10b981', '#f97316']
country_names = [FLAGS[c] for c in COUNTRIES]

for j, (mname, mkey) in enumerate(zip(metric_names, metric_keys)):
    ax = axes[j]
    ax.set_facecolor('#161b22')
    vals = [results[c][mkey] for c in COUNTRIES]
    bars = ax.bar(country_names, vals, color=bar_colors, width=0.55, edgecolor='#30363d', linewidth=0.8)
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f'{val:.4f}', ha='center', va='bottom', color='white', fontsize=9, fontweight='bold')
    ax.set_title(mname + ' (Ensemble — Test Set)', color='white', fontsize=12, fontweight='bold')
    ax.set_ylabel(mname, color='#8b949e')
    ax.tick_params(colors='#8b949e', labelsize=9)
    for sp in ax.spines.values():
        sp.set_edgecolor('#30363d')
    ax.set_facecolor('#161b22')
    ax.grid(True, axis='y', color='#21262d', linewidth=0.8)

fig.suptitle('Model Error Metrics — All Countries (Lower = Better)',
             color='white', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('notebooks/dashboard_metrics_chart.png', dpi=150,
            bbox_inches='tight', facecolor='#0d1117')
plt.close()
print('Chart 2 done.')

# ─── FIGURE 3: Residual Error Distribution ───────────────────────────────────
fig, axes = plt.subplots(1, 4, figsize=(18, 5))
fig.patch.set_facecolor('#0d1117')

for i, c in enumerate(COUNTRIES):
    ax  = axes[i]
    r   = results[c]
    err = r['y_test'].values - r['ens_test']
    ax.set_facecolor('#161b22')
    ax.hist(err, bins=12, color=bar_colors[i], edgecolor='#30363d', alpha=0.85)
    ax.axvline(0, color='white', linewidth=1.5, linestyle='--', alpha=0.7)
    ax.axvline(err.mean(), color='#f59e0b', linewidth=1.5, linestyle='-', alpha=0.9, label=f'Mean err: {err.mean():.3f}')
    ax.set_title(FLAGS[c], color='white', fontsize=11, fontweight='bold')
    ax.set_xlabel('Residual (Actual - Predicted)', color='#8b949e', fontsize=9)
    ax.set_ylabel('Count', color='#8b949e', fontsize=9)
    ax.tick_params(colors='#8b949e', labelsize=8)
    for sp in ax.spines.values():
        sp.set_edgecolor('#30363d')
    ax.grid(True, color='#21262d', linewidth=0.8)
    ax.legend(fontsize=8, facecolor='#0d1117', edgecolor='#30363d', labelcolor='#c9d1d9')

fig.suptitle('Forecast Residual Distribution (Ensemble) — Centered near 0 = Unbiased',
             color='white', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('notebooks/dashboard_residuals_chart.png', dpi=150,
            bbox_inches='tight', facecolor='#0d1117')
plt.close()
print('Chart 3 done.')
print('\nAll charts saved to notebooks/')
