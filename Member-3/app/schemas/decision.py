from pydantic import BaseModel

from app.schemas.rule import ThresholdRule
from app.schemas.telemetry import TelemetryData


class DecisionRequest(BaseModel):
    telemetry: TelemetryData
    rule: ThresholdRule