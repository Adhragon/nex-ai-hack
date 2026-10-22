import os
import pickle
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error

cities = ['bengaluru', 'chennai', 'delhi', 'kolkata', 'mumbai']
models_dir = '/content/nex-ai-hack/models'

print("--- Running Model Validation Suite ---")
for city in cities:
    clean_file = f'/content/nex-ai-hack/data/{city}_clean.csv'
    if not os.path.exists(clean_file):
        print(f"Clean file for {city} not found. Please run train.py first.")
        continue
        
    df = pd.read_csv(clean_file)
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    df['Hour'] = df['Datetime'].dt.hour
    df['Month'] = df['Datetime'].dt.month
    df['Hour_sin'] = np.sin(2 * np.pi * df['Hour'] / 23.0)
    df['Hour_cos'] = np.cos(2 * np.pi * df['Hour'] / 23.0)
    df['Month_sin'] = np.sin(2 * np.pi * (df['Month'] - 1) / 11.0)
    df['Month_cos'] = np.cos(2 * np.pi * (df['Month'] - 1) / 11.0)

    # Evaluate 1-Hour Model
    with open(f'{models_dir}/{city}_model_1h.pkl', 'rb') as f:
        pack_1h = pickle.load(f)
    df['Target_Next_Hour_AQI'] = df['AQI'].shift(-1)
    df_1h = df.dropna(subset=['Target_Next_Hour_AQI'])
    split_1h = int(len(df_1h) * 0.8)
    X_test_1h, y_test_1h = df_1h[pack_1h['features']].iloc[split_1h:], df_1h['Target_Next_Hour_AQI'].iloc[split_1h:]
    preds_1h = np.maximum(pack_1h['model'].predict(X_test_1h), 0)
    mae_1h = mean_absolute_error(y_test_1h, preds_1h)
    print(f"[{city.upper()}] 1-Hour Test MAE: {mae_1h:.2f}")

    # Evaluate Long-Horizon Model
    with open(f'{models_dir}/{city}_model_lh.pkl', 'rb') as f:
        pack_lh = pickle.load(f)
    day_of_year = df['Datetime'].dt.dayofyear
    df['Year_Sin'] = np.sin(2 * np.pi * day_of_year / 365.25)
    df['Year_Cos'] = np.cos(2 * np.pi * day_of_year / 365.25)
    df['Hour_Sin'] = np.sin(2 * np.pi * df['Hour'] / 24.0)
    df['Hour_Cos'] = np.cos(2 * np.pi * df['Hour'] / 24.0)
    df['DayOfWeek'] = df['Datetime'].dt.dayofweek
    
    split_lh = int(len(df) * 0.8)
    X_test_lh, y_test_lh = df[pack_lh['features']].iloc[split_lh:], df['AQI'].iloc[split_lh:]
    preds_lh = np.maximum(pack_lh['model'].predict(X_test_lh), 0)
    mae_lh = mean_absolute_error(y_test_lh, preds_lh)
    print(f"[{city.upper()}] Long-Horizon (Calendar) Test MAE: {mae_lh:.2f}")
