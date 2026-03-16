from __future__ import annotations

from fastapi.testclient import TestClient

from near_gas_compare.app import create_app


def test_health() -> None:
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "near-gas-comparison-api"
