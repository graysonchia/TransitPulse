from __future__ import annotations

import random
from os import getenv
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


TOTAL_ROWS = 500_000
BATCH_SIZE = 1_000


def build_engine() -> Engine:
    load_dotenv()

    required_vars = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing = [name for name in required_vars if not getenv(name)]
    if missing:
        raise RuntimeError(f"Missing required .env variables: {', '.join(missing)}")

    user = quote_plus(getenv("DB_USER", ""))
    password = quote_plus(getenv("DB_PASSWORD", ""))
    host = getenv("DB_HOST")
    port = getenv("DB_PORT")
    database = getenv("DB_NAME")
    connection_string = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"

    return create_engine(connection_string)


def fetch_dimension_ids(engine: Engine) -> dict[str, list]:
    with engine.connect() as connection:
        dimensions = {
            "dates": connection.execute(text("SELECT date_id FROM dim_date")).scalars().all(),
            "routes": connection.execute(text("SELECT route_id FROM dim_route")).scalars().all(),
            "stops": connection.execute(text("SELECT stop_id FROM dim_stop")).scalars().all(),
            "times": connection.execute(
                text("SELECT time_id, is_peak_hour FROM dim_time")
            ).mappings().all(),
        }

    empty_dimensions = [name for name, values in dimensions.items() if not values]
    if empty_dimensions:
        raise RuntimeError(
            "Cannot seed fact_ridership because these dimensions are empty: "
            + ", ".join(empty_dimensions)
        )

    return dimensions


def weighted_passenger_count(is_peak_hour: bool) -> int:
    if is_peak_hour:
        ranges = [(20, 80), (81, 160), (161, 260), (261, 400)]
        weights = [15, 35, 35, 15]
    else:
        ranges = [(0, 15), (16, 50), (51, 100), (101, 180)]
        weights = [35, 40, 20, 5]

    low, high = random.choices(ranges, weights=weights, k=1)[0]
    return random.randint(low, high)


def weighted_delay_minutes() -> float:
    return round(random.triangular(0, 30, 0), 2)


def make_batch(dimensions: dict[str, list], batch_size: int) -> list[dict]:
    rows = []
    for _ in range(batch_size):
        time_row = random.choice(dimensions["times"])
        trip_number = random.randint(1, 999_999_999)

        rows.append(
            {
                "date_id": random.choice(dimensions["dates"]),
                "time_id": time_row["time_id"],
                "route_id": random.choice(dimensions["routes"]),
                "stop_id": random.choice(dimensions["stops"]),
                "trip_id": f"SIM-{trip_number:09d}",
                "passenger_count": weighted_passenger_count(time_row["is_peak_hour"]),
                "delay_minutes": weighted_delay_minutes(),
            }
        )

    return rows


def insert_batch(engine: Engine, rows: list[dict]) -> None:
    statement = text(
        """
        INSERT INTO fact_ridership (
            date_id, time_id, route_id, stop_id,
            trip_id, passenger_count, delay_minutes
        )
        VALUES (
            :date_id, :time_id, :route_id, :stop_id,
            :trip_id, :passenger_count, :delay_minutes
        )
        """
    )

    with engine.begin() as connection:
        connection.execute(statement, rows)


def count_existing_rows(engine: Engine) -> int:
    with engine.connect() as connection:
        return connection.execute(text("SELECT COUNT(*) FROM fact_ridership")).scalar_one()


def main() -> None:
    print("[1/3] Connecting to database...")
    engine = build_engine()

    print("[2/3] Loading dimension IDs...")
    dimensions = fetch_dimension_ids(engine)
    print(
        "      Loaded "
        f"{len(dimensions['dates'])} dates, "
        f"{len(dimensions['routes'])} routes, "
        f"{len(dimensions['stops'])} stops, "
        f"{len(dimensions['times'])} times."
    )

    existing_rows = count_existing_rows(engine)
    rows_to_insert = max(TOTAL_ROWS - existing_rows, 0)
    if rows_to_insert == 0:
        print(f"[3/3] fact_ridership already has at least {TOTAL_ROWS:,} rows.")
        print("Ridership seeding complete.")
        return

    print(
        f"[3/3] Generating and inserting {rows_to_insert:,} ridership rows "
        f"to reach {TOTAL_ROWS:,} total..."
    )
    inserted = 0
    while inserted < rows_to_insert:
        current_batch_size = min(BATCH_SIZE, rows_to_insert - inserted)
        rows = make_batch(dimensions, current_batch_size)
        insert_batch(engine, rows)
        inserted += current_batch_size

        if inserted % 10_000 == 0 or inserted == rows_to_insert:
            print(f"      Inserted {inserted:,}/{rows_to_insert:,} new rows")

    print("Ridership seeding complete.")


if __name__ == "__main__":
    main()
