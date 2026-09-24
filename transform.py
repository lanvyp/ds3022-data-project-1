
import duckdb
import logging
 
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
    filename='transform.log'
)
logger = logging.getLogger(__name__)
 
TABLES = ["yellow_trips", "green_trips"]

# main function to transform tables
def transform_table(con, table_name):
    # match this table to its vehicle_type in vehicle_emissions
    if table_name == "yellow_trips":
        vehicle_type = "yellow_taxi"
    else:
        vehicle_type = "green_taxi"
 
    # each new column paired with its data type and the SQL expression that fills it
    NEW_COLUMNS = {
        # utilize real-time lookup according to in class
        "trip_co2_kgs": ("DOUBLE", f"""
            (trip_distance * (
                SELECT co2_grams_per_mile FROM vehicle_emissions
                WHERE vehicle_type = '{vehicle_type}'
            )) / 1000
        """),
        # avg_mph
        "avg_mph": ("DOUBLE", "trip_distance / (date_diff('second', pickup_datetime, dropoff_datetime) / 3600.0)"),
        # hour_of_day
        "hour_of_day": ("INTEGER", "date_part('hour', pickup_datetime)"),
        # day_of_week
        "day_of_week": ("INTEGER", "date_part('dow', pickup_datetime)"),
        # week_of_year
        "week_of_year": ("INTEGER", "date_part('week', pickup_datetime)"),
        # month_of_year
        "month_of_year": ("INTEGER", "date_part('month', pickup_datetime)"),
    }
 
    for column_name, (data_type, expression) in NEW_COLUMNS.items():
        con.execute(f"""
            ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {column_name} {data_type};
        """)
        con.execute(f"""
            UPDATE {table_name} SET {column_name} = {expression};
        """)
        logger.info(f"{table_name}: added {column_name}")
 
    n = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    logger.info(f"{table_name}: {n} rows transformed")
    print(f"{table_name}: {n} rows transformed")
 
# main function to transform all trip tables
def transform_trip_tables():
    con = None
    try:
        con = duckdb.connect(database='emissions.duckdb', read_only=False)
        logger.info("Connected to DuckDB instance")
 
        for table in TABLES:
            transform_table(con, table)
 
    except Exception as e:
        print(f"An error occurred: {e}")
        logger.error(f"An error occurred: {e}")
 
    finally:
        if con:
            con.close()
            logger.info("Closed DuckDB connection")
 
if __name__ == "__main__":
    transform_trip_tables()