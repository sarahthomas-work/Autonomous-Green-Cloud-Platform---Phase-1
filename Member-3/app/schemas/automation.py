from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class AutomationJob(BaseModel):
    job_id: str = Field(
        ...,
        description="Unique identifier of the automation job",
        examples=["job-001"],
    )

    node_id: str = Field(
        ...,
        description="Node on which the automation action is requested",
        examples=["demo-node-01"],
    )

    action: str = Field(
        ...,
        description="Automation action to perform",
        examples=["SCALE_UP"],
    )

    rule_id: str = Field(
        ...,
        description="Rule that triggered the automation job",
        examples=["cpu-high"],
    )

    status: str = Field(
        default="PENDING",
        description="Current status of the automation job",
        examples=["PENDING"],
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC time when the job was created",
    )

    reason: Optional[str] = Field(
        default=None,
        description="Reason why the automation job was created",
        examples=["CPU usage exceeded the configured threshold"],
    )