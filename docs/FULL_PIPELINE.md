# full pipeline

## what it does

runs everything from start to finish. takes raw data from kaggle, cleans it, builds features, trains models, and generates predictions. one script to run the whole system.

**file:** `scripts/full_pipeline.py`

---

## the 5 stages

### stage 1: download data

**function:** `download_latest_data(data_dir='../data')`

grabs the latest covid data from kaggle.

```
dataset: cvronao/covid19-philippine-dataset
output: Case_Information.csv
```

**what happens:**
1. uses kaggle API
2. downloads and unzips automatically
3. checks the file is there
4. returns the path

**needs:**
- kaggle API setup (`~/.kaggle/kaggle.json`)
- internet
- write access

---

### stage 2: clean data

**function:** `clean_pipeline(input_csv, output_csv='data/cleaned_ph_covid.csv')`

makes the messy raw data actually usable.

```
input:  Case_Information.csv (raw, messy)
        ↓
process: - fix column names
         - fill missing dates
         - make time series continuous
        ↓
output: cleaned_ph_covid.csv
```

**what it looks like:**
```csv
date,location,new_cases
2020-01-30,Metro Manila,3
2020-01-31,Metro Manila,5
2020-02-01,Metro Manila,0
```

---

### stage 3: feature engineering

**function:** `feature_pipeline(input_csv, output_csv='data/features_ph_covid.csv')`

creates all the features models need to learn.

```
input:  cleaned_ph_covid.csv
        ↓
process: - lag features (1-14 days)
         - rolling stats
         - temporal features
         - trend
        ↓
output: features_ph_covid.csv (25 features per row)
```

**25 total features:**
- 14 lag
- 5 rolling stats
- 5 temporal
- 1 trend

---

### stage 4: train models

**function:** `train_all_locations(features_csv, top_n=10)`

trains lightgbm for top locations.

```
input:  features_ph_covid.csv
        ↓
process: - pick top N by cases
         - for each:
           * split train/valid/test
           * train model
           * evaluate
           * save
        ↓
output: models/{location}_model.pkl
        reports/model_metrics.csv
```

**default:** top 10 locations

---

### stage 5: predict

**function:** `generate_all_predictions(models_dir, features_df, output_json, top_n=10)`

makes 7-day forecasts.

```
input:  trained models + latest features
        ↓
process: - for each location:
           * iterative forecast
           * validate predictions
         - compile to JSON
        ↓
output: predictions_7d.json
```

**json format:**
```json
{
  "generated_at": "2024-01-31T15:30:00Z",
  "predictions": {
    "Metro Manila": [
      {"date": "2024-02-01", "predicted_cases": 523.45, "day_ahead": 1},
      {"date": "2024-02-02", "predicted_cases": 487.12, "day_ahead": 2}
    ]
  }
}
```

---

## running the full pipeline

### `run_full_pipeline(skip_download=False, top_n=10)`

orchestrates everything with error handling and logging.

**parameters:**
- `skip_download` - skip data download (use existing), default: False
- `top_n` - how many locations, default: 10

**returns:**
- boolean: true if successful

**how to run:**
```bash
# full run
python full_pipeline.py

# skip download
python full_pipeline.py --skip-download

# model top 15 locations
python full_pipeline.py --top-n 15

# combine
python full_pipeline.py --skip-download --top-n 20
```

---

## the flow

```
START
  ↓
[1] download data (skip if --skip-download)
  ├─ kaggle API
  ├─ extract
  └─ validate
  ↓
[2] clean data
  ├─ load raw
  ├─ standardize
  ├─ fill dates
  └─ save
  ↓
[3] create features
  ├─ load clean
  ├─ engineer per location
  ├─ combine
  └─ save
  ↓
[4] train models
  ├─ pick top N
  ├─ train (loop)
  ├─ save models
  └─ save metrics
  ↓
[5] make predictions
  ├─ load models
  ├─ generate forecasts
  ├─ validate
  └─ save JSON
  ↓
[6] checks
  ├─ validate predictions
  └─ check anomalies
  ↓
SUCCESS → summary
```

---

## logging

logs go to both file and console.

**log file:** `pipeline.log`

**levels:**
- **INFO** - major milestones
- **WARNING** - non-critical problems
- **ERROR** - things that need fixing

**example:**
```
2024-01-31 15:20:00 - INFO - STARTING PIPELINE
2024-01-31 15:20:15 - INFO - downloading from Kaggle...
2024-01-31 15:20:45 - INFO - download done
2024-01-31 15:20:50 - INFO - starting cleanup...
2024-01-31 15:21:00 - INFO - processed 34 locations
2024-01-31 15:21:05 - INFO - feature engineering done
2024-01-31 15:21:20 - INFO - starting model training (top 10)...
2024-01-31 15:22:45 - INFO - training complete
2024-01-31 15:22:50 - INFO - generating forecasts...
2024-01-31 15:22:55 - INFO - ✓ saved predictions
2024-01-31 15:22:56 - INFO - PIPELINE COMPLETE
```

---

## timing

**typical run** (full dataset, top 10 locations):

| stage | time |
|-------|------|
| download | 30-60 sec |
| cleanup | 5-10 sec |
| features | 8-15 sec |
| training | 15-25 sec |
| predictions | 3-5 sec |
| **total** | **60-120 sec** |

---

## handling errors

robust error handling:

```python
try:
    success = run_full_pipeline(skip_download, top_n)
    
except DataDownloadError:
    # kaggle failed - use existing if available
    logger.error("download failed")
    
except DataQualityError:
    # data looks bad
    logger.error("data quality issues")
    
except ModelTrainingError:
    # training for location failed
    logger.error(f"training failed for {location}")
    # skip it, continue with others
    
except Exception as e:
    # something weird
    logger.error(f"unexpected: {str(e)}")
```

---

## output files

**what gets created:**

```
data/
  ├── cleaned_ph_covid.csv
  └── features_ph_covid.csv

models/
  ├── Metro Manila_model.pkl
  ├── Laguna_model.pkl
  └── ... (one per location)

reports/
  └── model_metrics.csv

predictions_7d.json
```

---

## production setup

### scheduled runs

can run on a schedule (cron):

```bash
# daily at 2 AM
0 2 * * * cd /path/to/pandemic-outbreak-tracker && python scripts/full_pipeline.py >> pipeline.log 2>&1
```

---

## what you need

**external:**
- Kaggle COVID-19 Philippine Dataset
- historical case data

**internal:**
- `scripts/prep.py`
- `scripts/features.py`
- `scripts/train.py`
- `scripts/predict.py`

---

## command line

```bash
# standard
python full_pipeline.py

# with args
python full_pipeline.py --skip-download --top-n 15

# full path
python /path/to/scripts/full_pipeline.py

# save output
python full_pipeline.py > pipeline_run.log 2>&1
```

---

## how to know if it worked

**success:**
- all 5 stages complete
- metrics file has data
- predictions JSON is valid
- all model files exist

**problems:**
- exit code isn't 0
- missing output files
- invalid JSON/CSV
- prediction validation fails

---

## notes

- mostly safe to re-run (overwrites old models)
- data files preserved (good for debugging)
- logs add up (archive old ones sometimes)
