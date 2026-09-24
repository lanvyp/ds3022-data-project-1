import duckdb
import logging

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
    filename='clean.log'
)
logger = logging.getLogger(__name__)

TABLES = ["yellow_trips", "green_trips"]

# main function to clean all trip tables
def clean_table(con, table_name):
    # base line 
    before_count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    logger.info(f"{table_name}: {before_count} rows before cleaning")

    # remove duplicate trips
    con.execute(f"""
        CREATE OR REPLACE TABLE {table_name} AS
        SELECT DISTINCT * FROM {table_name};
    """)
    n1 = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    logger.info(f"{table_name}: {n1} rows after removing duplicates")

    # remove trips with 0 passengers
    con.execute(f"""
        DELETE FROM {table_name}
        WHERE passenger_count = 0;
    """)
    n2 = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    logger.info(f"{table_name}: {n2} after removing 0-passenger trips")

    # remove trips 0 miles in length
    con.execute(f"""
        DELETE FROM {table_name}
        WHERE trip_distance = 0;
    """)
    n3 = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    logger.info(f"{table_name}: {n3} after removing 0-mile trips")

    # remove trips longer than 100 miles
    con.execute(f"""
        DELETE FROM {table_name}
        WHERE trip_distance > 100;
    """)
    n4 = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    logger.info(f"{table_name}: {n4} after removing trips over 100 miles")

    # remove trips lasting more than 1 day (86400 seconds)
    con.execute(f"""
        DELETE FROM {table_name}
        WHERE date_diff('second', pickup_datetime, dropoff_datetime) > 86400
           OR date_diff('second', pickup_datetime, dropoff_datetime) <= 0;
    """)
    after_count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    logger.info(f"{table_name}: {after_count} after removing trips over 1 day")
    removed = before_count - after_count
    logger.info(f"{table_name}: {after_count} after cleaning ({removed} removed)")
    print(f"{table_name}: {before_count} -> {after_count} rows ({removed} removed)")

# to test to see if it at 0 or not
def verify_table(con, table_name):
    # checkl for no duplicate
    dupes = con.execute(f"""
        SELECT COUNT(*) FROM (
            SELECT *, COUNT(*) AS cnt FROM {table_name} GROUP BY ALL HAVING cnt > 1
        )
    """).fetchone()[0]
    print(f"{table_name}: duplicates remaining = {dupes}")
    logger.info(f"{table_name}: duplicates remaining = {dupes}")

    # check if no 0 passenger trips
    zero_pax = con.execute(f"SELECT COUNT(*) FROM {table_name} WHERE passenger_count = 0").fetchone()[0]
    print(f"{table_name}: 0-passenger trips remaining = {zero_pax}")
    logger.info(f"{table_name}: 0-passenger trips remaining = {zero_pax}")

    # check if no 0-mile trips
    zero_miles = con.execute(f"SELECT COUNT(*) FROM {table_name} WHERE trip_distance = 0").fetchone()[0]
    print(f"{table_name}: 0-mile trips remaining = {zero_miles}")
    logger.info(f"{table_name}: 0-mile trips remaining = {zero_miles}")

    # check if no trips over 100 miles
    over_100 = con.execute(f"SELECT COUNT(*) FROM {table_name} WHERE trip_distance > 100").fetchone()[0]
    print(f"{table_name}: over-100-mile trips remaining = {over_100}")
    logger.info(f"{table_name}: over-100-mile trips remaining = {over_100}")

    # check if no trips over 1 day
    over_day = con.execute(f"""
        SELECT COUNT(*) FROM {table_name}
        WHERE date_diff('second', pickup_datetime, dropoff_datetime) > 86400
    """).fetchone()[0]
    print(f"{table_name}: over-1-day trips remaining = {over_day}")
    logger.info(f"{table_name}: over-1-day trips remaining = {over_day}")

# runs everything
def clean_trip_tables():
    con = None
    try:
        con = duckdb.connect(database='emissions.duckdb', read_only=False)
        logger.info("Connected to DuckDB instance")

        for table in TABLES:
            clean_table(con, table)
            verify_table(con, table)

    except Exception as e:
        print(f"An error occurred: {e}")
        logger.error(f"An error occurred: {e}")

    finally:
        if con:
            con.close()
            logger.info("Closed DuckDB connection")

if __name__ == "__main__":
    clean_trip_tables()