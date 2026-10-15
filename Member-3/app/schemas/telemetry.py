from datetime import datetime, timezone

from pydantic import BaseModel, Field


class TelemetryData(BaseModel):
    node_id: str = Field(
        ...,
        description="Unique identifier of the monitored compute node",
        examples=["node-01"],
    )

    region: str = Field(
        ...,
        description="Cloud region where the node is running",
        examples=["region-a"],
    )

    cpu_usage: float = Field(
        ...,
        ge=0,
        le=100,
        description="CPU utilization percentage",
        examples=[67.5],
    )

    memory_usage: float = Field(
        ...,
        ge=0,
        le=100,
        description="Memory utilization percentage",
        examples=[72.1],
    )

    disk_usage: float = Field(
        ...,
        ge=0,
        le=100,
        description="Disk utilization percentage",
        examples=[48.3],
    )

    network_in: float = Field(
        ...,
        ge=0,
        description="Incoming network traffic",
        examples=[1250.4],
    )

    network_out: float = Field(
        ...,
        ge=0,
        description="Outgoing network traffic",
        examples=[842.7],
    )

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the telemetry observation",
    )