from app.schemas.rule import ThresholdRule
from app.schemas.telemetry import TelemetryData
from app.services.rule_engine import rule_engine


def create_telemetry(cpu_usage=90.0, memory_usage=70.0):
    return TelemetryData(
        node_id="test-node",
        region="region-a",
        cpu_usage=cpu_usage,
        memory_usage=memory_usage,
        disk_usage=40.0,
        network_in=500.0,
        network_out=400.0,
    )


def test_cpu_above_threshold_triggers_action():
    telemetry = create_telemetry(cpu_usage=90.0)

    rule = ThresholdRule(
        rule_id="cpu-high",
        metric="cpu_usage",
        operator=">",
        threshold=80.0,
        action="SCALE_UP",
    )

    result = rule_engine.evaluate(telemetry, rule)

    assert result["matched"] is True
    assert result["action"] == "SCALE_UP"
    assert result["metric_value"] == 90.0


def test_cpu_below_threshold_does_not_trigger_action():
    telemetry = create_telemetry(cpu_usage=70.0)

    rule = ThresholdRule(
        rule_id="cpu-high",
        metric="cpu_usage",
        operator=">",
        threshold=80.0,
        action="SCALE_UP",
    )

    result = rule_engine.evaluate(telemetry, rule)

    assert result["matched"] is False
    assert result["action"] is None


def test_memory_threshold_triggers_action():
    telemetry = create_telemetry(memory_usage=90.0)

    rule = ThresholdRule(
        rule_id="memory-high",
        metric="memory_usage",
        operator=">",
        threshold=85.0,
        action="SCALE_UP",
    )

    result = rule_engine.evaluate(telemetry, rule)

    assert result["matched"] is True
    assert result["action"] == "SCALE_UP"


def test_invalid_metric_does_not_trigger_action():
    telemetry = create_telemetry()

    rule = ThresholdRule(
        rule_id="invalid-rule",
        metric="unknown_metric",
        operator=">",
        threshold=80.0,
        action="SCALE_UP",
    )

    result = rule_engine.evaluate(telemetry, rule)

    assert result["matched"] is False
    assert result["action"] is None