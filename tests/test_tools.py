from app.tools.k8s_tools import get_pod_logs, restart_pod

def test_get_pod_logs_oom_detection():
    """Test if the tool correctly identifies OOM errors."""
    result = get_pod_logs.invoke({"pod_name": "payment-service-oom", "namespace": "prod"})
    assert "OOMKilled" in result
    assert "exit code 137" in result

def test_get_pod_logs_normal_detection():
    """Test if the tool correctly identifies normal status."""
    result = get_pod_logs.invoke({"pod_name": "user-service", "namespace": "prod"})
    assert "Normal operation" in result

def test_restart_pod():
    """Test the restart pod tool."""
    result = restart_pod.invoke({"pod_name": "test-pod", "namespace": "default"})
    assert "restarted successfully" in result