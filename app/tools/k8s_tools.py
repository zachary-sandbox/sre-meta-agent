from langchain_core.tools import tool
import time

@tool
def get_pod_logs(pod_name: str, namespace: str = "default") -> str:
    """Retrieve K8s logs for a specific Pod and namespace."""
    time.sleep(0.5)  # Simulate network latency
    if "error" in pod_name.lower() or "oom" in pod_name.lower():
        return f"Error logs for {pod_name} in {namespace}:\n[ERROR] Java heap space. Container exited with code 137 (OOMKilled)."
    return f"Logs for {pod_name} in {namespace}: Normal operation."

@tool
def restart_pod(pod_name: str, namespace: str = "default") -> str:
    """Restart a specific Pod. HIGH RISK OPERATION."""
    time.sleep(1)
    return f"Pod {pod_name} in {namespace} restarted successfully."
