from __future__ import annotations

from datetime import date
from io import BytesIO, TextIOWrapper
from zipfile import ZipFile

import pandas as pd
import requests
from dotenv import load_dotenv
from os import getenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from urllib.parse import quote_plus


GTFS_URL = "https://api.data.gov.my/gtfs-static/prasarana?category=rapid-rail-kl"

ROUTE_TYPE_MAP = {
    0: "Tram",
    1: "LRT",
    2: "KTM",
    3: "BUS",
    5: "Monorail",
}

PEAK_HOURS = {7, 8, 9, 17, 18, 19}


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


def download_gtfs_zip() -> ZipFile:
    response = requests.get(GTFS_URL, timeout=60)
    response.raise_for_status()
    return ZipFile(BytesIO(response.content))


def read_gtfs_file(gtfs_zip: ZipFile, filename: str) -> pd.DataFrame:
    with gtfs_zip.open(filename) as gtfs_file:
        return pd.read_csv(TextIOWrapper(gtfs_file, encoding="utf-8-sig"))


def normalize_nullable(value):
    if pd.isna(value) or value == "":
        return None
    return value


def parse_routes(routes_df: pd.DataFrame) -> list[dict]:
    routes = []
    for row in routes_df.itertuples(index=False):
        route_type_id = normalize_nullable(getattr(row, "route_type", None))
        route_type = ROUTE_TYPE_MAP.get(int(route_type_id), "Unknown") if route_type_id is not None else "Unknown"

        routes.append(
            {
                "route_code": normalize_nullable(getattr(row, "route_id", None)),
                "route_name": normalize_nullable(getattr(row, "route_long_name", None)),
                "route_type": route_type,
                "operator": normalize_nullable(getattr(row, "agency_id", None)),
                "line_color": normalize_nullable(getattr(row, "route_color", None)),
                "is_express": False,
            }
        )
    return routes


def parse_stops(stops_df: pd.DataFrame) -> list[dict]:
    stops = []
    for row in stops_df.itertuples(index=False):
        stops.append(
            {
                "stop_code": normalize_nullable(getattr(row, "stop_id", None)),
                "stop_name": normalize_nullable(getattr(row, "stop_name", None)),
                "latitude": normalize_nullable(getattr(row, "stop_lat", None)),
                "longitude": normalize_nullable(getattr(row, "stop_lon", None)),
                "zone": normalize_nullable(getattr(row, "zone_id", None)),
                "is_terminal": False,
                "is_interchange": False,
                "route_id": None,
            }
        )
    return stops


def generate_dates() -> list[dict]:
    dates = []
    for full_date in pd.date_range(start="2024-01-01", end=date.today(), freq="D"):
        day = full_date.date()
        dates.append(
            {
                "full_date": day,
                "year": day.year,
                "month": day.month,
                "day": day.day,
                "weekday": day.strftime("%A"),
                "week_num": int(day.strftime("%V")),
                "is_weekend": day.weekday() >= 5,
                "is_holiday": False,
                "holiday_name": None,
            }
        )
    return dates


def period_for_hour(hour: int) -> str:
    if 7 <= hour <= 9:
        return "Morning Peak"
    if 12 <= hour <= 14:
        return "Lunch"
    if 17 <= hour <= 19:
        return "Evening Peak"
    if 20 <= hour <= 23:
        return "Night"
    if 0 <= hour <= 6:
        return "Midnight"
    return "Afternoon"


def generate_times() -> list[dict]:
    return [
        {
            "hour": hour,
            "minute": minute,
            "period": period_for_hour(hour),
            "is_peak_hour": hour in PEAK_HOURS,
        }
        for hour in range(24)
        for minute in range(60)
    ]


def insert_rows(engine: Engine, statement: str, rows: list[dict]) -> None:
    if not rows:
        return

    with engine.begin() as connection:
        connection.execute(text(statement), rows)


def main() -> None:
    print("[1/6] Downloading GTFS...")
    gtfs_zip = download_gtfs_zip()

    print("[2/6] Parsing routes...")
    routes_df = read_gtfs_file(gtfs_zip, "routes.txt")
    routes = parse_routes(routes_df)

    print("[3/6] Parsing stops...")
    stops_df = read_gtfs_file(gtfs_zip, "stops.txt")
    stops = parse_stops(stops_df)

    print("[4/6] Generating date and time dimensions...")
    dates = generate_dates()
    times = generate_times()

    print("[5/6] Connecting to database...")
    engine = build_engine()

    print("[6/6] Inserting rows...")
    insert_rows(
        engine,
        """
        INSERT INTO dim_route (
            route_code, route_name, route_type, operator, line_color, is_express
        )
        VALUES (
            :route_code, :route_name, :route_type, :operator, :line_color, :is_express
        )
        ON CONFLICT (route_code) DO NOTHING
        """,
        routes,
    )
    print(f"      Routes processed: {len(routes)}")

    insert_rows(
        engine,
        """
        INSERT INTO dim_stop (
            stop_code, stop_name, latitude, longitude, zone,
            is_terminal, is_interchange, route_id
        )
        VALUES (
            :stop_code, :stop_name, :latitude, :longitude, :zone,
            :is_terminal, :is_interchange, :route_id
        )
        ON CONFLICT (stop_code) DO NOTHING
        """,
        stops,
    )
    print(f"      Stops processed: {len(stops)}")

    insert_rows(
        engine,
        """
        INSERT INTO dim_date (
            full_date, year, month, day, weekday, week_num,
            is_weekend, is_holiday, holiday_name
        )
        VALUES (
            :full_date, :year, :month, :day, :weekday, :week_num,
            :is_weekend, :is_holiday, :holiday_name
        )
        ON CONFLICT (full_date) DO NOTHING
        """,
        dates,
    )
    print(f"      Dates processed: {len(dates)}")

    insert_rows(
        engine,
        """
        INSERT INTO dim_time (hour, minute, period, is_peak_hour)
        VALUES (:hour, :minute, :period, :is_peak_hour)
        ON CONFLICT (hour, minute) DO NOTHING
        """,
        times,
    )
    print(f"      Times processed: {len(times)}")
    print("ETL complete.")


if __name__ == "__main__":
    main()
