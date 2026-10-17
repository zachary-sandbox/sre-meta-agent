import pytest
from app.tools.k8s_tools import get_pod_logs

def test_tool_oom_detection():
    """Test tool accurately identifies OOM exceptions."""
    log = get_pod_logs.invoke({"pod_name": "payment-service-oom", "namespace": "prod"})
    assert "OOMKilled" in log

def test_tool_normal_detection():
    """Test tool accurately identifies normal status."""
    log = get_pod_logs.invoke({"pod_name": "user-service-normal", "namespace": "prod"})
    assert "Normal operation" in log
