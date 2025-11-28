# data preparation

## what it does

this module cleans up messy covid-19 case data and makes it usable. basically takes raw data with missing dates and weird formatting, then standardizes everything and fills in the gaps so we have continuous time series for each location.

**file:** `scripts/prep.py`

---

## main function

### `standardize_and_fill(df, date_col='date', loc_col='location', target_col='new_cases')`

takes raw case data and makes it clean. fills in missing dates, fixes column names, all that stuff.

**what it needs:**
- `df` - your raw data (DataFrame with case info)
- `date_col` - name of your date column (default: 'date')
- `loc_col` - name of location column (default: 'location')
- `target_col` - what you're counting (default: 'new_cases')

**gives back:**
- a DataFrame with daily data for each location
- any missing dates get filled with 0 cases
- everything sorted by date

**how to use it:**
```python
from scripts.prep import standardize_and_fill
import pandas as pd

df = pd.read_csv('data/Case_Information.csv')
cleaned_df = standardize_and_fill(df)
```

---

## how it works

1. **date fixing**: converts date column to actual datetime format
2. **keep what matters**: only keeps date, location, and case columns
3. **split by location**: processes each place separately
4. **fill the gaps**: creates a continuous date range from first day to last day
5. **zero fill**: any missing dates get 0 cases added
6. **rebuild**: puts it all back together in order

---

## sanity checks

- makes sure the date column exists and is valid
- checks that case numbers are actually numbers
- verifies locations have proper entries
- if there are duplicate dates, just takes the last one

---

## how it fits in

used first in `full_pipeline.py`:

```python
def clean_pipeline(input_csv, output_csv='data/cleaned_ph_covid.csv'):
    """takes raw data and cleans it"""
    df = pd.read_csv(input_csv)
    df_clean = standardize_and_fill(df)
    df_clean.to_csv(output_csv, index=False)
```

---

## output looks like

| Column | Type | what it is |
|--------|------|-----------|
| date | datetime | observation date (one per day) |
| new_cases | int | cases that day (0 if missing) |
| location | str | province or region name |

---

## things to remember

- if a date is missing between start and end, we assume 0 cases that day
- we don't fill in dates before the first record or after the last one
- everything stays in time order within each location
