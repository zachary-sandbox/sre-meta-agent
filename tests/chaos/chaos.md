## Deploy a crashing pod for testing mcp

```bash
# Create an OOM pod
kubectl run oom-pod --image=busybox --limits=memory=10Mi --restart=Never -- sh -c "sleep 3600"
kubectl run payment-service-oom --image=busybox --restart=Never -- sh -c "sleep 3600"
# Or deploy a crashing pod
kubectl run crash-pod --image=busybox --limits=memory=10Mi 

# Create a restart-demo
kubectl create deploy restart-demo --image=nginx 

# Start MCP Inspector
mcp dev mcp_servers/k8s_server.py
```

## Clear all
```bash
kubectl delete pod/oom-pod
kubectl delete pod/crash-pod
kubectl delete deploy/restart-demo
```
