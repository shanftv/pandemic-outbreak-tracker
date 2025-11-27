"""
prediction modules
generates 7-day forecasts using trained models.
"""

import pandas as pd
import numpy as np
import joblib
import json
import os
import glob
from datetime import timedelta


def iterative_forecast(last_row, model, feature_cols, horizon=7):
    """
    generate iterative multi-day forecast.
    
    args:
        last_row: last row of historical data with features
        model: trained LightGBM model
        feature_cols: list of feature column names
        horizon: number of days to forecast
    
    returns:
        list of prediction dicts
    """
    predictions = []
    current_row = last_row.copy()
    last_date = pd.to_datetime(current_row['date'])
    
    for day in range(1, horizon + 1):
        # prep feat
        X = current_row[feature_cols].values.reshape(1, -1)
        
        # predict (ensure non-negative)
        pred = max(0, model.predict(X)[0])
        pred_date = last_date + timedelta(days=day)
        
        predictions.append({
            'date': pred_date.strftime('%Y-%m-%d'),
            'predicted_cases': round(float(pred), 2),
            'day_ahead': day
        })
        
        # update features for next iteration
        # shift lags
        for lag in range(14, 1, -1):
            lag_col = f'lag_{lag}'
            if lag_col in current_row.index:
                current_row[lag_col] = current_row.get(f'lag_{lag-1}', 0)
        current_row['lag_1'] = pred
        
        # update rolling features (simplified)
        if 'roll_mean_7' in current_row.index:
            current_row['roll_mean_7'] = (current_row['roll_mean_7'] * 6 + pred) / 7
        if 'roll_mean_14' in current_row.index:
            current_row['roll_mean_14'] = (current_row['roll_mean_14'] * 13 + pred) / 14
        
        # update temporal features
        current_row['day_of_week'] = pred_date.dayofweek
        current_row['day_of_month'] = pred_date.day
        current_row['month'] = pred_date.month
        current_row['week_of_year'] = pred_date.isocalendar()[1]
        if 'days_since_start' in current_row.index:
            current_row['days_since_start'] += 1
    
    return predictions


def generate_all_predictions(models_dir, features_path, output_json, output_csv):
    """
    generate predictions for all trained models.
    
    args:
        models_dir: directory with trained model files
        features_path: path to features CSV
        output_json: path to save predictions JSON
        output_csv: path to save predictions CSV
    
    returns:
        dict of all predictions
    """
    print(f"Loading features from {features_path}...")
    df_features = pd.read_csv(features_path, parse_dates=['date'])
    
    print(f"Loading models from {models_dir}...")
    model_files = glob.glob(os.path.join(models_dir, 'lgb_*.pkl'))
    
    if not model_files:
        raise ValueError(f"No model files found in {models_dir}")
    
    print(f"Found {len(model_files)} models")
    
    all_predictions = {}
    predictions_flat = []
    
    for model_path in model_files:
        model_data = joblib.load(model_path)
        model = model_data['model']
        feature_cols = model_data['features']
        location = model_data['location']
        
        print(f"\nGenerating forecast for: {location}")
        
        # get latest data for this location
        loc_data = df_features[df_features['location'] == location].sort_values('date')
        
        if len(loc_data) == 0:
            print(f"  Warning: No data found for {location}")
            continue
        
        last_row = loc_data.iloc[-1]
        
        # generate forecast
        predictions = iterative_forecast(last_row, model, feature_cols, horizon=7)
        all_predictions[location] = predictions
        
        for p in predictions:
            predictions_flat.append({
                'location': location,
                **p
            })
        
        total_pred = sum(p['predicted_cases'] for p in predictions)
        last_7_actual = loc_data.tail(7)['new_cases'].sum()
        print(f"  Last 7 days: {last_7_actual:.0f} cases")
        print(f"  Next 7 days: {total_pred:.0f} cases")
    
    print(f"\nSaving predictions to {output_json}...")
    with open(output_json, 'w') as f:
        json.dump(all_predictions, f, indent=2)
    
    print(f"Saving predictions to {output_csv}...")
    predictions_df = pd.DataFrame(predictions_flat)
    predictions_df.to_csv(output_csv, index=False)
    
    print(f"\nGenerated predictions for {len(all_predictions)} locations")
    
    return all_predictions


def sanity_check_predictions(predictions):
    """
    run sanity checks on predictions.
    
    args:
        predictions: dict of predictions
    
    returns:
        bool: True if all checks pass
    """
    print("\nRunning sanity checks...")
    
    issues = []
    
    for location, preds in predictions.items():
        for p in preds:
            if p['predicted_cases'] < 0:
                issues.append(f"{location}: Negative prediction on {p['date']}")
            
            if np.isnan(p['predicted_cases']):
                issues.append(f"{location}: NaN prediction on {p['date']}")
    
    if issues:
        print("Sanity check FAILED:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("All sanity checks passed")
        return True


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 5:
        print("Usage: python predict.py <models_dir> <features_csv> <output_json> <output_csv>")
        sys.exit(1)
    
    models_directory = sys.argv[1]
    features_file = sys.argv[2]
    output_json_file = sys.argv[3]
    output_csv_file = sys.argv[4]
    
    predictions = generate_all_predictions(
        models_directory,
        features_file,
        output_json_file,
        output_csv_file
    )
    
    if not sanity_check_predictions(predictions):
        print("\nWARNING: Predictions failed sanity checks!")
        sys.exit(1)
