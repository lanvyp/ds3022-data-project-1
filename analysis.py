import duckdb
import logging
import matplotlib.pyplot as plt

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
    filename='analysis.log'
)
logger = logging.getLogger(__name__)
TABLES = ["yellow_trips", "green_trips"]

# labels
DAY_NAMES=["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

def report(con, table_name):
    label = table_name.replace("_trips", "").upper()

    # largest carbon producing trip of the year
    largest = con.execute(f"""
        SELECT trip_co2_kgs FROM {table_name}
        ORDER BY trip_co2_kgs DESC LIMIT 1
    """).fetchone()[0]
    msg = f"{label}: largest single-trip CO2 output of the year = {largest:.4f} kg"
    print(msg)
    logger.info(msg)

    # most carbon heavy and carbon light hour of day
    heavy_hour, heavy_hour_val = con.execute(f"""
        SELECT hour_of_day, AVG(trip_co2_kgs) AS avg_co2
        FROM {table_name} GROUP BY hour_of_day
        ORDER BY avg_co2 DESC LIMIT 1
    """).fetchone()
    light_hour, light_hour_val = con.execute(f"""
        SELECT hour_of_day, AVG(trip_co2_kgs) AS avg_co2
        FROM {table_name} GROUP BY hour_of_day
        ORDER BY avg_co2 ASC LIMIT 1
    """).fetchone()
    msg = (f"{label}: carbon-heaviest hour of day = {heavy_hour}:00 (avg {heavy_hour_val:.4f} kg) | "
           f"carbon-lightest hour of day = {light_hour}:00 (avg {light_hour_val:.4f} kg)")
    print(msg)
    logger.info(msg)

    # most carbon heavy and carbon light day of week
    heavy_dow, heavy_dow_val = con.execute(f"""
        SELECT day_of_week, AVG(trip_co2_kgs) AS avg_co2
        FROM {table_name} GROUP BY day_of_week
        ORDER BY avg_co2 DESC LIMIT 1
    """).fetchone()
    light_dow, light_dow_val = con.execute(f"""
        SELECT day_of_week, AVG(trip_co2_kgs) AS avg_co2
        FROM {table_name} GROUP BY day_of_week
        ORDER BY avg_co2 ASC LIMIT 1
    """).fetchone()
    msg = (f"{label}: carbon-heaviest day of week = {DAY_NAMES[heavy_dow]} (avg {heavy_dow_val:.4f} kg) | "
           f"carbon-lightest day of week = {DAY_NAMES[light_dow]} (avg {light_dow_val:.4f} kg)")
    print(msg)
    logger.info(msg)

    # 4. most carbon heavy and carbon light week of year
    heavy_week, heavy_week_val = con.execute(f"""
        SELECT week_of_year, AVG(trip_co2_kgs) AS avg_co2
        FROM {table_name} GROUP BY week_of_year
        ORDER BY avg_co2 DESC LIMIT 1
    """).fetchone()
    light_week, light_week_val = con.execute(f"""
        SELECT week_of_year, AVG(trip_co2_kgs) AS avg_co2
        FROM {table_name} GROUP BY week_of_year
        ORDER BY avg_co2 ASC LIMIT 1
    """).fetchone()
    msg = (f"{label}: carbon-heaviest week of year = week {heavy_week} (avg {heavy_week_val:.4f} kg) | "
           f"carbon-lightest week of year = week {light_week} (avg {light_week_val:.4f} kg)")
    print(msg)
    logger.info(msg)

    # 5. most carbon heavy and carbon light month of year
    heavy_month, heavy_month_val = con.execute(f"""
        SELECT month_of_year, AVG(trip_co2_kgs) AS avg_co2
        FROM {table_name} GROUP BY month_of_year
        ORDER BY avg_co2 DESC LIMIT 1
    """).fetchone()
    light_month, light_month_val = con.execute(f"""
        SELECT month_of_year, AVG(trip_co2_kgs) AS avg_co2
        FROM {table_name} GROUP BY month_of_year
        ORDER BY avg_co2 ASC LIMIT 1
    """).fetchone()
    msg = (f"{label}: carbon-heaviest month = {MONTH_NAMES[heavy_month - 1]} (avg {heavy_month_val:.4f} kg) | "
           f"carbon-lightest month = {MONTH_NAMES[light_month - 1]} (avg {light_month_val:.4f} kg)")
    print(msg)
    logger.info(msg)

def plot_monthly_co2(con):
    """
    6. Time-series plot: month of year on X-axis, total CO2 (kg) on Y-axis,
    one line for YELLOW and one for GREEN trips. Saved as a PNG.
    """
    yellow_by_month = con.execute("""
        SELECT month_of_year, SUM(trip_co2_kgs) AS total_co2
        FROM yellow_trips GROUP BY month_of_year ORDER BY month_of_year
    """).fetchdf()
    green_by_month = con.execute("""
        SELECT month_of_year, SUM(trip_co2_kgs) AS total_co2
        FROM green_trips GROUP BY month_of_year ORDER BY month_of_year
    """).fetchdf()

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(yellow_by_month["month_of_year"], yellow_by_month["total_co2"],
            marker="o", linewidth=2, color="#E8A33D", label="Yellow taxi")
    ax.plot(green_by_month["month_of_year"], green_by_month["total_co2"],
            marker="o", linewidth=2, color="#2E7D5B", label="Green taxi")

    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(MONTH_NAMES)
    ax.set_xlabel("Month")
    ax.set_ylabel("Total CO2 (kg)")
    ax.set_title("Monthly CO2 Output: Yellow vs Green Taxi Trips (2024)")
    ax.legend()
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig("co2_by_month.png", dpi=150)
    plt.close(fig)
    logger.info("Saved monthly CO2 plot to co2_by_month.png")
    print("Saved plot: co2_by_month.png")

def run_analysis():
    con = None
    try:
        con = duckdb.connect(database='emissions.duckdb', read_only=True)
        logger.info("Connected to DuckDB instance")

        for table in TABLES:
            report(con, table)

        plot_monthly_co2(con)

    except Exception as e:
        print(f"An error occurred: {e}")
        logger.error(f"An error occurred: {e}")

    finally:
        if con:
            con.close()
            logger.info("Closed DuckDB connection")

if __name__ == "__main__":
    run_analysis()