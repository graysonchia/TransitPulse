from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.schemas.responses import ForecastPoint

router = APIRouter(prefix="/api/forecast", tags=["forecast"])


@router.get("/ridership", response_model=list[ForecastPoint])
async def forecast_ridership(
    days_ahead: int = Query(default=90, ge=1, le=365),
    route_type: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[ForecastPoint]:
    route_filter = "WHERE r.route_type = :route_type" if route_type is not None else ""
    params = {"route_type": route_type} if route_type is not None else {}
    query = text(
        f"""
        SELECT
            d.full_date AS ds,
            SUM(f.passenger_count)::double precision AS y
        FROM fact_ridership f
        JOIN dim_date d ON f.date_id = d.date_id
        JOIN dim_route r ON f.route_id = r.route_id
        {route_filter}
        GROUP BY d.full_date
        ORDER BY d.full_date
        """
    )
    result = await db.execute(query, params)
    rows = result.mappings().all()
    if len(rows) < 30:
        raise HTTPException(status_code=400, detail="Not enough data for forecast")

    from prophet import Prophet

    history = pd.DataFrame(rows, columns=["ds", "y"])
    history["ds"] = pd.to_datetime(history["ds"])
    history["y"] = history["y"].astype(float)

    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
    )
    model.fit(history)
    future = model.make_future_dataframe(periods=days_ahead, freq="D")
    prediction = model.predict(future)[["ds", "yhat", "yhat_lower", "yhat_upper"]]

    last_history_date = history["ds"].max()
    prediction["is_forecast"] = prediction["ds"] > last_history_date
    historical_start = max(0, len(history) - 180)
    first_returned_date = history.iloc[historical_start]["ds"]
    response_frame = prediction[prediction["ds"] >= first_returned_date].copy()

    return [
        ForecastPoint(
            date=row.ds.strftime("%Y-%m-%d"),
            yhat=float(row.yhat),
            yhat_lower=float(row.yhat_lower),
            yhat_upper=float(row.yhat_upper),
            is_forecast=bool(row.is_forecast),
        )
        for row in response_frame.itertuples(index=False)
    ]
