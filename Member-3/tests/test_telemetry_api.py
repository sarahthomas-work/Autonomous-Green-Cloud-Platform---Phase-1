from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"
    assert data["service"] == "AGCP FastAPI Backend"


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Autonomous Green Cloud Platform API"
    assert data["docs"] == "/docs"
    assert data["health"] == "/health"


def test_ingest_telemetry():
    payload = {
        "node_id": "test-node-01",
        "region": "region-a",
        "cpu_usage": 65.5,
        "memory_usage": 70.2,
        "disk_usage": 45.8,
        "network_in": 1000.0,
        "network_out": 800.0,
    }

    response = client.post(
        "/api/v1/telemetry",
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["node_id"] == "test-node-01"
    assert data["region"] == "region-a"
    assert data["cpu_usage"] == 65.5
    assert data["memory_usage"] == 70.2


def test_get_all_telemetry():
    payload = {
        "node_id": "test-node-02",
        "region": "region-b",
        "cpu_usage": 55.0,
        "memory_usage": 60.0,
        "disk_usage": 40.0,
        "network_in": 500.0,
        "network_out": 400.0,
    }

    client.post(
        "/api/v1/telemetry",
        json=payload,
    )

    response = client.get("/api/v1/telemetry")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert any(
        item["node_id"] == "test-node-02"
        for item in data
    )


def test_get_telemetry_by_node():
    payload = {
        "node_id": "test-node-03",
        "region": "region-c",
        "cpu_usage": 50.0,
        "memory_usage": 55.0,
        "disk_usage": 35.0,
        "network_in": 300.0,
        "network_out": 250.0,
    }

    client.post(
        "/api/v1/telemetry",
        json=payload,
    )

    response = client.get(
        "/api/v1/telemetry/test-node-03"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 1
    assert data[0]["node_id"] == "test-node-03"


def test_unknown_node_returns_404():
    response = client.get(
        "/api/v1/telemetry/non-existent-node"
    )

    assert response.status_code == 404


def test_invalid_cpu_value_rejected():
    payload = {
        "node_id": "invalid-node",
        "region": "region-a",
        "cpu_usage": 150.0,
        "memory_usage": 50.0,
        "disk_usage": 40.0,
        "network_in": 100.0,
        "network_out": 100.0,
    }

    response = client.post(
        "/api/v1/telemetry",
        json=payload,
    )

    assert response.status_code == 422