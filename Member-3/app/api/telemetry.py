from typing import List

import httpx
from fastapi import APIRouter, HTTPException, status

from app.schemas.telemetry import TelemetryData
from app.services.prometheus_service import prometheus_service
from app.services.telemetry_service import telemetry_service


router = APIRouter(
    prefix="/api/v1/telemetry",
    tags=["Telemetry"],
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=TelemetryData,
    summary="Ingest telemetry data",
)
def ingest_telemetry(telemetry: TelemetryData):
    """
    Receive and validate telemetry data collected from
    monitored cloud infrastructure.
    """
    return telemetry_service.ingest(telemetry)


@router.get(
    "",
    response_model=List[TelemetryData],
    summary="Get all telemetry data",
)
def get_all_telemetry():
    """
    Return all telemetry observations currently held
    by the telemetry service.
    """
    return telemetry_service.get_all()


@router.get(
    "/prometheus",
    summary="Query Prometheus telemetry",
)
async def query_prometheus(promql: str):
    """
    Execute a PromQL query against the configured Prometheus server.
    """
    try:
        return await prometheus_service.query(promql)

    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Prometheus service unavailable: {exc}",
        )


@router.get(
    "/prometheus/normalized",
    response_model=TelemetryData,
    summary="Get normalized telemetry from Prometheus",
)
async def get_normalized_prometheus_telemetry(
    node_id: str = "node-01",
    region: str = "region-a",
):
    """
    Query Prometheus for standard Node Exporter metrics and
    convert them into the platform's normalized TelemetryData model.
    """

    try:
        cpu_usage = await prometheus_service.query_value(
            '100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'
        )

        memory_usage = await prometheus_service.query_value(
            '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100'
        )

        disk_usage = await prometheus_service.query_value(
            '(1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100'
        )

        network_in = await prometheus_service.query_value(
            'rate(node_network_receive_bytes_total[5m])'
        )

        network_out = await prometheus_service.query_value(
            'rate(node_network_transmit_bytes_total[5m])'
        )

        values = {
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "disk_usage": disk_usage,
            "network_in": network_in,
            "network_out": network_out,
        }

        missing_metrics = [
            name for name, value in values.items()
            if value is None
        ]

        if missing_metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "message": "Required Prometheus metrics were not found.",
                    "missing_metrics": missing_metrics,
                },
            )

        return TelemetryData(
            node_id=node_id,
            region=region,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_usage=disk_usage,
            network_in=network_in,
            network_out=network_out,
        )

    except HTTPException:
        raise

    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Prometheus service unavailable: {exc}",
        )


@router.get(
    "/{node_id}",
    response_model=List[TelemetryData],
    summary="Get telemetry for a node",
)
def get_node_telemetry(node_id: str):
    """
    Return telemetry observations for a specific compute node.
    """
    telemetry = telemetry_service.get_by_node(node_id)

    if not telemetry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No telemetry found for node '{node_id}'",
        )

    return telemetry