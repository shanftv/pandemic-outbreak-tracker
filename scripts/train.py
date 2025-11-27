"""
model training moule
trains LightGBM models for COVID-19 case forecasting
"""

import pandas as pd
import numpy as np
import lightgbm as lgb
import joblib
import os
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def get_feature_columns(df):
    """get list of feature columns (excluding location, date, target)"""
    return [col for col in df.columns 
            if col.startswith(('lag_', 'roll_', 'day_', 'month', 'week_', 'days_'))]


def train_location_model(df_loc, location_name, test_days=14, validation_days=14, verbose=True):
    """
    train a LightGBM model for a single location
    
    args:
        df_loc: DataFrame with features for one location
        location_name: name of the location
        test_days: days to hold out for testing
        validation_days: days for validation
        verbose: print training progress
    
    returns:
        model, metrics dict, feature columns
    """
    feature_cols = get_feature_columns(df_loc)
    target_col = 'new_cases'
    
    df_loc = df_loc.sort_values('date').reset_index(drop=True)
    total_rows = len(df_loc)
    test_start = total_rows - test_days
    val_start = test_start - validation_days
    
    train = df_loc.iloc[:val_start]
    validation = df_loc.iloc[val_start:test_start]
    test = df_loc.iloc[test_start:]
    
    if verbose:
        print(f"\nTraining: {location_name}")
        print(f"  Train: {len(train)} | Valid: {len(validation)} | Test: {len(test)}")
    
    X_train, y_train = train[feature_cols], train[target_col]
    X_val, y_val = validation[feature_cols], validation[target_col]
    X_test, y_test = test[feature_cols], test[target_col]
    
    train_data = lgb.Dataset(X_train, label=y_train)
    val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
    
    params = {
        'objective': 'regression',
        'metric': 'mae',
        'boosting_type': 'gbdt',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.8,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'verbose': -1,
        'seed': 42
    }
    
    model = lgb.train(
        params,
        train_data,
        num_boost_round=1000,
        valid_sets=[train_data, val_data],
        valid_names=['train', 'valid'],
        callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=False)]
    )
    
    y_val_pred = model.predict(X_val)
    y_test_pred = model.predict(X_test)
    
    metrics = {
        'location': location_name,
        'val_mae': mean_absolute_error(y_val, y_val_pred),
        'val_rmse': np.sqrt(mean_squared_error(y_val, y_val_pred)),
        'test_mae': mean_absolute_error(y_test, y_test_pred),
        'test_rmse': np.sqrt(mean_squared_error(y_test, y_test_pred)),
        'test_r2': r2_score(y_test, y_test_pred),
        'n_estimators': model.num_trees()
    }
    
    if verbose:
        print(f"  Valid MAE: {metrics['val_mae']:.2f} | Test MAE: {metrics['test_mae']:.2f}")
    
    return model, metrics, feature_cols


def train_all_locations(features_path, models_dir, metrics_path, top_n=10):
    """
    train models for top N locations by total cases
    
    Args:
        features_path: Path to features CSV
        models_dir: Directory to save models
        metrics_path: Path to save metrics CSV
        top_n: Number of top locations to model
    
    Returns:
        dict of trained models and metrics DataFrame
    """
    print(f"Loading features from {features_path}...")
    df = pd.read_csv(features_path, parse_dates=['date'])
    
    top_locations = df.groupby('location')['new_cases'].sum().nlargest(top_n).index.tolist()
    print(f"\nTraining models for top {top_n} locations:")
    for i, loc in enumerate(top_locations, 1):
        total = df[df['location'] == loc]['new_cases'].sum()
        print(f"  {i}. {loc}: {total:,.0f} total cases")
    
    # create output directory
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(os.path.dirname(metrics_path), exist_ok=True)
    
    # train models
    models = {}
    all_metrics = []
    
    for location in top_locations:
        loc_data = df[df['location'] == location].copy()
        
        if len(loc_data) < 50:
            print(f"\nWarning: Skipping {location}: insufficient data")
            continue
        
        try:
            model, metrics, features = train_location_model(loc_data, location)
            
            # save model
            safe_name = location.replace(" ", "_").replace("/", "_")
            model_path = os.path.join(models_dir, f'lgb_{safe_name}.pkl')
            joblib.dump({
                'model': model,
                'features': features,
                'location': location,
                'trained_date': pd.Timestamp.now().isoformat()
            }, model_path)
            
            models[location] = {
                'model': model,
                'features': features,
                'path': model_path
            }
            
            all_metrics.append(metrics)
            
        except Exception as e:
            print(f"\n Error training {location}: {str(e)}")
    
    # save metrics
    metrics_df = pd.DataFrame(all_metrics)
    metrics_df.to_csv(metrics_path, index=False)
    
    print(f"\n Trained {len(models)} models")
    print(f"Models saved to: {models_dir}")
    print(f"Metrics saved to: {metrics_path}")
    
    return models, metrics_df


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python train.py <features_csv> <models_dir> <metrics_csv>")
        sys.exit(1)
    
    features_file = sys.argv[1]
    models_directory = sys.argv[2]
    metrics_file = sys.argv[3]
    
    train_all_locations(features_file, models_directory, metrics_file)