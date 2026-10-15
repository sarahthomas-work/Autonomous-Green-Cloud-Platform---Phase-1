from fastapi import APIRouter, HTTPException, status

from app.schemas.decision import DecisionRequest
from app.services.decision_service import decision_service


router = APIRouter(
    prefix="/api/v1/rules",
    tags=["Decision Engine"],
)


@router.post(
    "/evaluate",
    summary="Evaluate a threshold rule and trigger automation",
)
def evaluate_rule(request: DecisionRequest):
    """
    Evaluate a threshold-based rule against telemetry data.

    If the rule matches, an automation job is created with
    PENDING status.
    """

    try:
        return decision_service.evaluate_and_trigger(
            telemetry=request.telemetry,
            rule=request.rule,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )