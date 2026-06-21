from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import delay, forecast, ml, ridership

app = FastAPI(title="TransitPulse API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ridership.router)
app.include_router(delay.router)
app.include_router(forecast.router)
app.include_router(ml.router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"status": "ok", "service": "TransitPulse API"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
