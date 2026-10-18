import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client(mocker):
    # [FIX] Inject a Mock Graph into app.state to prevent AttributeError/KeyError
    # since the FastAPI lifespan is not triggered during unit tests.
    mock_graph = mocker.MagicMock()
    app.state.agent_graph = mock_graph
    return TestClient(app)

def test_health_check(client):
    """Verify the health check endpoint returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_prometheus_webhook(client, mocker):
    """Verify the webhook endpoint accepts the payload and returns accepted status."""
    # [FIX] Use new_callable=mocker.AsyncMock because process_alert is an async function.
    mocker.patch("app.api.webhook.process_alert", new_callable=mocker.AsyncMock)
    
    payload = {
        "status": "firing",
        "alerts": [
            {
                "fingerprint": "test-123",
                "annotations": {"summary": "Pod payment-service OOMKilled"}
            }
        ]
    }
    
    response = client.post("/api/v1/webhook/prometheus", json=payload)
    
    # Verify the API successfully receives the request and returns 200
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"