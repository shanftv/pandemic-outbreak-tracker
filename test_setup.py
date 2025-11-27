"""
quick test script
runs a minimal version of the pipeline to verify everything works
"""

import os
import sys

def test_imports():
    """test that all required packages are installed"""
    print("\n" + "="*60)
    print("TEST 1: Checking Python packages...")
    print("="*60)
    
    required = ['pandas', 'numpy', 'sklearn', 'lightgbm', 'joblib', 'matplotlib']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"  [OK] {package}")
        except ImportError:
            print(f"  [FAIL] {package} - NOT INSTALLED")
            missing.append(package)
    
    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print(f"   Install with: pip install {' '.join(missing)}")
        return False
    else:
        print("\nAll packages installed!")
        return True


def test_kaggle_api():
    """test kaggle API config"""
    print("\n" + "="*60)
    print("TEST 2: Checking Kaggle API...")
    print("="*60)
    
    try:
        import subprocess
        result = subprocess.run(
            ['kaggle', 'datasets', 'list', '--max-size', '1'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("  Kaggle API is configured correctly!")
            return True
        else:
            print(f"  Kaggle API error: {result.stderr}")
            print("  → Check ~/.kaggle/kaggle.json (or %USERPROFILE%\\.kaggle\\kaggle.json)")
            return False
            
    except FileNotFoundError:
        print("  'kaggle' command not found")
        print("  -> Install with: pip install kaggle")
        return False
    except Exception as e:
        print(f"  Error: {str(e)}")
        return False


def test_data_exists():
    """check if data files exist"""
    print("\n" + "="*60)
    print("TEST 3: Checking data files...")
    print("="*60)
    
    data_dir = 'data'
    expected_files = ['Case_Information.csv']
    
    if not os.path.exists(data_dir):
        print(f"  Warning: Data directory doesn't exist yet")
        print(f"  -> Run: python scripts/full_pipeline.py")
        return False
    
    for file in expected_files:
        path = os.path.join(data_dir, file)
        if os.path.exists(path):
            size_mb = os.path.getsize(path) / (1024 * 1024)
            print(f"  [OK] {file} ({size_mb:.1f} MB)")
        else:
            print(f"  Warning: {file} - not found")
            print(f"  → Download with: kaggle datasets download -d cvronao/covid19-philippine-dataset -p data --unzip")
            return False
    
    return True


def test_sample_workflow():
    """test a minimal data processing workflow"""
    print("\n" + "="*60)
    print("TEST 4: Running sample workflow...")
    print("="*60)
    
    try:
        import pandas as pd
        import numpy as np
        
        # Create sample data
        print("  Creating sample data...")
        dates = pd.date_range('2025-01-01', periods=100, freq='D')
        sample_data = pd.DataFrame({
            'location': ['TEST_CITY'] * 100,
            'date': dates,
            'new_cases': np.random.poisson(50, 100)
        })
        
        # Test cleaning
        print("  Testing data cleaning...")
        sample_data['date'] = pd.to_datetime(sample_data['date'])
        assert sample_data['date'].notna().all(), "Date parsing failed"
        
        # Test feature creation
        print("  Testing feature engineering...")
        sample_data['lag_1'] = sample_data['new_cases'].shift(1)
        sample_data['roll_mean_7'] = sample_data['new_cases'].rolling(7).mean()
        assert 'lag_1' in sample_data.columns, "Feature creation failed"
        
        # Test model
        print("  Testing LightGBM import...")
        import lightgbm as lgb
        print(f"  LightGBM version: {lgb.__version__}")
        
        print("\n  Sample workflow completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n  Error in workflow: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_scripts_exist():
    """check if all scripts exist"""
    print("\n" + "="*60)
    print("TEST 5: Checking script files...")
    print("="*60)
    
    scripts = [
        'scripts/prep.py',
        'scripts/features.py',
        'scripts/train.py',
        'scripts/predict.py',
        'scripts/full_pipeline.py'
    ]
    
    all_exist = True
    for script in scripts:
        if os.path.exists(script):
            print(f"  [OK] {script}")
        else:
            print(f"  [FAIL] {script} - NOT FOUND")
            all_exist = False
    
    return all_exist


def main():
    """run all tests"""
    print("\n" + "="*60)
    print("PANDEMIC TRACKER - SYSTEM CHECK")
    print("="*60)
    print("\nThis script will verify your setup is ready.\n")
    
    results = []
    
    # Run tests
    results.append(("Package Installation", test_imports()))
    results.append(("Kaggle API", test_kaggle_api()))
    results.append(("Script Files", test_scripts_exist()))
    results.append(("Sample Workflow", test_sample_workflow()))
    results.append(("Data Files", test_data_exists()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} - {test_name}")
    
    # Overall
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n" + "="*60)
        print("ALL TESTS PASSED!")
        print("="*60)
        print("\nYou're ready to run the pipeline!")
        print("\nNext steps:")
        print("  1. Run the full pipeline:")
        print("     python scripts/full_pipeline.py")
        print("\n  2. Or open the Jupyter notebook:")
        print("     jupyter notebook")
        print("     → Open: notebooks/01_eda_and_modeling.ipynb")
    else:
        print("\n" + "="*60)
        print("SOME TESTS FAILED")
        print("="*60)
        print("\nPlease fix the issues above and run this script again.")
        print("\nCommon fixes:")
        print("  - Missing packages: pip install -r requirements.txt")
        print("  - Kaggle API: Set up ~/.kaggle/kaggle.json")
        print("  - Data files: Run pipeline or download manually")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
