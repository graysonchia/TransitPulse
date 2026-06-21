from pathlib import Path

import joblib
import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from backend.schemas.responses import AnomalyDay, ClusterProfile, StopCluster

router = APIRouter(prefix="/api/ml", tags=["machine-learning"])

MODELS_DIR = Path(__file__).parent.parent.parent / "models"
ANOMALY_PATH = MODELS_DIR / "anomaly_results.csv"
CLUSTERS_PATH = MODELS_DIR / "stop_clusters.csv"

anomaly_df = pd.read_csv(ANOMALY_PATH) if ANOMALY_PATH.exists() else pd.DataFrame()
clusters_df = pd.read_csv(CLUSTERS_PATH) if CLUSTERS_PATH.exists() else pd.DataFrame()


def _require_data(frame: pd.DataFrame, filename: str) -> None:
    if frame.empty:
        raise HTTPException(
            status_code=503,
            detail=f"{filename} is missing or empty. Run the corresponding notebook first.",
        )


@router.get("/anomalies", response_model=list[AnomalyDay])
async def get_anomalies(
    limit: int = Query(default=50, ge=1, le=1000),
    min_score: float = Query(default=0.0),
) -> list[AnomalyDay]:
    _require_data(anomaly_df, ANOMALY_PATH.name)
    filtered = (
        anomaly_df[anomaly_df["anomaly_score"] >= min_score]
        .sort_values("anomaly_score", ascending=False)
        .head(limit)
    )
    return [
        AnomalyDay(
            full_date=str(row.full_date),
            total_passengers=int(row.total_passengers),
            avg_delay=float(row.avg_delay),
            anomaly_score=float(row.anomaly_score),
        )
        for row in filtered.itertuples(index=False)
    ]


@router.get("/stop-clusters", response_model=list[StopCluster])
async def get_stop_clusters() -> list[StopCluster]:
    _require_data(clusters_df, CLUSTERS_PATH.name)
    return [
        StopCluster(
            stop_id=int(row.stop_id),
            stop_name=str(row.stop_name),
            cluster=int(row.cluster),
            cluster_label=str(row.cluster_label),
            total_passengers=int(row.total_passengers),
            avg_delay=float(row.avg_delay),
        )
        for row in clusters_df.itertuples(index=False)
    ]


@router.get("/cluster-profiles", response_model=list[ClusterProfile])
async def get_cluster_profiles() -> list[ClusterProfile]:
    _require_data(clusters_df, CLUSTERS_PATH.name)
    profiles = (
        clusters_df.groupby("cluster_label", as_index=False)
        .agg(
            stop_count=("stop_id", "count"),
            avg_passengers=("total_passengers", "mean"),
            avg_delay=("avg_delay", "mean"),
        )
        .sort_values("cluster_label")
    )
    return [
        ClusterProfile(
            cluster_label=str(row.cluster_label),
            stop_count=int(row.stop_count),
            avg_passengers=float(row.avg_passengers),
            avg_delay=float(row.avg_delay),
        )
        for row in profiles.itertuples(index=False)
    ]


def load_delay_classifier():
    model_path = MODELS_DIR / "delay_classifier.pkl"
    if not model_path.exists():
        raise HTTPException(status_code=503, detail=f"{model_path.name} is missing.")
    return joblib.load(model_path)


def load_stop_kmeans():
    model_path = MODELS_DIR / "stop_kmeans.pkl"
    if not model_path.exists():
        raise HTTPException(status_code=503, detail=f"{model_path.name} is missing.")
    return joblib.load(model_path)
