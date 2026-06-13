from __future__ import annotations

from datetime import datetime
from os import getenv
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

try:
    from prophet import Prophet
except ImportError:
    Prophet = None


st.set_page_config(page_title="TransitPulse Dashboard", page_icon="TP", layout="wide")

WEEKDAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
REQUIRED_DB_VARS = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]


def apply_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"], .stApp {
            font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(55, 139, 255, 0.16), transparent 32rem),
                linear-gradient(135deg, #07111f 0%, #0b1524 48%, #101827 100%);
            color: #e5edf7;
        }

        [data-testid="stSidebar"] {
            background: #0a1220;
            border-right: 1px solid rgba(148, 163, 184, 0.16);
        }

        [data-testid="stSidebar"] * {
            color: #dbeafe;
        }

        .block-container {
            max-width: 1480px;
            padding-top: 1.5rem;
            padding-bottom: 2.5rem;
        }

        .tp-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
            padding: 1.25rem 1.35rem;
            margin-bottom: 1.2rem;
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 18px;
            background: rgba(15, 23, 42, 0.78);
            box-shadow: 0 18px 50px rgba(0, 0, 0, 0.24);
        }

        .tp-logo {
            font-size: clamp(1.55rem, 4vw, 2.5rem);
            font-weight: 800;
            letter-spacing: 0;
            color: #f8fafc;
            line-height: 1.05;
        }

        .tp-logo span {
            color: #38bdf8;
        }

        .tp-tagline {
            margin-top: 0.35rem;
            color: #a7b6ca;
            font-size: clamp(0.9rem, 2vw, 1.02rem);
        }

        .tp-updated {
            color: #cbd5e1;
            font-size: 0.9rem;
            text-align: right;
            white-space: nowrap;
        }

        .kpi-card {
            padding: 1.1rem 1.15rem;
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 16px;
            background: linear-gradient(180deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.88));
            box-shadow: 0 14px 40px rgba(0, 0, 0, 0.18);
            min-height: 118px;
        }

        .kpi-label {
            color: #94a3b8;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.45rem;
        }

        .kpi-value {
            color: #f8fafc;
            font-size: clamp(1.3rem, 3vw, 2rem);
            font-weight: 800;
            line-height: 1.15;
            word-break: break-word;
        }

        .section-title {
            color: #f8fafc;
            font-size: 1.15rem;
            font-weight: 750;
            margin: 1.2rem 0 0.6rem;
        }

        .hero-panel {
            padding: 1rem;
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 18px;
            background: rgba(15, 23, 42, 0.74);
            box-shadow: 0 16px 48px rgba(0, 0, 0, 0.2);
        }

        div[data-testid="stMetricValue"] {
            color: #f8fafc;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.45rem;
            border-bottom: 1px solid rgba(148, 163, 184, 0.18);
        }

        .stTabs [data-baseweb="tab"] {
            background: rgba(15, 23, 42, 0.72);
            border-radius: 999px;
            color: #cbd5e1;
            padding: 0.55rem 1rem;
        }

        .stTabs [aria-selected="true"] {
            background: #0ea5e9;
            color: #ffffff;
        }

        @media (max-width: 768px) {
            .tp-header {
                align-items: flex-start;
                flex-direction: column;
            }

            .tp-updated {
                text-align: left;
                white-space: normal;
            }

            .kpi-card {
                min-height: 96px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource
def get_engine() -> Engine:
    project_root = Path(__file__).resolve().parents[1]
    env_path = project_root / ".env"
    load_dotenv(env_path)

    db_config = {}
    for name in REQUIRED_DB_VARS:
        try:
            secret_value = st.secrets[name]
        except Exception:
            secret_value = None
        db_config[name] = secret_value or getenv(name)

    missing = [name for name, value in db_config.items() if not value]
    if missing:
        raise RuntimeError(
            "Missing required database credentials in Streamlit Secrets or .env: "
            + ", ".join(missing)
        )

    user = quote_plus(str(db_config["DB_USER"]))
    password = quote_plus(str(db_config["DB_PASSWORD"]))
    host = db_config["DB_HOST"]
    port = db_config["DB_PORT"]
    database = db_config["DB_NAME"]
    connection_string = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"

    return create_engine(connection_string)


def read_query(sql: str, params: dict | None = None) -> pd.DataFrame:
    return pd.read_sql(text(sql), get_engine(), params=params or {})


@st.cache_data(ttl=300)
def load_filter_options() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    date_bounds = read_query(
        """
        SELECT MIN(full_date) AS min_date, MAX(full_date) AS max_date
        FROM dim_date
        """
    )
    routes = read_query(
        """
        SELECT route_id, route_code, route_name, route_type
        FROM dim_route
        ORDER BY route_name, route_code
        """
    )
    route_types = read_query(
        """
        SELECT DISTINCT route_type
        FROM dim_route
        WHERE route_type IS NOT NULL
        ORDER BY route_type
        """
    )
    return date_bounds, routes, route_types


def route_label(row: pd.Series) -> str:
    route_name = row["route_name"] or row["route_code"]
    return f"{route_name} ({row['route_code']})"


def build_filter_clause(
    start_date,
    end_date,
    selected_route_ids: list[int],
    selected_route_types: list[str],
) -> tuple[str, dict]:
    clauses = ["d.full_date BETWEEN :start_date AND :end_date"]
    params = {"start_date": start_date, "end_date": end_date}

    if selected_route_ids:
        placeholders = []
        for index, route_id in enumerate(selected_route_ids):
            key = f"route_id_{index}"
            placeholders.append(f":{key}")
            params[key] = int(route_id)
        clauses.append(f"r.route_id IN ({', '.join(placeholders)})")

    if selected_route_types:
        placeholders = []
        for index, route_type in enumerate(selected_route_types):
            key = f"route_type_{index}"
            placeholders.append(f":{key}")
            params[key] = route_type
        clauses.append(f"r.route_type IN ({', '.join(placeholders)})")

    return " AND ".join(clauses), params


def format_number(value: float | int | None) -> str:
    if pd.isna(value) or value is None:
        return "0"
    return f"{value:,.0f}"


def format_delay(value: float | int | None) -> str:
    if pd.isna(value) or value is None:
        return "0.00 min"
    return f"{value:,.2f} min"


def render_kpi(label: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def style_figure(fig: go.Figure, height: int | None = None) -> go.Figure:
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.35)",
        font={"color": "#dbeafe", "family": "Inter, sans-serif"},
        legend={"bgcolor": "rgba(0,0,0,0)"},
        margin={"l": 12, "r": 12, "t": 40, "b": 30},
    )
    fig.update_xaxes(gridcolor="rgba(148,163,184,0.14)", zerolinecolor="rgba(148,163,184,0.2)")
    fig.update_yaxes(gridcolor="rgba(148,163,184,0.14)", zerolinecolor="rgba(148,163,184,0.2)")
    if height:
        fig.update_layout(height=height)
    return fig


def get_last_updated() -> str:
    updated = read_query("SELECT MAX(created_at) AS last_updated FROM fact_ridership")
    value = updated.loc[0, "last_updated"] if not updated.empty else None
    if pd.isna(value):
        return datetime.now().strftime("%Y-%m-%d %H:%M")
    return pd.to_datetime(value).strftime("%Y-%m-%d %H:%M")


def build_forecast(daily: pd.DataFrame) -> pd.DataFrame:
    if Prophet is None:
        raise RuntimeError("Prophet is not installed in this environment.")
    if len(daily) < 2:
        raise RuntimeError("Prophet needs at least two daily ridership observations to train.")

    training = daily.rename(columns={"full_date": "ds", "total_passengers": "y"}).copy()
    training["ds"] = pd.to_datetime(training["ds"])
    training["y"] = pd.to_numeric(training["y"])

    model = Prophet(
        interval_width=0.95,
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
    )
    model.fit(training)
    future = model.make_future_dataframe(periods=90, freq="D")
    forecast = model.predict(future)
    forecast["is_forecast"] = forecast["ds"] > training["ds"].max()
    return forecast


apply_css()

try:
    date_bounds, routes, route_types = load_filter_options()
except Exception as exc:
    st.error(f"Could not connect to the TransitPulse database: {exc}")
    st.stop()

if date_bounds.empty or pd.isna(date_bounds.loc[0, "min_date"]) or pd.isna(date_bounds.loc[0, "max_date"]):
    st.warning("No dates found in dim_date. Run the ETL before opening the dashboard.")
    st.stop()

if routes.empty:
    st.warning("No routes found in dim_route. Run the GTFS ETL before opening the dashboard.")
    st.stop()

min_date = pd.to_datetime(date_bounds.loc[0, "min_date"]).date()
max_date = pd.to_datetime(date_bounds.loc[0, "max_date"]).date()
routes = routes.copy()
routes["label"] = routes.apply(route_label, axis=1)

with st.sidebar:
    st.markdown("### Controls")
    selected_dates = st.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
        start_date, end_date = selected_dates
    else:
        start_date, end_date = min_date, max_date

    route_options = dict(zip(routes["label"], routes["route_id"], strict=False))
    selected_route_labels = st.multiselect("Route", options=list(route_options.keys()))
    selected_route_ids = [route_options[label] for label in selected_route_labels]

    route_type_options = route_types["route_type"].dropna().tolist()
    selected_route_types = st.multiselect("Route type", options=route_type_options)

filter_clause, filter_params = build_filter_clause(
    start_date,
    end_date,
    selected_route_ids,
    selected_route_types,
)

with st.spinner("Loading latest dashboard data..."):
    last_updated = get_last_updated()
    kpis = read_query(
        f"""
        WITH filtered AS (
            SELECT
                f.passenger_count,
                f.delay_minutes,
                s.stop_name,
                r.route_name,
                r.route_code
            FROM fact_ridership f
            JOIN dim_date d ON f.date_id = d.date_id
            JOIN dim_route r ON f.route_id = r.route_id
            JOIN dim_stop s ON f.stop_id = s.stop_id
            WHERE {filter_clause}
        ),
        stop_rank AS (
            SELECT stop_name, SUM(passenger_count) AS total_passengers
            FROM filtered
            GROUP BY stop_name
            ORDER BY total_passengers DESC
            LIMIT 1
        ),
        route_rank AS (
            SELECT COALESCE(NULLIF(route_name, ''), route_code) AS route, SUM(passenger_count) AS total_passengers
            FROM filtered
            GROUP BY route
            ORDER BY total_passengers DESC
            LIMIT 1
        )
        SELECT
            (SELECT SUM(passenger_count) FROM filtered) AS total_ridership,
            (SELECT AVG(delay_minutes) FROM filtered) AS avg_delay,
            (SELECT stop_name FROM stop_rank) AS busiest_stop,
            (SELECT route FROM route_rank) AS busiest_route
        """,
        filter_params,
    )

st.markdown(
    f"""
    <div class="tp-header">
        <div>
            <div class="tp-logo">Transit<span>Pulse</span></div>
            <div class="tp-tagline">Live rail ridership intelligence for Kuala Lumpur transit operations.</div>
        </div>
        <div class="tp-updated">Last updated<br><strong>{last_updated}</strong></div>
    </div>
    """,
    unsafe_allow_html=True,
)

kpi_row = kpis.iloc[0] if not kpis.empty else pd.Series(dtype="object")
kpi_cols = st.columns(4)
with kpi_cols[0]:
    render_kpi("Total Ridership", format_number(kpi_row.get("total_ridership")))
with kpi_cols[1]:
    render_kpi("Average Delay", format_delay(kpi_row.get("avg_delay")))
with kpi_cols[2]:
    render_kpi("Busiest Stop", kpi_row.get("busiest_stop") or "N/A")
with kpi_cols[3]:
    render_kpi("Busiest Route", kpi_row.get("busiest_route") or "N/A")

with st.spinner("Loading stop ridership map..."):
    stop_map = read_query(
        f"""
        SELECT
            s.stop_name,
            s.latitude::FLOAT AS latitude,
            s.longitude::FLOAT AS longitude,
            SUM(f.passenger_count) AS total_passengers
        FROM fact_ridership f
        JOIN dim_date d ON f.date_id = d.date_id
        JOIN dim_route r ON f.route_id = r.route_id
        JOIN dim_stop s ON f.stop_id = s.stop_id
        WHERE {filter_clause}
            AND s.latitude IS NOT NULL
            AND s.longitude IS NOT NULL
        GROUP BY s.stop_name, s.latitude, s.longitude
        ORDER BY total_passengers DESC
        """,
        filter_params,
    )

st.markdown('<div class="section-title">Network Ridership Map</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-panel">', unsafe_allow_html=True)
if stop_map.empty:
    st.info("No stop location records match the selected filters.")
else:
    center_lat = stop_map["latitude"].mean()
    center_lon = stop_map["longitude"].mean()
    fig_map = px.scatter_mapbox(
        stop_map,
        lat="latitude",
        lon="longitude",
        size="total_passengers",
        color="total_passengers",
        hover_name="stop_name",
        hover_data={"latitude": False, "longitude": False, "total_passengers": ":,.0f"},
        color_continuous_scale="Turbo",
        size_max=38,
        zoom=10,
        height=680,
        labels={"total_passengers": "Passengers"},
    )
    fig_map.update_layout(
        mapbox_style="carto-darkmatter",
        mapbox_center={"lat": center_lat, "lon": center_lon},
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "#dbeafe"},
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
    )
    st.plotly_chart(fig_map, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

overview_tab, forecast_tab, delay_tab = st.tabs(["Ridership Overview", "90-Day Forecast", "Delay Analysis"])

with overview_tab:
    left, right = st.columns(2)

    with st.spinner("Loading ridership trend..."):
        daily = read_query(
            f"""
            SELECT d.full_date, SUM(f.passenger_count) AS total_passengers
            FROM fact_ridership f
            JOIN dim_date d ON f.date_id = d.date_id
            JOIN dim_route r ON f.route_id = r.route_id
            WHERE {filter_clause}
            GROUP BY d.full_date
            ORDER BY d.full_date
            """,
            filter_params,
        )

    with st.spinner("Loading route ridership..."):
        by_route = read_query(
            f"""
            SELECT
                COALESCE(NULLIF(r.route_name, ''), r.route_code) AS route,
                SUM(f.passenger_count) AS total_passengers
            FROM fact_ridership f
            JOIN dim_date d ON f.date_id = d.date_id
            JOIN dim_route r ON f.route_id = r.route_id
            WHERE {filter_clause}
            GROUP BY route
            ORDER BY total_passengers DESC
            """,
            filter_params,
        )

    with left:
        st.markdown('<div class="section-title">Daily Ridership Trend</div>', unsafe_allow_html=True)
        if daily.empty:
            st.info("No ridership records match the selected filters.")
        else:
            fig_daily = px.line(
                daily,
                x="full_date",
                y="total_passengers",
                markers=True,
                labels={"full_date": "Date", "total_passengers": "Passengers"},
            )
            fig_daily.update_traces(line={"color": "#38bdf8", "width": 3}, marker={"size": 6})
            st.plotly_chart(style_figure(fig_daily, height=430), use_container_width=True)

    with right:
        st.markdown('<div class="section-title">Ridership by Route</div>', unsafe_allow_html=True)
        if by_route.empty:
            st.info("No route ridership records match the selected filters.")
        else:
            fig_route = px.bar(
                by_route,
                x="route",
                y="total_passengers",
                labels={"route": "Route", "total_passengers": "Passengers"},
                color="total_passengers",
                color_continuous_scale="Blues",
            )
            fig_route.update_layout(xaxis_tickangle=-35, showlegend=False)
            st.plotly_chart(style_figure(fig_route, height=430), use_container_width=True)

    with st.spinner("Loading hour by weekday heatmap..."):
        heatmap = read_query(
            f"""
            SELECT
                d.weekday,
                EXTRACT(ISODOW FROM d.full_date)::INT AS weekday_order,
                t.hour,
                SUM(f.passenger_count) AS total_passengers
            FROM fact_ridership f
            JOIN dim_date d ON f.date_id = d.date_id
            JOIN dim_time t ON f.time_id = t.time_id
            JOIN dim_route r ON f.route_id = r.route_id
            WHERE {filter_clause}
            GROUP BY d.weekday, weekday_order, t.hour
            ORDER BY weekday_order, t.hour
            """,
            filter_params,
        )

    st.markdown('<div class="section-title">Hour vs Weekday Ridership</div>', unsafe_allow_html=True)
    if heatmap.empty:
        st.info("No hourly ridership records match the selected filters.")
    else:
        heatmap_pivot = heatmap.pivot(index="weekday", columns="hour", values="total_passengers")
        heatmap_pivot = heatmap_pivot.reindex(WEEKDAY_ORDER)
        fig_heatmap = px.imshow(
            heatmap_pivot,
            aspect="auto",
            color_continuous_scale="YlGnBu",
            labels={"x": "Hour", "y": "Weekday", "color": "Passengers"},
        )
        st.plotly_chart(style_figure(fig_heatmap, height=470), use_container_width=True)

with forecast_tab:
    st.markdown('<div class="section-title">Prophet Forecast: Next 90 Days</div>', unsafe_allow_html=True)
    with st.spinner("Training Prophet model and forecasting the next 90 days..."):
        try:
            forecast = build_forecast(daily)
            future_only = forecast[forecast["is_forecast"]].copy()

            fig_forecast = go.Figure()
            fig_forecast.add_trace(
                go.Scatter(
                    x=daily["full_date"],
                    y=daily["total_passengers"],
                    mode="lines+markers",
                    name="Historical",
                    line={"color": "#38bdf8", "width": 3},
                )
            )
            fig_forecast.add_trace(
                go.Scatter(
                    x=future_only["ds"],
                    y=future_only["yhat_upper"],
                    mode="lines",
                    line={"width": 0},
                    showlegend=False,
                    hoverinfo="skip",
                )
            )
            fig_forecast.add_trace(
                go.Scatter(
                    x=future_only["ds"],
                    y=future_only["yhat_lower"],
                    mode="lines",
                    fill="tonexty",
                    fillcolor="rgba(56, 189, 248, 0.18)",
                    line={"width": 0},
                    name="95% interval",
                )
            )
            fig_forecast.add_trace(
                go.Scatter(
                    x=future_only["ds"],
                    y=future_only["yhat"],
                    mode="lines",
                    name="Forecast",
                    line={"color": "#f59e0b", "width": 3},
                )
            )
            fig_forecast.update_layout(
                title="Daily Ridership Forecast",
                xaxis_title="Date",
                yaxis_title="Passengers",
            )
            st.plotly_chart(style_figure(fig_forecast, height=560), use_container_width=True)

            forecast_preview = future_only[["ds", "yhat", "yhat_lower", "yhat_upper"]].head(14)
            forecast_preview.columns = ["Date", "Prediction", "Lower Bound", "Upper Bound"]
            st.dataframe(forecast_preview, use_container_width=True, hide_index=True)
        except Exception as exc:
            st.error(f"Could not generate the Prophet forecast: {exc}")

with delay_tab:
    route_col, stop_col = st.columns(2)

    with st.spinner("Loading worst routes for delay..."):
        worst_routes = read_query(
            f"""
            SELECT
                COALESCE(NULLIF(r.route_name, ''), r.route_code) AS route,
                AVG(f.delay_minutes) AS avg_delay_minutes,
                SUM(f.passenger_count) AS total_passengers
            FROM fact_ridership f
            JOIN dim_date d ON f.date_id = d.date_id
            JOIN dim_route r ON f.route_id = r.route_id
            WHERE {filter_clause}
            GROUP BY route
            ORDER BY avg_delay_minutes DESC
            LIMIT 10
            """,
            filter_params,
        )

    with st.spinner("Loading worst stops for delay..."):
        worst_stops = read_query(
            f"""
            SELECT
                s.stop_name,
                AVG(f.delay_minutes) AS avg_delay_minutes,
                SUM(f.passenger_count) AS total_passengers
            FROM fact_ridership f
            JOIN dim_date d ON f.date_id = d.date_id
            JOIN dim_route r ON f.route_id = r.route_id
            JOIN dim_stop s ON f.stop_id = s.stop_id
            WHERE {filter_clause}
            GROUP BY s.stop_name
            ORDER BY avg_delay_minutes DESC
            LIMIT 10
            """,
            filter_params,
        )

    with route_col:
        st.markdown('<div class="section-title">Worst Routes by Average Delay</div>', unsafe_allow_html=True)
        if worst_routes.empty:
            st.info("No route delay records match the selected filters.")
        else:
            fig_worst_routes = px.bar(
                worst_routes.sort_values("avg_delay_minutes"),
                x="avg_delay_minutes",
                y="route",
                orientation="h",
                color="avg_delay_minutes",
                color_continuous_scale="OrRd",
                labels={"avg_delay_minutes": "Avg Delay (min)", "route": "Route"},
            )
            st.plotly_chart(style_figure(fig_worst_routes, height=500), use_container_width=True)

    with stop_col:
        st.markdown('<div class="section-title">Worst Stops by Average Delay</div>', unsafe_allow_html=True)
        if worst_stops.empty:
            st.info("No stop delay records match the selected filters.")
        else:
            fig_worst_stops = px.bar(
                worst_stops.sort_values("avg_delay_minutes"),
                x="avg_delay_minutes",
                y="stop_name",
                orientation="h",
                color="avg_delay_minutes",
                color_continuous_scale="OrRd",
                labels={"avg_delay_minutes": "Avg Delay (min)", "stop_name": "Stop"},
            )
            st.plotly_chart(style_figure(fig_worst_stops, height=500), use_container_width=True)
