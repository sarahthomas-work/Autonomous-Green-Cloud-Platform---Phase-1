import numpy as np

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_prediction_api_without_rule():
    values = np.linspace(10, 90, 60).tolist()

    payload = {
        "node_id": "prediction-node-01",
        "values": values,
    }

    response = client.post(
        "/api/v1/predict",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data["predicted_value"], float)
    assert data["input_values"] == 60
    assert data["threshold_evaluation"] is None
    assert data["automation_job"] is None


def test_prediction_api_triggers_automation():
    values = np.linspace(10, 90, 60).tolist()

    payload = {
        "node_id": "prediction-node-02",
        "values": values,
        "rule": {
            "rule_id": "predicted-high-test",
            "metric": "predicted_value",
            "operator": ">",
            "threshold": 0,
            "action": "SCALE_UP",
        },
    }

    response = client.post(
        "/api/v1/predict",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["threshold_evaluation"]["matched"] is True
    assert data["threshold_evaluation"]["metric"] == "predicted_value"
    assert data["threshold_evaluation"]["action"] == "SCALE_UP"

    assert data["automation_job"] is not None
    assert data["automation_job"]["node_id"] == "prediction-node-02"
    assert data["automation_job"]["action"] == "SCALE_UP"
    assert data["automation_job"]["status"] == "PENDING"


def test_prediction_api_does_not_trigger_automation():
    values = np.linspace(10, 90, 60).tolist()

    payload = {
        "node_id": "prediction-node-03",
        "values": values,
        "rule": {
            "rule_id": "predicted-high-test",
            "metric": "predicted_value",
            "operator": ">",
            "threshold": 1000,
            "action": "SCALE_UP",
        },
    }

    response = client.post(
        "/api/v1/predict",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["threshold_evaluation"]["matched"] is False
    assert data["threshold_evaluation"]["action"] is None
    assert data["automation_job"] is None


def test_prediction_api_rejects_less_than_60_values():
    values = np.linspace(10, 50, 59).tolist()

    payload = {
        "node_id": "prediction-node-04",
        "values": values,
    }

    response = client.post(
        "/api/v1/predict",
        json=payload,
    )

    assert response.status_code == 422


def test_prediction_api_rejects_invalid_rule_metric():
    values = np.linspace(10, 90, 60).tolist()

    payload = {
        "node_id": "prediction-node-05",
        "values": values,
        "rule": {
            "rule_id": "invalid-metric-test",
            "metric": "cpu_usage",
            "operator": ">",
            "threshold": 80,
            "action": "SCALE_UP",
        },
    }

    response = client.post(
        "/api/v1/predict",
        json=payload,
    )

    assert response.status_code == 400
    assert "predicted_value" in response.json()["detail"]