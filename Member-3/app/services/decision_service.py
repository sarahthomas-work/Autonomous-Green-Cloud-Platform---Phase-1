from app.schemas.rule import ThresholdRule
from app.schemas.telemetry import TelemetryData
from app.services.automation_service import automation_service
from app.services.rule_engine import rule_engine


class DecisionService:
    """
    Coordinates rule evaluation and automation job creation.

    A matched threshold rule results in a pending automation job.
    Actual automation execution is handled separately.
    """

    def evaluate_and_trigger(
        self,
        telemetry: TelemetryData,
        rule: ThresholdRule,
    ) -> dict:
        """
        Evaluate a rule against telemetry and create an automation
        job when the rule matches.
        """

        evaluation = rule_engine.evaluate(
            telemetry,
            rule,
        )

        job = None

        if evaluation["matched"]:
            job = automation_service.create_job(
                node_id=telemetry.node_id,
                action=rule.action,
                rule_id=rule.rule_id,
                reason=evaluation["reason"],
            )

        return {
            "evaluation": evaluation,
            "automation_job": job,
        }


decision_service = DecisionService()