from app.schemas.rule import ThresholdRule
from app.schemas.telemetry import TelemetryData


class RuleEvaluationEngine:
    """
    Evaluates telemetry data against threshold-based rules.
    """

    def evaluate(
        self,
        telemetry: TelemetryData,
        rule: ThresholdRule,
    ) -> dict:
        """
        Compare the selected telemetry metric with the rule threshold.
        """

        metric_value = getattr(telemetry, rule.metric, None)

        if metric_value is None:
            return {
                "rule_id": rule.rule_id,
                "metric": rule.metric,
                "metric_value": None,
                "operator": rule.operator,
                "threshold": rule.threshold,
                "matched": False,
                "action": None,
                "reason": f"Metric '{rule.metric}' was not found in telemetry.",
            }

        matched = self._compare(
            metric_value,
            rule.operator,
            rule.threshold,
        )

        return {
            "rule_id": rule.rule_id,
            "metric": rule.metric,
            "metric_value": metric_value,
            "operator": rule.operator,
            "threshold": rule.threshold,
            "matched": matched,
            "action": rule.action if matched else None,
            "reason": (
                f"Rule matched: {metric_value} {rule.operator} {rule.threshold}"
                if matched
                else f"Rule not matched: {metric_value} {rule.operator} {rule.threshold}"
            ),
        }

    def _compare(
        self,
        value: float,
        operator: str,
        threshold: float,
    ) -> bool:
        """
        Perform the threshold comparison.
        """

        if operator == ">":
            return value > threshold

        if operator == ">=":
            return value >= threshold

        if operator == "<":
            return value < threshold

        if operator == "<=":
            return value <= threshold

        if operator == "==":
            return value == threshold

        raise ValueError(
            f"Unsupported operator: {operator}"
        )


rule_engine = RuleEvaluationEngine()