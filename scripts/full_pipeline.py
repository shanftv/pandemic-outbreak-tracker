"""
full end to end pipelines
runs the complete workflow from data download to prediction generation

this script is designed to be run by the Cloud Engineer's cron job

usage:
    python full_pipeline.py [--skip-download] [--top-n 10]
"""

import os
import sys
import argparse
from datetime import datetime
import logging

# add scripts to path
sys.path.insert(0, os.path.dirname(__file__))

from prep import clean_pipeline
from features import feature_pipeline
from train import train_all_locations
from predict import generate_all_predictions, sanity_check_predictions


# setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def download_latest_data(data_dir='../data'):
    """
    dl latest data from kaggle
    
    args:
        data_dir: directory to save data
    
    returns:
        path to downloaded CSV
    """
    logger.info("Downloading latest data from Kaggle...")
    
    import subprocess
    
    try:
        # dl dataset
        result = subprocess.run(
            ['kaggle', 'datasets', 'download', 
             '-d', 'cvronao/covid19-philippine-dataset',
             '-p', data_dir, '--unzip'],
            capture_output=True,
            text=True,
            check=True
        )
        
        logger.info("Data downloaded successfully")
        
        # return path to main case file
        case_file = os.path.join(data_dir, 'Case_Information.csv')
        
        if not os.path.exists(case_file):
            raise FileNotFoundError(f"Expected file not found: {case_file}")
        
        return case_file
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to download data: {e.stderr}")
        raise
    except Exception as e:
        logger.error(f"Error downloading data: {str(e)}")
        raise


def run_full_pipeline(skip_download=False, top_n=10):
    """
    run the complete pipeline
    
    args:
        skip_download: skip data download (use existing data)
        top_n: number of top locations to model
    
    returns:
        bool: true if successful
    """
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        logger.info(f"\n{'='*80}")
        logger.info(f"STARTING PIPELINE RUN: {timestamp}")
        logger.info(f"{'='*80}\n")
        
        base_dir = os.path.dirname(os.path.dirname(__file__))
        data_dir = os.path.join(base_dir, 'data')
        models_dir = os.path.join(base_dir, 'models')
        reports_dir = os.path.join(base_dir, 'reports')
        
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(models_dir, exist_ok=True)
        os.makedirs(reports_dir, exist_ok=True)
        
        # file paths
        raw_data_path = os.path.join(data_dir, 'Case_Information.csv')
        cleaned_path = os.path.join(data_dir, 'cleaned_ph_covid.csv')
        features_path = os.path.join(data_dir, 'features_ph_covid.csv')
        metrics_path = os.path.join(reports_dir, 'model_metrics.csv')
        predictions_json = os.path.join(base_dir, 'predictions_7d.json')
        predictions_csv = os.path.join(base_dir, 'predictions_7d.csv')
        
        # step 1: dl data
        if not skip_download:
            raw_data_path = download_latest_data(data_dir)
        else:
            logger.info(f"Skipping download, using: {raw_data_path}")
            if not os.path.exists(raw_data_path):
                raise FileNotFoundError(f"Data file not found: {raw_data_path}")
        
        # step 2: clean data
        logger.info("\nStep 1/4: Cleaning data...")
        df_clean = clean_pipeline(raw_data_path, cleaned_path)
        
        # step 3: create features
        logger.info("\nStep 2/4: Engineering features...")
        df_features = feature_pipeline(cleaned_path, features_path)
        
        # step 4: train models
        logger.info(f"\n Step 3/4: Training models (top {top_n} locations)...")
        models, metrics_df = train_all_locations(
            features_path,
            models_dir,
            metrics_path,
            top_n=top_n
        )
        
        # step 5: generate predictions
        logger.info("\n🔮 Step 4/4: Generating 7-day forecasts...")
        predictions = generate_all_predictions(
            models_dir,
            features_path,
            predictions_json,
            predictions_csv
        )
        
        # step 6: sanity checks
        if not sanity_check_predictions(predictions):
            logger.warning("Predictions failed sanity checks!")
            return False
        
        # success summary
        logger.info(f"\n{'='*80}")
        logger.info("PIPELINE COMPLETED SUCCESSFULLY")
        logger.info(f"{'='*80}")
        logger.info(f"\nSummary:")
        logger.info(f"  - Cleaned records: {len(df_clean):,}")
        logger.info(f"  - Locations: {df_clean['location'].nunique()}")
        logger.info(f"  - Models trained: {len(models)}")
        logger.info(f"  - Predictions generated: {len(predictions)} locations × 7 days")
        logger.info(f"\nOutput files:")
        logger.info(f"  - {predictions_json}")
        logger.info(f"  - {predictions_csv}")
        logger.info(f"  - {metrics_path}")
        logger.info(f"\n Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
        
    except Exception as e:
        logger.error(f"\nPIPELINE FAILED: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """main entry point"""
    parser = argparse.ArgumentParser(
        description='COVID-19 Prediction Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
ex:
  # run full pipeline with data download
  python full_pipeline.py
  
  # skip download, use existing data
  python full_pipeline.py --skip-download
  
  # train models for top 5 locations only
  python full_pipeline.py --top-n 5
        """
    )
    
    parser.add_argument(
        '--skip-download',
        action='store_true',
        help='Skip Kaggle download, use existing data'
    )
    
    parser.add_argument(
        '--top-n',
        type=int,
        default=10,
        help='Number of top locations to model (default: 10)'
    )
    
    args = parser.parse_args()
    
    # run pipeline
    success = run_full_pipeline(
        skip_download=args.skip_download,
        top_n=args.top_n
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
