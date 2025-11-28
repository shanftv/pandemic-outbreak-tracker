# model training

## what it does

trains individual models for each location. each place gets its own lightgbm model because different regions have different epidemic patterns. we use regression to predict actual case counts.

**file:** `scripts/train.py`

---

## model setup

- **algorithm:** LightGBM (Light Gradient Boosting Machine)
- **task:** regression (predicting actual numbers, not categories)
- **scope:** one model per location
- **target:** `new_cases` (daily case count)

---

## main functions

### `get_feature_columns(df)`

pulls out the feature column names from the engineered data.

**what it needs:**
- `df` - dataset with engineered features

**gives back:**
- list of feature columns (stuff starting with lag_, roll_, day_, month, week_, days_)

**example:**
```python
features = get_feature_columns(df)
# Returns: ['lag_1', 'lag_2', ..., 'roll_mean_7', 'day_of_week', ...]
```

---

### `train_location_model(df_loc, location_name, test_days=14, validation_days=14, verbose=True)`

trains a lightgbm model for one location. does train/validation/test split properly.

**what it needs:**
- `df_loc` - features for one location, sorted by date
- `location_name` - name of the location (for logging)
- `test_days` - how many days to save for testing (default: 14)
- `validation_days` - how many for tuning (default: 14)
- `verbose` - print stuff while training (default: True)

**gives back:**
- tuple: `(model, metrics_dict, feature_columns)`
  - `model` - trained lightgbm model you can use for predictions
  - `metrics_dict` - how good it is (MAE, RMSE, R², etc.)
  - `feature_columns` - which features it uses

---

## how data is split

for a location with N days of data:

```
[Train: 0 to (N-28)] | [Validation: (N-28) to (N-14)] | [Test: (N-14) to N]
     ↓                        ↓                               ↓
  train the model      tune hyperparameters           check if it's good
```

**the split:**
- **training:** first (N - 28) rows
- **validation:** next 14 rows
- **test:** last 14 rows

this makes sure we're not cheating by using future data during training.

---

## training example

```python
from scripts.train import train_location_model

# load your data
df_location = df[df['location'] == 'Metro Manila'].sort_values('date')

# train it
model, metrics, features = train_location_model(
    df_location, 
    location_name='Metro Manila',
    test_days=14,
    validation_days=14
)

# check the results
print(f"MAE: {metrics['mae']}")
print(f"RMSE: {metrics['rmse']}")
print(f"R²: {metrics['r2']}")
```

---

## how good are the predictions

each model gets graded on the test set:

| metric | formula | what it means |
|--------|---------|---------------|
| **MAE** | average of absolute errors | wrong by this many cases on average |
| **RMSE** | penalizes bigger errors more | like MAE but emphasizes bad predictions |
| **R²** | explains this % of variance | 0.8 = 80% of the ups and downs are explained |
| **MAPE** | percentage error | wrong by this percentage |

---

## lightgbm settings

the default configuration:

```python
{
    'num_leaves': 31,
    'max_depth': -1,
    'learning_rate': 0.05,
    'n_estimators': 300,
    'objective': 'regression',
    'metric': 'mae',
    'verbose': -1
}
```

**tuning:** validation set performance is watched for early stopping.

---

## where models get saved

trained models saved with joblib:

```python
joblib.dump(model, f'models/{location_name}_model.pkl')
```

file naming: `{location}_model.pkl`

example: `models/Metro Manila_model.pkl`

---

## training many locations

the full pipeline trains top N locations:

```python
def train_all_locations(features_csv, top_n=10):
    """train models for top N locations by cases"""
    df = pd.read_csv(features_csv, parse_dates=['date'])
    
    # get top locations by total cases
    location_cases = df.groupby('location')['new_cases'].sum().sort_values(ascending=False)
    top_locations = location_cases.head(top_n).index
    
    models = {}
    metrics_all = []
    
    for location in top_locations:
        df_loc = df[df['location'] == location].sort_values('date')
        model, metrics, features = train_location_model(
            df_loc, 
            location_name=location,
            verbose=True
        )
        
        models[location] = {
            'model': model,
            'features': features,
            'metrics': metrics
        }
        
        metrics_all.append({**metrics, 'location': location})
    
    return models, metrics_all
```

