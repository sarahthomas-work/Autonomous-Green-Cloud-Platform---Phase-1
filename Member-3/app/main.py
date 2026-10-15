from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.rules import router as rules_router
from app.api.telemetry import router as telemetry_router
from app.api.prediction import router as prediction_router
from telemetry_pipeline import (
    router as member1_telemetry_router,
    start_poller,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_poller()
    yield
app = FastAPI(
    lifespan=lifespan,
    title="Autonomous Green Cloud Platform API",
    description=(
        "Core backend API for the Autonomous Green Cloud Platform (AGCP). "
        "The API provides telemetry ingestion, processing, "
        "and machine learning prediction capabilities."
    ),
    version="1.0.0",
)


app.include_router(telemetry_router)
app.include_router(rules_router)
app.include_router(prediction_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "AGCP FastAPI Backend",
        "version": "1.0.0",
    }


@app.get("/", tags=["Health"])
def root():
    return {
        "message": "Autonomous Green Cloud Platform API",
        "docs": "/docs",
        "health": "/health",
    }
app.include_router(member1_telemetry_router)