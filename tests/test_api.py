import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client(mocker):
    # [FIX] 给 app.state 注入一个 Mock Graph，防止未执行 lifespan 导致 AttributeError/KeyError
    mock_graph = mocker.MagicMock()
    app.state.agent_graph = mock_graph
    return TestClient(app)

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_prometheus_webhook(client, mocker):
    # [FIX] 必须使用 new_callable=mocker.AsyncMock，因为 process_alert 是 async 函数
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
    
    # 验证 API 正常接收并返回
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"