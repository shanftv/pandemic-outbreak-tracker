# metrics and analysis

## what it does

tracks how good our models are doing. measures prediction accuracy, classifies danger zones, and keeps an eye on performance over time.

**files:**
- `api/routes/metrics.py` - metrics API
- `reports/model_metrics.csv` - performance history
- `reports/backtest_results.csv` - backtesting

---

## performance metrics

### what we measure during training

for each location:

| metric | what it is | why it matters |
|--------|-----------|--------|
| **MAE** (Mean Absolute Error) | average difference | tells you errors in actual case numbers |
| **RMSE** (Root Mean Squared Error) | penalizes big errors more | cares more about really bad predictions |
| **R²** | how much we explained | 0.8 = explained 80% of the ups and downs |
| **MAPE** | percentage error | how wrong we were in percent terms |

**example:**
```python
{
    'location': 'Metro Manila',
    'mae': 234.56,
    'rmse': 412.34,
    'r2': 0.782,
    'mape': 12.45,
    'train_samples': 85,
    'validation_samples': 14,
    'test_samples': 14
}
```

---

## danger zones

### assigning risk levels

predictions get a color based on how bad they are:

```python
def classify_risk_level(predicted_cases, historical_mean, historical_std):
    """color code the prediction"""
    
    # how many standard deviations away from average
    z_score = (predicted_cases - historical_mean) / historical_std if historical_std > 0 else 0
    
    if z_score < 0:
        return 'LOW'  # green
    elif z_score < 1:
        return 'MODERATE'  # yellow
    elif z_score < 2:
        return 'HIGH'  # orange
    else:
        return 'CRITICAL'  # red
```

**color meanings:**
- **GREEN** - below average (safe)
- **YELLOW** - average to average+1 std dev
- **ORANGE** - average+1 to average+2 std dev  
- **RED** - way above average (bad)

---

## tracking performance by location

### what's in the metrics file

`reports/model_metrics.csv` stores:

```csv
location,mae,rmse,r2,mape,total_cases,avg_daily,data_points,last_updated
Metro Manila,234.56,412.34,0.782,12.45,15234,523.24,89,2024-01-31
Laguna,145.23,287.65,0.821,9.12,8567,287.56,76,2024-01-31
Cavite,89.45,156.78,0.901,7.23,4521,145.61,72,2024-01-31
```

**what it tells us:**
- **high R²** = model is reliable
- **low MAE relative to avg_daily** = errors are proportional
- **consistent MAPE** = works the same across locations

---

## backtesting results

### how predictions actually did

`reports/backtest_results.csv`:

```csv
location,forecast_date,actual_date,predicted_cases,actual_cases,error,error_pct,days_ahead
Metro Manila,2024-01-24,2024-01-31,450,512,62,13.5,7
Metro Manila,2024-01-24,2024-01-30,420,478,58,12.1,6
Metro Manila,2024-01-24,2024-01-29,380,398,18,4.5,5
```

**what it shows:**
```python
# error gets bigger the further out you predict
# day 1: ±3.2% error
# day 4: ±8.5% error
# day 7: ±15.3% error
```

---

## metrics API

### `GET /api/v1/metrics`

returns all the metrics for the system.

**example response:**
```json
{
  "generated_at": "2024-01-31T15:30:00Z",
  "overall_stats": {
    "locations_tracked": 10,
    "average_r2": 0.812,
    "average_mae": 156.34,
    "median_mape": 10.23
  },
  "location_metrics": [
    {
      "location": "Metro Manila",
      "mae": 234.56,
      "rmse": 412.34,
      "r2": 0.782,
      "mape": 12.45,
      "last_updated": "2024-01-31T15:20:00Z"
    }
  ],
  "model_info": {
    "algorithm": "LightGBM",
    "last_training": "2024-01-31T10:00:00Z",
    "training_data_points": 2147,
    "feature_count": 25
  }
}
```

---

## what's good performance

### ranges for each metric

| metric | excellent | good | acceptable | poor |
|--------|-----------|------|-----------|------|
| **R²** | > 0.80 | 0.70-0.80 | 0.60-0.70 | < 0.60 |
| **MAPE** | < 8% | 8-12% | 12-15% | > 15% |
| **MAE/Mean** | < 20% | 20-30% | 30-40% | > 40% |

**our system:** about 85% of models are "good" to "excellent"

---

## finding weird predictions

### automatic checks

we automatically flag predictions that look sus:

```python
def validate_prediction_quality(prediction, historical_context):
    """catch anomalies"""
    
    # check 1: extreme outlier
    if abs(prediction - historical_mean) > 5 * historical_std:
        flag_anomaly("way too high or too low")
    
    # check 2: nothing changes
    if prediction_std == 0:
        flag_anomaly("same prediction every day - boring")
    
    # check 3: outside normal range
    ci_lower = historical_mean - 2 * historical_std
    ci_upper = historical_mean + 2 * historical_std
    
    if not (ci_lower < prediction < ci_upper):
        flag_warning("prediction outside normal range")
```

---

## seasonal patterns

### accuracy changes by time of year

```
month     avg MAE    avg RMSE   avg R²
-----     -------    --------   ------
january    234.5      412.3      0.78
february   189.3      356.8      0.81
march      156.7      289.4      0.84
april      234.8      445.6      0.73
```

**finding:** mid-year is harder to predict (May-June worse)

---

## tracking improvements

### what we watch over time

- how long training takes per location
- model file size
- which features matter most
- how fast predictions run (API response time)

**targets:**
- training: < 5 seconds per location
- full pipeline: < 60 seconds
- API response: < 100ms

---

## weekly reports

### what the report looks like

```
MODEL PERFORMANCE REPORT - Week Ending 2024-01-31

KEY METRICS:
- Average R²: 0.812 (↑ 0.03 from last week)
- Average MAE: 156.34 cases/day (↓ 12% from last week)
- Forecast Accuracy (Day 1): 96.4%

TOP PERFORMERS:
1. Cavite: R² = 0.901, MAPE = 7.23%
2. Bulacan: R² = 0.889, MAPE = 8.45%
3. Pangasinan: R² = 0.876, MAPE = 9.12%

NEEDS ATTENTION:
- Quezon City: R² = 0.621 (weird patterns)
- Cabanatuan: MAE = 456 (data quality issues)

RECOMMENDATIONS:
1. tune hyperparameters for low performers
2. check data quality for problematic locations
3. try new features for locations that struggle
```

---

## how it all works

- metrics auto-generated after each pipeline run
- accessible via REST API real-time
- historical metrics kept for trend analysis
- alerts fire if performance drops suddenly
