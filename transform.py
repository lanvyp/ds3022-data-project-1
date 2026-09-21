import duckdb
import logging

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
    filename='transform.log'
)
logger = logging.getLogger(__name__)

TABLES = ["yellow_trips", "green_trips"]

def transform_table(con, table_name):
    # match this table to its vehicle_type in vehicle_emissions
    if table_name == "yellow_trips":
        vehicle_type = "yellow_taxi"
    else:
        vehicle_type = "green_taxi"

    # utilize real-time lookup according to in class
    con.execute(f"""
        ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS trip_co2_kgs DOUBLE;
    """)
    con.execute(f"""
        UPDATE {table_name}
        SET trip_co2_kgs = (
            trip_distance * (
                SELECT co2_grams_per_mile FROM vehicle_emissions
                WHERE vehicle_type = '{vehicle_type}'
            )
        ) / 1000;
    """)
    logger.info(f"{table_name}: added trip_co2_kgs")

    # avg_mph
    con.execute(f"""
        ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS avg_mph DOUBLE;
    """)
    con.execute(f"""
        UPDATE {table_name}
        SET avg_mph = trip_distance / (date_diff('second', pickup_datetime, dropoff_datetime) / 3600.0);
    """)
    logger.info(f"{table_name}: added avg_mph")

    # hour_of_day
    con.execute(f"""
        ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS hour_of_day INTEGER;
    """)
    con.execute(f"""
        UPDATE {table_name}
        SET hour_of_day = date_part('hour', pickup_datetime);
    """)
    logger.info(f"{table_name}: added hour_of_day")

    # day_of_week
    con.execute(f"""
        ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS day_of_week INTEGER;
    """)
    con.execute(f"""
        UPDATE {table_name}
        SET day_of_week = date_part('dow', pickup_datetime);
    """)
    logger.info(f"{table_name}: added day_of_week")

    # week_of_year
    con.execute(f"""
        ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS week_of_year INTEGER;
    """)
    con.execute(f"""
        UPDATE {table_name}
        SET week_of_year = date_part('week', pickup_datetime);
    """)
    logger.info(f"{table_name}: added week_of_year")

    # month_of_year
    con.execute(f"""
        ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS month_of_year INTEGER;
    """)
    con.execute(f"""
        UPDATE {table_name}
        SET month_of_year = date_part('month', pickup_datetime);
    """)
    logger.info(f"{table_name}: added month_of_year")

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