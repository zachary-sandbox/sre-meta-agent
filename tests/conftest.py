import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    """Provides a FastAPI TestClient for API tests."""
    with TestClient(app) as c:
        yield c