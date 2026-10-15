from fastapi import APIRouter, HTTPException, status

from app.schemas.prediction import (
    PredictionRequest,
    PredictionResponse,
    LivePredictionRequest,
)
from app.services.automation_service import automation_service
from app.services.prediction_service import prediction_service
from app.services.live_prediction_service import live_prediction_service


router = APIRouter(
    prefix="/api/v1/predict",
    tags=["Prediction"],
)


@router.post(
    "",
    response_model=PredictionResponse,
    summary="Generate an LSTM prediction",
)
def predict(request: PredictionRequest):
    """
    Generate an LSTM prediction and optionally evaluate it
    against a threshold rule.

    When the prediction crosses the configured threshold,
    a pending automation job is created.
    """

    try:
        predicted_value = prediction_service.predict(
            request.values
        )

        # Generate optimization recommendation
        if predicted_value >= 80:
            recommendation = (
                "High predicted resource utilization. "
                "Consider scaling or optimizing resource allocation."
            )
        else:
            recommendation = (
                "Predicted resource utilization is within "
                "the normal operating range."
            )

        threshold_evaluation = None
        automation_job = None

        # Evaluate prediction against optional rule
        if request.rule is not None:
            rule = request.rule

            if rule.metric != "predicted_value":
                raise ValueError(
                    "Prediction rules must use metric 'predicted_value'."
                )

            if rule.operator == ">":
                matched = predicted_value > rule.threshold
            elif rule.operator == ">=":
                matched = predicted_value >= rule.threshold
            elif rule.operator == "<":
                matched = predicted_value < rule.threshold
            elif rule.operator == "<=":
                matched = predicted_value <= rule.threshold
            elif rule.operator == "==":
                matched = predicted_value == rule.threshold
            else:
                raise ValueError(
                    f"Unsupported operator: {rule.operator}"
                )

            threshold_evaluation = {
                "rule_id": rule.rule_id,
                "metric": rule.metric,
                "metric_value": predicted_value,
                "operator": rule.operator,
                "threshold": rule.threshold,
                "matched": matched,
                "action": rule.action if matched else None,
                "reason": (
                    f"Prediction rule matched: "
                    f"{predicted_value} {rule.operator} {rule.threshold}"
                    if matched
                    else
                    f"Prediction rule not matched: "
                    f"{predicted_value} {rule.operator} {rule.threshold}"
                ),
            }

            # Trigger automation when threshold is matched
            if matched:
                automation_job = automation_service.create_job(
                    node_id=request.node_id,
                    action=rule.action,
                    rule_id=rule.rule_id,
                    reason=threshold_evaluation["reason"],
                )

        return PredictionResponse(
            predicted_value=predicted_value,
            input_values=len(request.values),
            optimization_recommendation=recommendation,
            threshold_evaluation=threshold_evaluation,
            automation_job=automation_job,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
@router.post("/live", response_model=PredictionResponse, summary="Generate prediction from live telemetry")
def predict_live(request: LivePredictionRequest):
    try:
        values = live_prediction_service.get_cpu_history(request.node_id)

        predicted_value = prediction_service.predict(values)

        if predicted_value >= 80:
            recommendation = (
                "High predicted resource utilization. "
                "Consider scaling or optimizing resource allocation."
            )
        else:
            recommendation = (
                "Predicted resource utilization is within "
                "the normal operating range."
            )

        threshold_evaluation = None
        automation_job = None

        if request.rule is not None:
            rule = request.rule

            if rule.metric != "predicted_value":
                raise ValueError(
                    "Prediction rules must use metric 'predicted_value'."
                )

            if rule.operator == ">":
                matched = predicted_value > rule.threshold
            elif rule.operator == ">=":
                matched = predicted_value >= rule.threshold
            elif rule.operator == "<":
                matched = predicted_value < rule.threshold
            elif rule.operator == "<=":
                matched = predicted_value <= rule.threshold
            elif rule.operator == "==":
                matched = predicted_value == rule.threshold
            else:
                raise ValueError(
                    f"Unsupported operator: {rule.operator}"
                )

            threshold_evaluation = {
                "rule_id": rule.rule_id,
                "metric": rule.metric,
                "metric_value": predicted_value,
                "operator": rule.operator,
                "threshold": rule.threshold,
                "matched": matched,
                "action": rule.action if matched else None,
                "reason": (
                    f"Prediction rule matched: "
                    f"{predicted_value} {rule.operator} {rule.threshold}"
                    if matched
                    else
                    f"Prediction rule not matched: "
                    f"{predicted_value} {rule.operator} {rule.threshold}"
                ),
            }

            if matched:
                automation_job = automation_service.create_job(
                    node_id=request.node_id,
                    action=rule.action,
                    rule_id=rule.rule_id,
                    reason=threshold_evaluation["reason"],
                )

        return PredictionResponse(
            predicted_value=predicted_value,
            input_values=len(values),
            optimization_recommendation=recommendation,
            threshold_evaluation=threshold_evaluation,
            automation_job=automation_job,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )