import os
import sys
import io
import json
from pathlib import Path
from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer
from kubernetes import client, config
from kubernetes.client.exceptions import ApiException # 🚨 Add this import

# Force UTF-8 encoding for stdin/stdout/stderr (Fixes Windows GBK issues)
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')

# ==========================================
# 🚨 Key Update: Load .env from the project root
# ==========================================
# Get the current file's parent directory's parent (i.e., the project root)
ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"

# Explicitly load the .env file
load_dotenv(dotenv_path=ENV_PATH)

# Get the path from environment variables; fallback to the default user directory
KUBECONFIG_PATH = os.getenv("KUBECONFIG_PATH", os.path.expanduser("~/.kube/config"))

mcp = MCPServer("KubernetesTools")

def _load_k8s_config():
    """Load Kubernetes configuration."""
    kube_path = Path(KUBECONFIG_PATH)
    
    # If the path in .env is relative, resolve it based on the project root
    if not kube_path.is_absolute():
        kube_path = ROOT_DIR / kube_path

    if kube_path.exists():
        print(f"[K8s Config] Loading kubeconfig from: {kube_path}")
        config.load_kube_config(config_file=str(kube_path))
    else:
        try:
            # Fallback for running inside a K8s Pod
            config.load_incluster_config()
        except config.ConfigException:
            raise RuntimeError(f"❌ Kubeconfig file not found at: {kube_path}")

@mcp.tool()
def get_pod_events(pod_name: str, namespace: str = "default") -> str:
    """Get Kubernetes events related to a specific Pod (useful for ImagePullBackOff or CrashLoopBackOff)."""
    try:
        _load_k8s_config()
        v1 = client.CoreV1Api()
        # Fetch events matching the pod name
        events = v1.list_namespaced_event(
            namespace=namespace,
            field_selector=f"involvedObject.name={pod_name}"
        )
        
        if not events.items:
            return f"No events found for pod {pod_name}."
            
        result = []
        for event in events.items:
            result.append(f"[{event.type}] {event.reason}: {event.message}")
            
        return "\n".join(result)
    except ApiException as e:
        return f"K8s API Error: {e.reason}"
    except Exception as e:
        return f"Failed to fetch events: {str(e)}"

@mcp.tool()
def list_failed_pods(namespace: str = "default") -> str:
    """List pods that are not in 'Running' or 'Succeeded' state."""
    try:
        _load_k8s_config()
        v1 = client.CoreV1Api()
        pods = v1.list_namespaced_pod(namespace=namespace)
        failed = [
            f"{p.metadata.name} ({p.status.phase})"
            for p in pods.items
            if p.status.phase not in ("Running", "Succeeded")
        ]
        return "\n".join(failed) if failed else "All pods are in Running state."
    except Exception as e:
        return f"Failed to query pods: {e}"

if __name__ == "__main__":
    mcp.run()