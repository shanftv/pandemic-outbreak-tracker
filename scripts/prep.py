"""
data preprocessing modile
handles cleaning and standardization of COVID-19 case data
"""

import pandas as pd
import numpy as np
from datetime import datetime


def standardize_and_fill(df, date_col='date', loc_col='location', target_col='new_cases'):
    """
    standardize column names and fill missing dates for continuous time series
    
    args:
        df: DataFrame with case data
        date_col: name of date column
        loc_col: name of location column
        target_col: name of target variable (new cases)
    
    returns:
        DataFrame with continuous daily frequency per location
    """
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    
    # keep only needed columns
    cols = [date_col, loc_col, target_col]
    df = df[cols].copy()
    
    # process each location
    out = []
    for loc, group in df.groupby(loc_col):
        # create continuous date range
        date_range = pd.date_range(
            start=group[date_col].min(),
            end=group[date_col].max(),
            freq='D'
        )

        group_indexed = group.set_index(date_col)
        group_filled = group_indexed.reindex(date_range, fill_value=0)
        
        group_filled = group_filled.reset_index()
        group_filled.columns = [date_col, target_col]
        group_filled[loc_col] = loc
        
        out.append(group_filled)
    
    result = pd.concat(out, ignore_index=True)
    return result[[loc_col, date_col, target_col]].sort_values([loc_col, date_col]).reset_index(drop=True)


def aggregate_case_information(df_cases, date_col='date_announced', loc_col='province'):
    """
    aggregate individual case records into daily counts per location
    
    args:
        df_cases: DataFrame with individual case records
        date_col: column name for confirmation date
        loc_col: column name for location
    
    returns:
        DataFrame with daily aggregated cases
    """
    # Convert date
    df_cases[date_col] = pd.to_datetime(df_cases[date_col], errors='coerce')
    
    # Remove invalid records
    df_clean = df_cases.dropna(subset=[date_col, loc_col]).copy()
    
    # Aggregate
    daily = df_clean.groupby([loc_col, date_col]).size().reset_index(name='new_cases')
    daily.columns = ['location', 'date', 'new_cases']
    
    return daily.sort_values(['location', 'date']).reset_index(drop=True)


def clean_pipeline(input_path, output_path):
    """
    full cleaning pipeline from raw case data to cleaned time series
    
    args:
        input_path: path to raw Case_Information.csv
        output_path: path to save cleaned data
    
    returns:
        cleaned DataFrame
    """
    print(f"Loading data from {input_path}...")
    df = pd.read_csv(input_path)
    
    print(f"Aggregating daily cases...")
    df_daily = aggregate_case_information(df)
    
    print(f"Filling missing dates...")
    df_clean = standardize_and_fill(df_daily)
    
    print(f"Saving to {output_path}...")
    df_clean.to_csv(output_path, index=False)
    
    print(f"Cleaned {len(df_clean)} records for {df_clean['location'].nunique()} locations")
    print(f"Date range: {df_clean['date'].min()} to {df_clean['date'].max()}")
    
    return df_clean


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python prep.py <input_csv> <output_csv>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    clean_pipeline(input_file, output_file)