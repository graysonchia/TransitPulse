from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.schemas.responses import DelayEntry

router = APIRouter(prefix="/api/delay", tags=["delay"])


class HourlyDelay(BaseModel):
    hour: int
    avg_delay_minutes: float


@router.get("/worst-routes", response_model=list[DelayEntry])
async def get_worst_routes(
    limit: int = Query(default=10, ge=1, le=100),
    year: Optional[int] = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[DelayEntry]:
    date_join = "JOIN dim_date d ON f.date_id = d.date_id" if year is not None else ""
    where_clause = "WHERE d.year = :year" if year is not None else ""
    params: dict[str, object] = {"limit": limit}
    if year is not None:
        params["year"] = year

    query = text(
        f"""
        SELECT
            COALESCE(NULLIF(r.route_name, ''), r.route_code) AS name,
            ROUND(AVG(f.delay_minutes)::numeric, 2) AS avg_delay_minutes,
            SUM(f.passenger_count) AS total_passengers
        FROM fact_ridership f
        JOIN dim_route r ON f.route_id = r.route_id
        {date_join}
        {where_clause}
        GROUP BY r.route_id, r.route_name, r.route_code
        ORDER BY avg_delay_minutes DESC
        LIMIT :limit
        """
    )
    result = await db.execute(query, params)
    return [DelayEntry(**row) for row in result.mappings().all()]


@router.get("/worst-stops", response_model=list[DelayEntry])
async def get_worst_stops(
    limit: int = Query(default=10, ge=1, le=100),
    year: Optional[int] = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[DelayEntry]:
    date_join = "JOIN dim_date d ON f.date_id = d.date_id" if year is not None else ""
    where_clause = "WHERE d.year = :year" if year is not None else ""
    params: dict[str, object] = {"limit": limit}
    if year is not None:
        params["year"] = year

    query = text(
        f"""
        SELECT
            s.stop_name AS name,
            ROUND(AVG(f.delay_minutes)::numeric, 2) AS avg_delay_minutes,
            SUM(f.passenger_count) AS total_passengers
        FROM fact_ridership f
        JOIN dim_stop s ON f.stop_id = s.stop_id
        {date_join}
        {where_clause}
        GROUP BY s.stop_id, s.stop_name
        ORDER BY avg_delay_minutes DESC
        LIMIT :limit
        """
    )
    result = await db.execute(query, params)
    return [DelayEntry(**row) for row in result.mappings().all()]


@router.get("/by-hour", response_model=list[HourlyDelay])
async def get_delay_by_hour(
    db: AsyncSession = Depends(get_db),
) -> list[HourlyDelay]:
    query = text(
        """
        SELECT
            t.hour,
            ROUND(AVG(f.delay_minutes)::numeric, 2) AS avg_delay_minutes
        FROM fact_ridership f
        JOIN dim_time t ON f.time_id = t.time_id
        GROUP BY t.hour
        ORDER BY t.hour
        """
    )
    result = await db.execute(query)
    return [HourlyDelay(**row) for row in result.mappings().all()]
