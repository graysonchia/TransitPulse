from pydantic import BaseModel


class KPISummary(BaseModel):
    total_passengers: int
    total_trips: int
    avg_delay_minutes: float
    active_routes: int
    active_stops: int


class DailyRidership(BaseModel):
    full_date: str
    total_passengers: int
    trip_count: int
    avg_delay: float


class RouteRidership(BaseModel):
    route: str
    route_type: str
    total_passengers: int


class HeatmapCell(BaseModel):
    weekday: str
    hour: int
    total_passengers: int


class DelayEntry(BaseModel):
    name: str
    avg_delay_minutes: float
    total_passengers: int


class ForecastPoint(BaseModel):
    date: str
    yhat: float
    yhat_lower: float
    yhat_upper: float
    is_forecast: bool


class AnomalyDay(BaseModel):
    full_date: str
    total_passengers: int
    avg_delay: float
    anomaly_score: float


class StopCluster(BaseModel):
    stop_id: int
    stop_name: str
    cluster: int
    cluster_label: str
    total_passengers: int
    avg_delay: float


class ClusterProfile(BaseModel):
    cluster_label: str
    stop_count: int
    avg_passengers: float
    avg_delay: float
