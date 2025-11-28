# predictions

## what it does

takes trained models and generates 7-day forecasts. uses an iterative strategy where each day's prediction feeds into the next day, so day 2 uses day 1's prediction, day 3 uses day 2, etc.

**file:** `scripts/predict.py`

---

## main function

### `iterative_forecast(last_row, model, feature_cols, horizon=7)`

generates a multi-day forecast using the iterative approach.

**what it needs:**
- `last_row` - last row of historical data with all features
- `model` - trained lightgbm model
- `feature_cols` - list of feature column names
- `horizon` - how many days to forecast (default: 7)

**gives back:**
- list of prediction dictionaries like:
  ```python
  [
    {'date': '2024-02-01', 'predicted_cases': 523.45, 'day_ahead': 1},
    {'date': '2024-02-02', 'predicted_cases': 487.12, 'day_ahead': 2},
    ...
  ]
  ```

**example:**
```python
from scripts.predict import iterative_forecast
import pandas as pd
import joblib

# load model
model = joblib.load('models/Metro Manila_model.pkl')
last_row = df[df['location'] == 'Metro Manila'].iloc[-1]

# forecast 7 days
forecast = iterative_forecast(last_row, model, feature_cols, horizon=7)

for pred in forecast:
    print(f"{pred['date']}: {pred['predicted_cases']} cases")
```

---

## how iterative forecasting works

predicts one day at a time. each day's prediction becomes a feature for the next day.

**day 1:** use actual historical data
```
features: [lag_1, lag_2, ..., lag_14, roll_mean_7, day_of_week, ...]
         (all real historical data)
         ↓
         model → day 1 prediction (523 cases)
```

**day 2:** use day 1 prediction
```
features: [day1_pred, lag_1, lag_2, ..., lag_13, roll_mean_7, ...]
         (lag_1 now = day 1 prediction, others shifted)
         ↓
         model → day 2 prediction (487 cases)
```

**day 3+:** keep going

---

## updating features as we go

lag features shift forward:

```python
# shift all lags
for lag in range(14, 1, -1):
    current_row[f'lag_{lag}'] = current_row[f'lag_{lag-1}']

# most recent = the prediction we just made
current_row['lag_1'] = prediction
```

rolling stats recalculated:
```python
# update with new prediction
roll_mean_7 = np.mean(recent_predictions[-7:])
roll_std_7 = np.std(recent_predictions[-7:])
```

---

## no negative cases

if the model predicts something negative (which happens), we set it to 0:

```python
pred = max(0, model.predict(X)[0])
```

makes sense - can't have negative cases.

---

## generate all predictions

### `generate_all_predictions(models_dir, features_df, output_json, top_n=10)`

makes 7-day forecasts for all locations.

**what it needs:**
- `models_dir` - where your model files are
- `features_df` - latest features for all locations
- `output_json` - where to save the results
- `top_n` - how many locations (default: 10)

**output:**
```json
{
  "generated_at": "2024-01-31T15:30:00Z",
  "predictions": {
    "Metro Manila": [
      {
        "date": "2024-02-01",
        "predicted_cases": 523.45,
        "day_ahead": 1
      },
      ...
    ],
    "Laguna": [...]
  }
}
```

---

## prediction pipeline

```python
def generate_all_predictions(models_dir, features_df, output_json, top_n=10):
    """make predictions for top N locations"""
    predictions = {}
    
    model_files = glob.glob(os.path.join(models_dir, '*_model.pkl'))
    
    for model_file in model_files[:top_n]:
        location = os.path.basename(model_file).replace('_model.pkl', '')
        
        # load model
        model = joblib.load(model_file)
        
        # get latest data
        df_loc = features_df[features_df['location'] == location]
        last_row = df_loc.iloc[-1]
        
        # get features
        feature_cols = get_feature_columns(df_loc)
        
        # forecast
        forecast = iterative_forecast(last_row, model, feature_cols, horizon=7)
        predictions[location] = forecast
    
    # save
    output = {
        'generated_at': datetime.now(UTC).isoformat(),
        'predictions': predictions
    }
    
    with open(output_json, 'w') as f:
        json.dump(output, f, indent=2)
```

---

## sanity checks

### `sanity_check_predictions(predictions_json)`

makes sure the predictions look good before we use them.

**checks:**
1. no NaN or weird infinite numbers
2. all values are zero or positive
3. all 7 days present
4. no crazy jumps between days
5. all locations have predictions

**example:**
```python
from scripts.predict import sanity_check_predictions

is_valid, errors = sanity_check_predictions('predictions_7d.json')
if not is_valid:
    print(f"problems: {errors}")
```

---

## in the full pipeline

used in `full_pipeline.py` like:

```python
def run_full_pipeline(skip_download=False, top_n=10):
    # ... cleaning and training ...
    
    # make predictions
    logger.info("making 7-day forecasts...")
    predictions_file = os.path.join(base_dir, 'predictions_7d.json')
    df_features = pd.read_csv(os.path.join(base_dir, 'data', 'features_ph_covid.csv'))
    
    generate_all_predictions(
        models_dir=models_dir,
        features_df=df_features,
        output_json=predictions_file,
        top_n=top_n
    )
    
    # check it
    is_valid, errors = sanity_check_predictions(predictions_file)
    if is_valid:
        logger.info(f"✓ predictions saved")
    else:
        logger.error(f"prediction check failed: {errors}")
```

---

## why 7 days

- **useful timeframe** - people can actually do something about it
- **accuracy drops after** - the further out you go, the worse predictions get
- **updates weekly** - fresh data keeps things relevant
- **fast enough** - doesn't take forever to compute

---

## notes

- each location forecast is separate (no mixing between regions)
- feature engineering during prediction keeps everything honest
- predictions used to calculate danger zones for the map
- errors get bigger for days 5, 6, 7 (day 1 is most accurate)
