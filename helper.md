

```bash
git commit -m "feat(v0.2.0): integrate MCP v2, real K8s cluster, and HITL interrupts" -m "- Replace mock tools with a standalone MCP v2 Server (mcp_servers/k8s_server.py).
- Connect to real Kubernetes clusters using the official Python SDK and dynamic kubeconfig paths.
- Add 'get_pod_events' tool to assist the LLM in diagnosing ImagePullBackOff errors.
- Implement LangGraph dynamic 'interrupt()' in the approval node for high-risk actions (restart_pod).
- Create /api/v1/chat/approve endpoint to resume paused graph states via Command(resume=True/False).
- Fix frontend text rendering for LangChain's list-of-dicts content format.
- Format raw K8s ApiExceptions into clean, LLM-readable messages.

Closes #2"

git push origin 3-mvp-enterprise-safety-mcp
```

## tag

```bash
git tag -a v0.2.0 -m "Release v0.2.0: Enterprise Safety & MCP Integration" -m "- Integrated MCP v2 server for real K8s tool execution
- Added true Human-in-the-Loop (HITL) interrupts for high-risk actions
- Fixed frontend streaming rendering and K8s API error handling"

git push origin v0.2.0
```

## re-tag
```bash
# Delete locally (ignore error if it doesn't exist)
git tag -d v0.2.0

# Delete remotely (ignore error if it doesn't exist)
git push origin --delete v0.2.0

git tag -a v0.2.0 -m "Release v0.2.0: Enterprise Safety & MCP Integration" -m "- Replaced mock tools with a standalone MCP v2 Server for real Kubernetes execution.
- Implemented true Human-in-the-Loop (HITL) interrupts in LangGraph for high-risk actions.
- Added dynamic environment configurations (BACKEND_API_URL, KUBECONFIG_PATH).
- Enforced ASCII-only English logging and error handling for RHEL9/cross-platform compatibility."

git push origin v0.2.0
```
