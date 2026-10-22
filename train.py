import os
import pickle
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
from sklearn.multioutput import MultiOutputRegressor

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

file_paths = [
    DATA_DIR / "bengaluru_hour_with_festivals_anomalies.csv",
    DATA_DIR / "chennai_hour_with_festivals_anomalies.csv",
    DATA_DIR / "delhi_hour_with_festivals_anomalies.csv",
    DATA_DIR / "kolkata_hour_with_festivals_anomalies.csv",
    DATA_DIR / "mumbai_hour_with_festivals_anomalies.csv",
]
file_paths = [p for p in file_paths if p.exists()]

primary_sensors = ['PM2.5', 'PM10', 'NO', 'NO2', 'NOx', 'CO', 'SO2', 'O3']
imputed_cities = {}
models_dir = str(MODELS_DIR)

print("--- Step 1: Processing, Imputing and Saving Clean Datasets ---")
for file in file_paths:
    df = pd.read_csv(file)
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    df = df.sort_values('Datetime').reset_index(drop=True)
    city_name = str(df['City'].dropna().unique()[0]).strip().title()
    
    if 'Festival_or_Anomaly' in df.columns:
        fest_df = df['Festival_or_Anomaly'].fillna('').str.get_dummies(sep='; ')
        fest_df = fest_df.add_prefix('Fest_')
        df = pd.concat([df, fest_df], axis=1)
        fest_cols = fest_df.columns.tolist()
    else:
        fest_cols = []

    df['PM2.5_lag_1'] = df['PM2.5'].shift(1)
    df['PM10_lag_1'] = df['PM10'].shift(1)
    df['AQI_lag_1'] = df['AQI'].shift(1)

    df_filtered = df.dropna(thresh=4, subset=primary_sensors).copy()
    cols_to_impute = primary_sensors + ['Benzene', 'Toluene', 'Xylene', 'AQI', 'PM2.5_lag_1', 'PM10_lag_1', 'AQI_lag_1'] + fest_cols
    cols_to_impute = [col for col in cols_to_impute if col in df_filtered.columns and df_filtered[col].notna().any()]

    imputer = IterativeImputer(max_iter=10, random_state=42)
    imputed_values = imputer.fit_transform(df_filtered[cols_to_impute])
    df_filtered[cols_to_impute] = pd.DataFrame(imputed_values, columns=cols_to_impute, index=df_filtered.index)
    imputed_cities[city_name] = df_filtered
    
    # Save clean datasets
    df_filtered.to_csv(DATA_DIR / f"{city_name.lower()}_clean.csv", index=False)

print("--- Step 2: Training 1H Model, 8H Model, and Long-Horizon Calendar Models ---")
for city, df in imputed_cities.items():
    # Feature Engineering
    df['Hour'] = df['Datetime'].dt.hour
    df['Month'] = df['Datetime'].dt.month
    df['Hour_sin'] = np.sin(2 * np.pi * df['Hour'] / 23.0)
    df['Hour_cos'] = np.cos(2 * np.pi * df['Hour'] / 23.0)
    df['Month_sin'] = np.sin(2 * np.pi * (df['Month'] - 1) / 11.0)
    df['Month_cos'] = np.cos(2 * np.pi * (df['Month'] - 1) / 11.0)
    
    # Target engineering (1H)
    df['Target_Next_Hour_AQI'] = df['AQI'].shift(-1)
    df_1h = df.dropna(subset=['Target_Next_Hour_AQI']).copy()
    exclude_cols = ['Datetime', 'City', 'Festival_or_Anomaly', 'Target_Next_Hour_AQI', 'Hour', 'Month']
    features_1h = [col for col in df_1h.columns if col not in exclude_cols and pd.api.types.is_numeric_dtype(df_1h[col])]
    
    split_idx = int(len(df_1h) * 0.8)
    model_1h = xgb.XGBRegressor(n_estimators=150, learning_rate=0.05, max_depth=6, random_state=42, objective='reg:squarederror')
    model_1h.fit(df_1h[features_1h].iloc[:split_idx], df_1h['Target_Next_Hour_AQI'].iloc[:split_idx])
    
    with open(MODELS_DIR / f"{city.lower()}_model_1h.pkl", "wb") as f:
        pickle.dump({"model": model_1h, "features": features_1h}, f)
        
    # Target engineering (8H MultiOutput)
    target_cols_8h = []
    df_8h = df.copy()
    for h in range(1, 9):
        col_name = f"Target_Next_{h}H_AQI"
        df_8h[col_name] = df_8h["AQI"].shift(-h)
        target_cols_8h.append(col_name)
    df_8h = df_8h.dropna(subset=target_cols_8h).copy()
    
    exclude_cols_8h = ["Datetime", "City", "Festival_or_Anomaly", "Hour", "Month"] + target_cols_8h
    features_8h = [col for col in df_8h.columns if col not in exclude_cols_8h and pd.api.types.is_numeric_dtype(df_8h[col])]
    
    split_8h = int(len(df_8h) * 0.8)
    base_model = xgb.XGBRegressor(n_estimators=100, learning_rate=0.05, max_depth=5, random_state=42, objective="reg:squarederror")
    model_8h = MultiOutputRegressor(base_model)
    model_8h.fit(df_8h[features_8h].iloc[:split_8h], df_8h[target_cols_8h].iloc[:split_8h])
    
    with open(MODELS_DIR / f"{city.lower()}_model_8h.pkl", "wb") as f:
        pickle.dump({"model": model_8h, "features": features_8h}, f)

    # Target engineering (Long Horizon Calendar-Only)
    df_lh = df.copy()
    day_of_year = df_lh["Datetime"].dt.dayofyear
    df_lh["Year_Sin"] = np.sin(2 * np.pi * day_of_year / 365.25)
    df_lh["Year_Cos"] = np.cos(2 * np.pi * day_of_year / 365.25)
    df_lh["Hour_Sin"] = np.sin(2 * np.pi * df_lh["Hour"] / 24.0)
    df_lh["Hour_Cos"] = np.cos(2 * np.pi * df_lh["Hour"] / 24.0)
    df_lh["DayOfWeek"] = df_lh["Datetime"].dt.dayofweek
    
    fest_cols_lh = [c for c in df_lh.columns if c.startswith("Fest_")]
    features_lh = ["Year_Sin", "Year_Cos", "Hour_Sin", "Hour_Cos", "DayOfWeek"] + fest_cols_lh
    
    split_lh = int(len(df_lh) * 0.8)
    model_lh = xgb.XGBRegressor(n_estimators=1000, learning_rate=0.1, max_depth=10, colsample_bytree=0.8, random_state=42, n_jobs=-1)
    model_lh.fit(df_lh[features_lh].iloc[:split_lh], df_lh["AQI"].iloc[:split_lh])
    
    with open(MODELS_DIR / f"{city.lower()}_model_lh.pkl", "wb") as f:
        pickle.dump({"model": model_lh, "features": features_lh}, f)

print(f"Training complete! All models stored in {MODELS_DIR}")
