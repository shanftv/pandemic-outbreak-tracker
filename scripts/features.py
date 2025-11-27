"""
feature engr. module
creates lag features and rolling statistics for time series forecasting
"""

try:
    import pandas as pd
except Exception as e:
    raise ImportError("pandas is required to run this script; install it with 'pip install pandas'") from e

try:
    import numpy as np
except Exception as e:
    raise ImportError("numpy is required to run this script; install it with 'pip install numpy'") from e


def make_features(df_loc, target='new_cases', n_lags=14):
    """
    create features for time series forecasting
    
    args:
        df_loc: DataFrame for a single location
        target: Name of target column
        n_lags: Number of lag features to create
    
    returns:
        DataFrame with engineered features
    """
    df = df_loc.sort_values('date').copy()
    
    # lag features
    for lag in range(1, n_lags + 1):
        df[f'lag_{lag}'] = df[target].shift(lag)
    
    # rolling statistics (shifted to avoid leakage)
    df['roll_mean_7'] = df[target].shift(1).rolling(window=7, min_periods=1).mean()
    df['roll_mean_14'] = df[target].shift(1).rolling(window=14, min_periods=1).mean()
    df['roll_std_7'] = df[target].shift(1).rolling(window=7, min_periods=1).std().fillna(0)
    df['roll_max_7'] = df[target].shift(1).rolling(window=7, min_periods=1).max()
    df['roll_min_7'] = df[target].shift(1).rolling(window=7, min_periods=1).min()
    
    # temporal features
    df['day_of_week'] = df['date'].dt.dayofweek
    df['day_of_month'] = df['date'].dt.day
    df['month'] = df['date'].dt.month
    df['week_of_year'] = df['date'].dt.isocalendar().week.astype(int)
    
    # trend
    df['days_since_start'] = (df['date'] - df['date'].min()).dt.days
    
    return df


def feature_pipeline(input_path, output_path, min_lag=14):
    """
    full feature engineering pipeline
    
    args:
        input_path: Path to cleaned data
        output_path: Path to save features
        min_lag: Minimum lag features required (removes first N rows)
    
    returns:
        DataFrame with features
    """
    print(f"Loading cleaned data from {input_path}...")
    df = pd.read_csv(input_path, parse_dates=['date'])
    
    print("Creating features for all locations...")
    all_features = []
    
    for loc in df['location'].unique():
        loc_data = df[df['location'] == loc].copy()
        loc_features = make_features(loc_data)
        all_features.append(loc_features)
    
    df_features = pd.concat(all_features, ignore_index=True)
    
    # remove rows with missing critical lags
    print(f"Removing rows with missing lag features...")
    df_features = df_features.dropna(subset=[f'lag_{lag}' for lag in range(1, min_lag + 1)])
    
    print(f"Saving features to {output_path}...")
    df_features.to_csv(output_path, index=False)
    
    feature_cols = [col for col in df_features.columns if col not in ['location', 'date', 'new_cases']]
    print(f"Created {len(feature_cols)} features for {len(df_features)} records")
    
    return df_features


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python features.py <input_csv> <output_csv>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    feature_pipeline(input_file, output_file)
