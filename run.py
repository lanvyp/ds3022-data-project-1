from load import load_parquet_files
from clean import clean_trip_tables
from transform import transform_trip_tables
from analysis import run_analysis

# runs the full pipeline in order: load, clean, transform, analyze
def pipeline():
    load_parquet_files()
    clean_trip_tables()
    transform_trip_tables()
    run_analysis()

if __name__ == "__main__":
    pipeline()