import duckdb
import os
import logging

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
    filename='load.log'
)
logger = logging.getLogger(__name__)

# main function to load all parquet files into DuckDB
def load_parquet_files():
    con = None
    try:
        # Connect to local DuckDB instance
        con = duckdb.connect(database='emissions.duckdb', read_only=False)
        logger.info("Connected to DuckDB instance")

        # given in class
        con.execute(f"""
            DROP TABLE IF EXISTS vehicle_emissions;
            CREATE TABLE vehicle_emissions AS
            SELECT * FROM read_csv_auto('data/vehicle_emissions.csv');
        """)
        n = con.execute("SELECT COUNT(*) FROM vehicle_emissions").fetchone()[0]
        print(f"vehicle_emissions: {n} rows loaded")
        logger.info(f"Loaded {n} rows into vehicle_emissions table")

        # yellow_trips
        yellow_urls = [
            f"https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-{m:02d}.parquet"
            for m in range(1, 13)
        ]
        # trimmed the data by picking only the things we need based on what was said in class
        con.execute(f"""
            DROP TABLE IF EXISTS yellow_trips;
            CREATE TABLE yellow_trips AS
            SELECT
                VendorID,
                tpep_pickup_datetime AS pickup_datetime,
                tpep_dropoff_datetime AS dropoff_datetime,
                passenger_count,
                trip_distance
            FROM read_parquet({yellow_urls});
        """)
        n_yellow = con.execute("SELECT COUNT(*) FROM yellow_trips").fetchone()[0]
        print(f"yellow_trips: {n_yellow} rows loaded")
        logger.info(f"Loaded {n_yellow} rows into yellow_trips table")

        # green_trips
        green_urls = [
            f"https://d37ci6vzurychx.cloudfront.net/trip-data/green_tripdata_2024-{m:02d}.parquet"
            for m in range(1, 13)
        ]
        # same as above but just for green trips
        con.execute(f"""
            DROP TABLE IF EXISTS green_trips;
            CREATE TABLE green_trips AS
            SELECT
                VendorID,
                lpep_pickup_datetime AS pickup_datetime,
                lpep_dropoff_datetime AS dropoff_datetime,
                passenger_count,
                trip_distance
            FROM read_parquet({green_urls});
        """)
        n_green = con.execute("SELECT COUNT(*) FROM green_trips").fetchone()[0]
        print(f"green_trips: {n_green} rows loaded")
        logger.info(f"Loaded {n_green} rows into green_trips table")

        logger.info("Dropped table if exists")

    except Exception as e:
        print(f"An error occurred: {e}")
        logger.error(f"An error occurred: {e}")

    finally:
        if con:
            con.close()
            logger.info("Closed DuckDB connection")

if __name__ == "__main__":
    load_parquet_files()