import os
import pickle
import numpy as np
import pandas as pd

def predict_next_hours(city, current_features_dict, horizon=1):
    """
    Expects context dictionary with primary sensor inputs
    (e.g., {'PM2.5': 45.0, 'PM10': 120.0, ..., 'AQI': 101.0, 'Hour': 14, 'Month': 6})
    """
    models_dir = '/content/nex-ai-hack/models'
    
    if horizon == 1:
        model_path = f"{models_dir}/{city.lower()}_model_1h.pkl"
        if not os.path.exists(model_path):
            raise ValueError(f"Model not trained for {city}")
        with open(model_path, 'rb') as f:
            pack = pickle.load(f)
        
        # Prepare input df from the single row
        df_in = pd.DataFrame([current_features_dict])
        # Compute cyclical features if not present
        if 'Hour_sin' not in df_in.columns:
            df_in['Hour_sin'] = np.sin(2 * np.pi * df_in['Hour'] / 23.0)
            df_in['Hour_cos'] = np.cos(2 * np.pi * df_in['Hour'] / 23.0)
            df_in['Month_sin'] = np.sin(2 * np.pi * (df_in['Month'] - 1) / 11.0)
            df_in['Month_cos'] = np.cos(2 * np.pi * (df_in['Month'] - 1) / 11.0)
            
        # Align features
        X = df_in[pack['features']]
        prediction = pack['model'].predict(X)[0]
        return max(float(prediction), 0.0)
    
    elif horizon <= 8:
        model_path = f"{models_dir}/{city.lower()}_model_8h.pkl"
        with open(model_path, 'rb') as f:
            pack = pickle.load(f)
        df_in = pd.DataFrame([current_features_dict])
        if 'Hour_sin' not in df_in.columns:
            df_in['Hour_sin'] = np.sin(2 * np.pi * df_in['Hour'] / 23.0)
            df_in['Hour_cos'] = np.cos(2 * np.pi * df_in['Hour'] / 23.0)
            df_in['Month_sin'] = np.sin(2 * np.pi * (df_in['Month'] - 1) / 11.0)
            df_in['Month_cos'] = np.cos(2 * np.pi * (df_in['Month'] - 1) / 11.0)
            
        X = df_in[pack['features']]
        predictions = pack['model'].predict(X)[0]
        return [max(float(val), 0.0) for val in predictions[:horizon]]
        
    else:
        raise ValueError("For predictions larger than 8 hours, use the long horizon calendar model.")
