import duckdb
import logging

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
    filename='clean.log'
)
logger = logging.getLogger(__name__)

TABLES = ["yellow_trips", "green_trips"]

def clean_table(con, table_name):
    before_count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    logger.info(f"{table_name}: {before_count} rows before cleaning")

    # the trim that was talked about in class (still confused why its not in load)
    con.execute(f"""
        CREATE OR REPLACE TABLE {table_name} AS
        SELECT DISTINCT
            pickup_datetime,
            dropoff_datetime,
            passenger_count,
            trip_distance
        FROM {table_name}
        WHERE
            passenger_count > 0
            AND trip_distance > 0
            AND trip_distance <= 100
            AND date_diff('second', pickup_datetime, dropoff_datetime) <= 86400
            AND date_diff('second', pickup_datetime, dropoff_datetime) > 0;
    """)

    after_count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    removed = before_count - after_count
    logger.info(f"{table_name}: {after_count} rows after cleaning ({removed} removed)")
    print(f"{table_name}: {before_count} -> {after_count} rows ({removed} removed)")

def verify_table(con, table_name):
    checks = {
        "duplicate rows": f"""...GROUP BY ALL HAVING cnt > 1...""",
        "0 passenger trips": f"SELECT COUNT(*) FROM {table_name} WHERE passenger_count = 0",
        "0 mile trips": f"SELECT COUNT(*) FROM {table_name} WHERE trip_distance = 0",
        "trips over 100 miles": f"SELECT COUNT(*) FROM {table_name} WHERE trip_distance > 100",
        "trips over 1 day": f"""...date_diff(...) > 86400...""",
    }

    for label, query in checks.items():
        n = con.execute(query).fetchone()[0]
        if n == 0:
            print(f"{table_name}: OK - no {label} remain")
        else:
            print(f"{table_name}: WARNING - {n} rows with {label} still present")

def clean_trip_tables():
    con = duckdb.connect(database='emissions.duckdb', read_only=False)
    for table in TABLES:
        clean_table(con, table)
        verify_table(con, table)