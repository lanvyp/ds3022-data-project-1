import duckdb
import logging
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
    filename='analysis.log'
)
logger = logging.getLogger(__name__)

DB_PATH = "emissions.duckdb"
TABLES = {"YELLOW": "yellow_trips", "GREEN": "green_trips"}

# day_of_week
DAY_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
# month_of_year is 1-12
MONTH_NAMES = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# helper function to log and print messages
def report(message):
    print(message)    
    logger.info(message) 

# helper function to find the largest single trip in terms of CO2 output
def largest_trip(con, label, table):
    # single largest carbon producing trip of the year
    val = con.execute(f"SELECT MAX(trip_co2_kgs) FROM {table}").fetchone()[0]
    report(f"[{label}] Largest single-trip CO2 output of the year: {val:.4f} kg")

# helper function to find the heaviest and lightest average CO2 output by a given column
def heaviest_lightest(con, label, table, column, description, names=None):
    # groups by the given column, averages trip_co2_kgs across the whole year --> reports the heaviest and lightest average
    rows = con.execute(f"""
        SELECT {column}, AVG(trip_co2_kgs) AS avg_co2
        FROM {table} GROUP BY {column} ORDER BY avg_co2 DESC
    """).fetchall()

    pretty = lambda v: names[int(v)] if names else v
    high, low = rows[0], rows[-1]

    report(f"[{label}] Most carbon-heavy {description}: {pretty(high[0])} ({high[1]:.4f} kg avg/trip)")
    report(f"[{label}] Most carbon-light {description}: {pretty(low[0])} ({low[1]:.4f} kg avg/trip)")

# helper function to plot monthly CO2 output for both cab types
def plot_monthly_co2(con):
    # time-series plot: month on X-axis, total CO2 on Y-axis, one line per cab type
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = {"YELLOW": "#E8A33D", "GREEN": "#2E7D5B"}

    for label, table in TABLES.items():
        by_month = con.execute(f"""
            SELECT month_of_year, SUM(trip_co2_kgs) AS total_co2
            FROM {table} GROUP BY month_of_year ORDER BY month_of_year
        """).fetchdf()
        ax.plot(by_month["month_of_year"], by_month["total_co2"],
                marker="o", linewidth=2, color=colors[label], label=f"{label.title()} taxi")

    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(MONTH_NAMES[1:])
    ax.set_xlabel("Month")
    ax.set_ylabel("Total CO2 (kg)")
    ax.set_title("Monthly CO2 Output: Yellow vs Green Taxi Trips (2024)")
    ax.legend()
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig("co2_by_month.png", dpi=150)
    plt.close(fig)
    report("Saved plot: co2_by_month.png")

# main function to run the analysis
def run_analysis():
    con = None
    try:
        con = duckdb.connect(database=DB_PATH, read_only=True)
        logger.info("Connected to DuckDB instance")

        for label, table in TABLES.items():
            largest_trip(con, label, table)
            heaviest_lightest(con, label, table, "hour_of_day", "hour of day")
            heaviest_lightest(con, label, table, "day_of_week", "day of week", names=DAY_NAMES)
            heaviest_lightest(con, label, table, "week_of_year", "week of year")
            heaviest_lightest(con, label, table, "month_of_year", "month of year", names=MONTH_NAMES)
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