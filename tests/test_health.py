"""Phase 0 acceptance: the app is up and /health returns 200."""
import fastapi.testclient
import pytest

import main


@pytest.fixture()
def client():
    return fastapi.testclient.TestClient(main.app)


def test_health_returns_200(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "woundwatch"


def test_openapi_docs_available(client):
    # FastAPI auto-generates OpenAPI; confirm the app is a proper FastAPI app.
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
