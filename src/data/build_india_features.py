import pandas as pd
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MASTER_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "india_master.csv")
OUT_PATH = os.path.join(PROJECT_ROOT, "data", "features", "india_features.csv")

def run():
    print("Building India features...")
    df = pd.read_csv(MASTER_PATH, index_col=0, parse_dates=True)
    
    # Target lags
    for i in range(1, 5):
        df[f'gdp_growth_lag{i}'] = df['gdp_growth'].shift(i)

    # Other lags
    other_vars = ['cpi_growth', 'wb_gdp_growth_pct', 'wb_cpi_inflation_pct', 
                  'wb_unemployment_pct', 'wb_trade_bal_gdp_pct', 'wb_gross_savings_pct']
    for var in other_vars:
        if var in df.columns:
            for i in range(1, 3):
                df[f'{var}_lag{i}'] = df[var].shift(i)

    # Rolling stats (must shift by 1 to prevent data leakage)
    df['gdp_growth_roll2_mean'] = df['gdp_growth'].shift(1).rolling(2).mean()
    df['gdp_growth_roll2_std']  = df['gdp_growth'].shift(1).rolling(2).std()
    df['gdp_growth_roll4_mean'] = df['gdp_growth'].shift(1).rolling(4).mean()
    df['gdp_growth_roll4_std']  = df['gdp_growth'].shift(1).rolling(4).std()

    # YoY approx (sum of last 4 QoQ log diffs)
    df['gdp_growth_yoy'] = df['gdp_growth'].rolling(4).sum()

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    df.to_csv(OUT_PATH)
    print(f"Saved {OUT_PATH} with {len(df.columns)} columns.")

if __name__ == "__main__":
    run()
