from pydantic import BaseModel, Field


class ThresholdRule(BaseModel):
    rule_id: str = Field(
        ...,
        description="Unique identifier of the rule",
        examples=["cpu-high"],
    )

    metric: str = Field(
        ...,
        description="Telemetry metric to evaluate",
        examples=["cpu_usage"],
    )

    operator: str = Field(
        ...,
        description="Comparison operator",
        examples=[">"],
    )

    threshold: float = Field(
        ...,
        description="Threshold value used for rule evaluation",
        examples=[80.0],
    )

    action: str = Field(
        ...,
        description="Automation action to trigger when the rule matches",
        examples=["SCALE_UP"],
    )