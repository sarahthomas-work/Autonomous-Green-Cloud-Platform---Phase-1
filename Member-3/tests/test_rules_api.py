from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def create_payload(cpu_usage):
    return {
        "telemetry": {
            "node_id": "api-test-node",
            "region": "region-a",
            "cpu_usage": cpu_usage,
            "memory_usage": 70.0,
            "disk_usage": 40.0,
            "network_in": 500.0,
            "network_out": 400.0,
        },
        "rule": {
            "rule_id": "cpu-high-api",
            "metric": "cpu_usage",
            "operator": ">",
            "threshold": 80.0,
            "action": "SCALE_UP",
        },
    }


def test_rule_api_creates_job_when_threshold_is_exceeded():
    response = client.post(
        "/api/v1/rules/evaluate",
        json=create_payload(cpu_usage=90.0),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["evaluation"]["matched"] is True
    assert data["evaluation"]["action"] == "SCALE_UP"

    assert data["automation_job"] is not None
    assert data["automation_job"]["action"] == "SCALE_UP"
    assert data["automation_job"]["rule_id"] == "cpu-high-api"
    assert data["automation_job"]["status"] == "PENDING"


def test_rule_api_does_not_create_job_when_threshold_is_not_exceeded():
    response = client.post(
        "/api/v1/rules/evaluate",
        json=create_payload(cpu_usage=60.0),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["evaluation"]["matched"] is False
    assert data["evaluation"]["action"] is None

    assert data["automation_job"] is None

def test_rule_api_rejects_unsupported_operator():
    payload = create_payload(cpu_usage=90.0)

    payload["rule"]["operator"] = "!="

    response = client.post(
        "/api/v1/rules/evaluate",
        json=payload,
    )

    assert response.status_code == 400