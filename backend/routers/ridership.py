from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.schemas.responses import (
    DailyRidership,
    HeatmapCell,
    KPISummary,
    RouteRidership,
)

router = APIRouter(prefix="/api/ridership", tags=["ridership"])


@router.get("/summary", response_model=KPISummary)
async def get_summary(
    route_type: Optional[str] = Query(default=None),
    is_weekend: Optional[bool] = Query(default=None),
    year: Optional[int] = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> KPISummary:
    joins: list[str] = []
    filters: list[str] = []
    params: dict[str, object] = {}

    if route_type is not None:
        joins.append("JOIN dim_route r ON f.route_id = r.route_id")
        filters.append("r.route_type = :route_type")
        params["route_type"] = route_type

    if is_weekend is not None or year is not None:
        joins.append("JOIN dim_date d ON f.date_id = d.date_id")
    if is_weekend is not None:
        filters.append("d.is_weekend = :is_weekend")
        params["is_weekend"] = is_weekend
    if year is not None:
        filters.append("d.year = :year")
        params["year"] = year

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    query = text(
        f"""
        SELECT
            COALESCE(SUM(f.passenger_count), 0) AS total_passengers,
            COUNT(f.ridership_id) AS total_trips,
            COALESCE(ROUND(AVG(f.delay_minutes)::numeric, 2), 0) AS avg_delay_minutes,
            COUNT(DISTINCT f.route_id) AS active_routes,
            COUNT(DISTINCT f.stop_id) AS active_stops
        FROM fact_ridership f
        {' '.join(joins)}
        {where_clause}
        """
    )
    result = await db.execute(query, params)
    row = result.mappings().one()
    return KPISummary(**row)


@router.get("/daily", response_model=list[DailyRidership])
async def get_daily_ridership(
    route_type: Optional[str] = Query(default=None),
    year: int = Query(default_factory=lambda: datetime.utcnow().year),
    db: AsyncSession = Depends(get_db),
) -> list[DailyRidership]:
    route_filter = "AND r.route_type = :route_type" if route_type is not None else ""
    params: dict[str, object] = {"year": year}
    if route_type is not None:
        params["route_type"] = route_type

    query = text(
        f"""
        SELECT
            d.full_date::text AS full_date,
            SUM(f.passenger_count) AS total_passengers,
            COUNT(*) AS trip_count,
            ROUND(AVG(f.delay_minutes)::numeric, 2) AS avg_delay
        FROM fact_ridership f
        JOIN dim_date d ON f.date_id = d.date_id
        JOIN dim_route r ON f.route_id = r.route_id
        WHERE d.year = :year
        {route_filter}
        GROUP BY d.full_date
        ORDER BY d.full_date
        """
    )
    result = await db.execute(query, params)
    return [DailyRidership(**row) for row in result.mappings().all()]


@router.get("/by-route", response_model=list[RouteRidership])
async def get_ridership_by_route(
    year: int = Query(default_factory=lambda: datetime.utcnow().year),
    db: AsyncSession = Depends(get_db),
) -> list[RouteRidership]:
    query = text(
        """
        SELECT
            COALESCE(NULLIF(r.route_name, ''), r.route_code) AS route,
            r.route_type,
            SUM(f.passenger_count) AS total_passengers
        FROM fact_ridership f
        JOIN dim_route r ON f.route_id = r.route_id
        JOIN dim_date d ON f.date_id = d.date_id
        WHERE d.year = :year
        GROUP BY route, r.route_type
        ORDER BY total_passengers DESC
        """
    )
    result = await db.execute(query, {"year": year})
    return [RouteRidership(**row) for row in result.mappings().all()]


@router.get("/heatmap", response_model=list[HeatmapCell])
async def get_ridership_heatmap(
    route_type: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[HeatmapCell]:
    where_clause = "WHERE r.route_type = :route_type" if route_type is not None else ""
    params = {"route_type": route_type} if route_type is not None else {}
    query = text(
        f"""
        SELECT
            d.weekday,
            t.hour,
            SUM(f.passenger_count) AS total_passengers
        FROM fact_ridership f
        JOIN dim_date d ON f.date_id = d.date_id
        JOIN dim_time t ON f.time_id = t.time_id
        JOIN dim_route r ON f.route_id = r.route_id
        {where_clause}
        GROUP BY d.weekday, t.hour
        ORDER BY t.hour
        """
    )
    result = await db.execute(query, params)
    return [HeatmapCell(**row) for row in result.mappings().all()]