---

## why top N locations

chosen by:
1. total cases (highest first)
2. consistent data (need 60+ days)
3. enough cases to make good predictions (avoid noise)

---

## what the output looks like

console will show something like:

```
Training: Metro Manila
  Train: 85 | Valid: 14 | Test: 14
  MAE: 234.56 | RMSE: 412.34 | R²: 0.782

Training: Laguna
  Train: 72 | Valid: 14 | Test: 14
  MAE: 145.23 | RMSE: 287.65 | R²: 0.821
```

---

## notes

- each location gets its own model so it can learn regional patterns
- lightgbm (ensemble approach) is less likely to overfit
- validation set prevents us from tuning too hard
- each model saved separately so you can use them independently
|--------|---------|-----------------|
| **MAE** | $\frac{1}{n}\sum\|\hat{y}_i - y_i\|$ | Average absolute error (same units as target) |
| **RMSE** | $\sqrt{\frac{1}{n}\sum(\hat{y}_i - y_i)^2}$ | Penalizes larger errors more than MAE |
| **R²** | $1 - \frac{SS_{res}}{SS_{tot}}$ | Proportion of variance explained (0-1) |
| **MAPE** | $\frac{100}{n}\sum\|\frac{y_i - \hat{y}_i}{y_i}\|$ | Percentage error |

---

## Hyperparameters

Default LightGBM configuration:

```python
{
    'num_leaves': 31,
    'max_depth': -1,
    'learning_rate': 0.05,
    'n_estimators': 300,
    'objective': 'regression',
    'metric': 'mae',
    'verbose': -1
}
```

**Tuning:** Validation set performance is monitored for early stopping.

---

## Model Storage

Trained models are saved using joblib:

```python
joblib.dump(model, f'models/{location_name}_model.pkl')
```

File naming convention: `{location}_model.pkl`

Example: `models/Metro Manila_model.pkl`

---

## Training Loop

The full pipeline trains models for top N locations:

```python
def train_all_locations(features_csv, top_n=10):
    """Train models for top N locations by case volume."""
    df = pd.read_csv(features_csv, parse_dates=['date'])
    
    # Get top locations by total cases
    location_cases = df.groupby('location')['new_cases'].sum().sort_values(ascending=False)
    top_locations = location_cases.head(top_n).index
    
    models = {}
    metrics_all = []
    
    for location in top_locations:
        df_loc = df[df['location'] == location].sort_values('date')
        model, metrics, features = train_location_model(
            df_loc, 
            location_name=location,
            verbose=True
        )
        
        models[location] = {
            'model': model,
            'features': features,
            'metrics': metrics
        }
        
        metrics_all.append({**metrics, 'location': location})
    
    return models, metrics_all
```

---

## Model Selection Criteria

**Top N Locations** are selected by:
1. Total cumulative cases (descending)
2. Consistency of data (minimum 60+ days of history)
3. Sufficient case volume (avoid noise in small counts)

---

## Training Output

**Console Output Example:**

```
Training: Metro Manila
  Train: 85 | Valid: 14 | Test: 14
  MAE: 234.56 | RMSE: 412.34 | R²: 0.782

Training: Laguna
  Train: 72 | Valid: 14 | Test: 14
  MAE: 145.23 | RMSE: 287.65 | R²: 0.821
```

---

## Notes

- Models are location-specific to capture regional epidemic dynamics
- Ensemble approach (LightGBM) reduces overfitting risk
- Validation set prevents hyperparameter tuning bias
- Models saved independently for flexible serving
