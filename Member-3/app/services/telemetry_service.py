from typing import Dict, List

from app.schemas.telemetry import TelemetryData


class TelemetryService:
    """
    Temporary in-memory telemetry service for Phase 1 Review 1.

    PostgreSQL/Redis persistence will be integrated separately
    as part of the database and data-flow work.
    """

    def __init__(self):
        self._telemetry: List[TelemetryData] = []

    def ingest(self, telemetry: TelemetryData) -> TelemetryData:
        self._telemetry.append(telemetry)
        return telemetry

    def get_all(self) -> List[TelemetryData]:
        return self._telemetry

    def get_by_node(self, node_id: str) -> List[TelemetryData]:
        return [
            item
            for item in self._telemetry
            if item.node_id == node_id
        ]


telemetry_service = TelemetryService()