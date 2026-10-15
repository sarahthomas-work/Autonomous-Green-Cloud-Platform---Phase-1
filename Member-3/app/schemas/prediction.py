from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.automation import AutomationJob
from app.schemas.rule import ThresholdRule


class PredictionRequest(BaseModel):
    node_id: str = Field(
        ...,
        description="Unique identifier of the monitored compute node",
        examples=["node-01"],
    )
    values: List[float] = Field(
        ...,
        min_length=60,
        description="Historical values used by the LSTM model. At least 60 values are required.",
        examples=[[10.5, 12.3, 15.7]],
    )
    rule: Optional[ThresholdRule] = Field(
        default=None,
        description="Optional threshold rule to evaluate against the predicted value.",
    )


class PredictionResponse(BaseModel):
    predicted_value: float
    input_values: int
    optimization_recommendation: str
    threshold_evaluation: Optional[dict] = None
    automation_job: Optional[AutomationJob] = None

class LivePredictionRequest(BaseModel):
    node_id: str = Field(
        ...,
        description="Node/instance identifier from Member 1 telemetry",
        examples=["10.0.1.10:9100"],
    )

    rule: Optional[ThresholdRule] = Field(
        default=None,
        description="Optional threshold rule to evaluate against the predicted CPU utilization.",
    )