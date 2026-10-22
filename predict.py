import os
import pickle
from pathlib import Path
from datetime import datetime, date
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data"


def get_model_path(city: str, model_type: str = "lh") -> Path:
    return MODELS_DIR / f"{city.lower()}_model_{model_type}.pkl"


def has_model(city: str, model_type: str = "lh") -> bool:
    return get_model_path(city, model_type).exists()


def predict_school_hours(city: str, target_date: str | date | datetime) -> pd.DataFrame:
    """
    Predicts hourly AQI for school hours (06:00 to 18:00) on a target date
    using the Long-Horizon Calendar Model (trained on seasonal, weekly, and hourly cycles).
    
    Returns a DataFrame containing ['Datetime', 'AQI', 'City', 'Source'] matching
    the schema expected by planner.py.
    """
    model_path = get_model_path(city, "lh")
    if not model_path.exists():
        raise FileNotFoundError(
            f"Forecast model not found for '{city}' at {model_path}. "
            f"Please run 'python train.py' to generate the model artifacts."
        )

    with open(model_path, "rb") as f:
        pack = pickle.load(f)

    if isinstance(target_date, str):
        dt = pd.to_datetime(target_date)
    elif isinstance(target_date, datetime):
        dt = pd.to_datetime(target_date)
    else:
        dt = pd.to_datetime(str(target_date))

    day_of_year = dt.dayofyear
    day_of_week = dt.dayofweek

    year_sin = np.sin(2 * np.pi * day_of_year / 365.25)
    year_cos = np.cos(2 * np.pi * day_of_year / 365.25)

    rows = []
    # School planning hours are 6 AM to 6 PM (hours 6 through 17)
    for hour in range(6, 18):
        hour_sin = np.sin(2 * np.pi * hour / 24.0)
        hour_cos = np.cos(2 * np.pi * hour / 24.0)

        feat_map = {
            "Year_Sin": year_sin,
            "Year_Cos": year_cos,
            "Hour_Sin": hour_sin,
            "Hour_Cos": hour_cos,
            "DayOfWeek": day_of_week,
        }

        # Any missing feature (such as festival dummy columns) defaults to 0.0
        for feature_name in pack["features"]:
            if feature_name not in feat_map:
                feat_map[feature_name] = 0.0

        rows.append({
            "Datetime": pd.Timestamp(year=dt.year, month=dt.month, day=dt.day, hour=hour),
            "features": feat_map,
        })

    features_df = pd.DataFrame([r["features"] for r in rows])[pack["features"]]
    raw_preds = pack["model"].predict(features_df)
    clamped_preds = [max(round(float(val), 1), 0.0) for val in raw_preds]

    predicted_df = pd.DataFrame({
        "Datetime": [r["Datetime"] for r in rows],
        "AQI": clamped_preds,
        "City": city.title(),
        "Source": "Forecast",
    })

    return predicted_df


def predict_next_hours(city: str, current_features_dict: dict, horizon: int = 1):
    """
    Expects context dictionary with primary sensor inputs
    (e.g., {'PM2.5': 45.0, 'PM10': 120.0, ..., 'AQI': 101.0, 'Hour': 14, 'Month': 6})
    Predicts short-term AQI for horizon (1 or up to 8 hours).
    """
    if horizon == 1:
        model_path = get_model_path(city, "1h")
        if not model_path.exists():
            raise FileNotFoundError(f"1-hour model not found for {city} at {model_path}")
        with open(model_path, "rb") as f:
            pack = pickle.load(f)

        df_in = pd.DataFrame([current_features_dict])
        if "Hour_sin" not in df_in.columns and "Hour" in df_in.columns:
            df_in["Hour_sin"] = np.sin(2 * np.pi * df_in["Hour"] / 23.0)
            df_in["Hour_cos"] = np.cos(2 * np.pi * df_in["Hour"] / 23.0)
        if "Month_sin" not in df_in.columns and "Month" in df_in.columns:
            df_in["Month_sin"] = np.sin(2 * np.pi * (df_in["Month"] - 1) / 11.0)
            df_in["Month_cos"] = np.cos(2 * np.pi * (df_in["Month"] - 1) / 11.0)

        for col in pack["features"]:
            if col not in df_in.columns:
                df_in[col] = 0.0

        X = df_in[pack["features"]]
        prediction = pack["model"].predict(X)[0]
        return max(float(prediction), 0.0)

    elif horizon <= 8:
        model_path = get_model_path(city, "8h")
        if not model_path.exists():
            raise FileNotFoundError(f"8-hour model not found for {city} at {model_path}")
        with open(model_path, "rb") as f:
            pack = pickle.load(f)

        df_in = pd.DataFrame([current_features_dict])
        if "Hour_sin" not in df_in.columns and "Hour" in df_in.columns:
            df_in["Hour_sin"] = np.sin(2 * np.pi * df_in["Hour"] / 23.0)
            df_in["Hour_cos"] = np.cos(2 * np.pi * df_in["Hour"] / 23.0)
        if "Month_sin" not in df_in.columns and "Month" in df_in.columns:
            df_in["Month_sin"] = np.sin(2 * np.pi * (df_in["Month"] - 1) / 11.0)
            df_in["Month_cos"] = np.cos(2 * np.pi * (df_in["Month"] - 1) / 11.0)

        for col in pack["features"]:
            if col not in df_in.columns:
                df_in[col] = 0.0

        X = df_in[pack["features"]]
        predictions = pack["model"].predict(X)[0]
        return [max(float(val), 0.0) for val in predictions[:horizon]]

    else:
        raise ValueError("For predictions larger than 8 hours, use predict_school_hours or the long-horizon calendar model.")
