def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_prometheus_webhook(client):
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
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"