# feature engineering

## what it does

this is where we create all the features that the model actually uses. we take cleaned data and make it predictable by building lag features (previous days), rolling averages, time patterns, etc. basically turning raw numbers into things the model can learn from.

**file:** `scripts/features.py`

---

## main function

### `make_features(df_loc, target='new_cases', n_lags=14)`

takes time series data for one location and creates all the features we need for prediction.

**what it needs:**
- `df_loc` - time series data, sorted by date
- `target` - column you're predicting (default: 'new_cases')
- `n_lags` - how many past days to look at (default: 14)

**gives back:**
- same DataFrame but with tons of new columns
- total: 14 lag + 5 rolling + 5 temporal + 1 trend = 25 features

---

## what features we create

### lag features (14 of them)

basically just previous day values. like lag_1 is yesterday's cases, lag_2 is two days ago, etc.

```python
lag_1, lag_2, ..., lag_14
```

**why:** yesterday's cases are a good predictor of today
**idea:** recent data tells you more than old data

---

### rolling stats (5 features)

averages and spreads over short windows. all shifted so we don't cheat using today's data.

| feature | window | what it is |
|---------|--------|-----------|
| `roll_mean_7` | 7 days | average of last 7 days |
| `roll_mean_14` | 14 days | average of last 14 days |
| `roll_std_7` | 7 days | how much it bounces around |
| `roll_max_7` | 7 days | peak in last 7 days |
| `roll_min_7` | 7 days | lowest point in 7 days |

**why:** shows trend and volatility
**no cheating:** uses `.shift(1)` so today's data isn't included

---

### temporal features (5 features)

time of day/week/year stuff. captures patterns like "weekends have fewer cases" or seasonal patterns.

| feature | range | what it is |
|---------|-------|-----------|
| `day_of_week` | 0-6 | 0 = Monday, 6 = Sunday |
| `day_of_month` | 1-31 | which day of month |
| `month` | 1-12 | which month |
| `week_of_year` | 1-52 | week number |
| `days_since_start` | 0+ | how many days since beginning |

**why:** some days/weeks/months have patterns

---

## how to use it

```python
from scripts.features import make_features
import pandas as pd

# load clean data
df = pd.read_csv('data/cleaned_ph_covid.csv')

# process each location
features_list = []
for location, group in df.groupby('location'):
    featured_df = make_features(group, target='new_cases', n_lags=14)
    features_list.append(featured_df)

# combine and save
final_features = pd.concat(features_list, ignore_index=True)
final_features.to_csv('data/features_ph_covid.csv', index=False)
```

---

## no data cheating!

rolling stats use shift(1) on purpose:

```python
df['roll_mean_7'] = df[target].shift(1).rolling(window=7).mean()
```

this makes sure the model never sees today's data when making a prediction. keeps everything honest.

---

## which features matter most

when lightgbm trains, it tells us which features are most important:
1. **lag features** - about 40-50% importance (the heavy hitters)
2. **rolling stats** - about 25-30% importance  
3. **temporal features** - about 15-20% importance
4. **trend** - about 5-10% importance

---

## missing data

- first few rows will have NaN (because you need past data for lags)
- these rows get skipped during training
- need at least: `n_lags + 7` rows (21 rows minimum for default settings)

---

## example output

looks something like this after engineering:

```
date       location      new_cases  lag_1  lag_2  ...  roll_mean_7  day_of_week  month
2020-01-30 Metro Manila      3      NaN    NaN         NaN           3          1
2020-01-31 Metro Manila      5      3.0    NaN         NaN           4          1
...
2020-02-10 Metro Manila     12     11.0   10.0         8.5           0          2
```

---

## integration

in the full pipeline it's used like:

```python
def feature_pipeline(input_csv, output_csv='data/features_ph_covid.csv'):
    """run the feature engineering"""
    df = pd.read_csv(input_csv, parse_dates=['date'])
    
    features_list = []
    for location, group in df.groupby('location'):
        featured = make_features(group)
        features_list.append(featured)
    
    result = pd.concat(features_list, ignore_index=True)
    result.to_csv(output_csv, index=False)
```
