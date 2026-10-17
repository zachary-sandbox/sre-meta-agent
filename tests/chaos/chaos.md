## Deploy a crashing pod for testing mcp

```bash
# Create an OOM pod
kubectl run oom-pod --image=busybox --limits=memory=10Mi --restart=Never -- sh -c "sleep 3600"
# Or deploy a crashing pod
kubectl run crash-pod --image=busybox -- sh -c "exit 1"

# Start MCP Inspector
mcp dev mcp_servers/k8s_server.py
```
