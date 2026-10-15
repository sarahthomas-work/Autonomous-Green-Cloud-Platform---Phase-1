from app.schemas.rule import ThresholdRule
from app.schemas.telemetry import TelemetryData
from app.services.decision_service import DecisionService


def create_telemetry(cpu_usage=90.0):
    return TelemetryData(
        node_id="decision-test-node",
        region="region-a",
        cpu_usage=cpu_usage,
        memory_usage=70.0,
        disk_usage=40.0,
        network_in=500.0,
        network_out=400.0,
    )


def test_matched_rule_creates_automation_job():
    service = DecisionService()

    telemetry = create_telemetry(cpu_usage=90.0)

    rule = ThresholdRule(
        rule_id="cpu-high",
        metric="cpu_usage",
        operator=">",
        threshold=80.0,
        action="SCALE_UP",
    )

    result = service.evaluate_and_trigger(
        telemetry,
        rule,
    )

    assert result["evaluation"]["matched"] is True

    job = result["automation_job"]

    assert job is not None
    assert job.node_id == "decision-test-node"
    assert job.action == "SCALE_UP"
    assert job.rule_id == "cpu-high"
    assert job.status == "PENDING"


def test_unmatched_rule_does_not_create_automation_job():
    service = DecisionService()

    telemetry = create_telemetry(cpu_usage=60.0)

    rule = ThresholdRule(
        rule_id="cpu-high",
        metric="cpu_usage",
        operator=">",
        threshold=80.0,
        action="SCALE_UP",
    )

    result = service.evaluate_and_trigger(
        telemetry,
        rule,
    )

    assert result["evaluation"]["matched"] is False
    assert result["automation_job"] is None