#!/bin/bash

PROJECT_NAME="sre-meta-agent"

echo "🚀 Initializing Enterprise-Grade AI Agent Platform (Factory Pattern): $PROJECT_NAME..."

if [ -d "$PROJECT_NAME" ]; then
    echo "❌ Error: Directory $PROJECT_NAME already exists. Please remove or rename it."
    exit 1
fi

mkdir -p $PROJECT_NAME
cd $PROJECT_NAME

# ==========================================
# 1. Create Directory Structure
# ==========================================
echo "📁 Creating directory structure..."
mkdir -p app/api
mkdir -p app/core
mkdir -p app/services
mkdir -p app/tools
mkdir -p app/schemas
mkdir -p tests/chaos
mkdir -p deploy

# ==========================================
# 2. Generate Config Files
# ==========================================
echo "📝 Generating config files..."

cat << 'EOF' > requirements.txt
fastapi>=0.115.0
uvicorn>=0.32.0
pydantic>=2.10.0
langgraph>=0.4.0
langgraph-checkpoint>=2.0.0
langchain-openai>=0.3.0
langchain-core>=0.3.0
langchain-anthropic>=0.2.0
langchain-deepseek>=0.1.0
langchain-ollama>=0.2.0
python-dotenv>=1.0.0
pytest>=7.4.0
pytest-asyncio>=0.21.1
httpx>=0.25.0
sse-starlette>=2.0.0
EOF

cat << 'EOF' > .env.example
# ==========================================
# LLM Configuration (Factory Pattern)
# ==========================================
# Options: openai, anthropic, deepseek, ollama
LLM_PROVIDER=openai
LLM_MODEL_NAME=gpt-4-turbo
LLM_TEMPERATURE=0

# API Keys (Fill in the one corresponding to your LLM_PROVIDER)
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-your-anthropic-key
DEEPSEEK_API_KEY=sk-your-deepseek-key

# If using a proxy or OpenAI-compatible endpoint
# OPENAI_API_BASE=https://api.your-proxy.com/v1

# If using Ollama locally
# OLLAMA_BASE_URL=http://localhost:11434
EOF

cat << 'EOF' > .gitignore
__pycache__/
*.py[cod]
.env
.venv/
.pytest_cache/
chaos_report.md
EOF

cat << 'EOF' > .condarc.example
# Copy this content to C:\Users\<YourUsername>\.condarc
show_channel_urls: true
default_channels:
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/r
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/msys2
custom_channels:
  conda-forge: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
  msys2: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
  bioconda: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
EOF

# ==========================================
# 3. Generate Application Code (app/)
# ==========================================
echo "📝 Generating application code..."

touch app/__init__.py app/api/__init__.py app/core/__init__.py app/services/__init__.py app/tools/__init__.py app/schemas/__init__.py
touch tests/__init__.py tests/chaos/__init__.py

# Schemas
cat << 'EOF' > app/schemas/payloads.py
from pydantic import BaseModel
from typing import Dict, Any, List

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default_session"

class ApprovalRequest(BaseModel):
    session_id: str
    tool_call_id: str
    approved: bool

class PrometheusAlert(BaseModel):
    status: str
    alerts: List[Dict[str, Any]]
EOF

# Services
cat << 'EOF' > app/services/prompts.py
SRE_SYSTEM_PROMPT = """You are a senior Kubernetes SRE Expert.
Your task is to help R&D personnel troubleshoot K8s cluster faults.
You have access to tools to retrieve Pod logs or execute restart operations.
Think step-by-step:
1. Identify the fault symptom (e.g., OOM, CrashLoopBackOff).
2. Call the get_pod_logs tool if necessary.
3. Analyze the logs, provide conclusions, and remediation advice.
Warning: If a high-risk operation (like restarting) is needed, explicitly prompt the user for approval."""
EOF

cat << 'EOF' > app/services/llm.py
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_deepseek import ChatDeepSeek
from langchain_ollama import ChatOllama

load_dotenv()

def get_llm(provider: str = None, model_name: str = None, **kwargs):
    """LLM Factory Function."""
    provider = (provider or os.getenv("LLM_PROVIDER", "openai")).lower()
    model_name = model_name or os.getenv("LLM_MODEL_NAME", "gpt-4-turbo")
    
    if "temperature" not in kwargs:
        kwargs["temperature"] = float(os.getenv("LLM_TEMPERATURE", 0))

    print(f"🔧 [LLM Factory] Initializing {provider} model: {model_name}")

    if provider == "openai":
        return ChatOpenAI(model=model_name, **kwargs)
    elif provider == "anthropic":
        return ChatAnthropic(model=model_name, **kwargs)
    elif provider == "deepseek":
        return ChatDeepSeek(model=model_name, **kwargs)
    elif provider == "ollama":
        return ChatOllama(model=model_name, **kwargs)
    else:
        raise ValueError(f"❌ Unsupported LLM Provider: {provider}")

llm = get_llm()
EOF

# Tools
cat << 'EOF' > app/tools/k8s_tools.py
from langchain_core.tools import tool
import time

@tool
def get_pod_logs(pod_name: str, namespace: str = "default") -> str:
    """Retrieve K8s logs for a specific Pod and namespace."""
    time.sleep(0.5)
    if "error" in pod_name.lower() or "oom" in pod_name.lower():
        return f"Error logs for {pod_name} in {namespace}:\n[ERROR] Java heap space. Container exited with code 137 (OOMKilled)."
    return f"Logs for {pod_name} in {namespace}: Normal operation."

@tool
def restart_pod(pod_name: str, namespace: str = "default") -> str:
    """Restart a specific Pod. HIGH RISK OPERATION."""
    time.sleep(1)
    return f"Pod {pod_name} in {namespace} restarted successfully."
EOF

# Core Graph
cat << 'EOF' > app/core/state.py
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    current_step: str
EOF

cat << 'EOF' > app/core/graph.py
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage, ToolMessage
from app.core.state import AgentState
from app.tools.k8s_tools import get_pod_logs, restart_pod
from app.services.prompts import SRE_SYSTEM_PROMPT
from app.services.llm import llm

tools = [get_pod_logs, restart_pod]
llm_with_tools = llm.bind_tools(tools)

def planner_node(state: AgentState):
    messages = state["messages"]
    system_msg = SystemMessage(content=SRE_SYSTEM_PROMPT)
    response = llm_with_tools.invoke([system_msg] + list(messages))
    return {"messages": [response]}

def tool_node(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    tool_messages = []
    
    for tool_call in last_message.tool_calls:
        if tool_call["name"] == "get_pod_logs":
            result = get_pod_logs.invoke(tool_call["args"])
        elif tool_call["name"] == "restart_pod":
            result = restart_pod.invoke(tool_call["args"])
        else:
            result = "Unknown tool"
        tool_messages.append(ToolMessage(tool_call_id=tool_call["id"], content=result))
    
    return {"messages": tool_messages}

def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("planner", planner_node)
    workflow.add_node("tools", tool_node)
    workflow.set_entry_point("planner")

    def should_continue(state: AgentState):
        last_message = state["messages"][-1]
        if getattr(last_message, "tool_calls", None):
            return "continue"
        return "end"

    workflow.add_conditional_edges("planner", should_continue, {"continue": "tools", "end": END})
    workflow.add_edge("tools", "planner")

    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)

sre_agent_app = build_graph()
EOF

# API Routers
cat << 'EOF' > app/api/chat.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.core.graph import sre_agent_app
from app.schemas.payloads import ChatRequest
from langchain_core.messages import HumanMessage
import json

router = APIRouter()

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    config = {"configurable": {"thread_id": request.session_id}}
    inputs = {"messages": [HumanMessage(content=request.message)]}

    async def event_generator():
        async for event in sre_agent_app.astream_events(inputs, config=config, version="v1"):
            kind = event["event"]
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"
            elif kind == "on_tool_start":
                tool_name = event["name"]
                yield f"data: {json.dumps({'type': 'status', 'content': f'Executing tool: {tool_name}...'})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
EOF

cat << 'EOF' > app/api/webhook.py
from fastapi import APIRouter, BackgroundTasks
from app.schemas.payloads import PrometheusAlert
from app.core.graph import sre_agent_app
from langchain_core.messages import HumanMessage

router = APIRouter()

def process_alert(alert: PrometheusAlert):
    alert_summary = alert.alerts[0].get("annotations", {}).get("summary", "Unknown alert") if alert.alerts else "Unknown alert"
    prompt = f"System Alert Triggered: {alert_summary}. Please analyze the root cause and provide troubleshooting steps."
    fingerprint = alert.alerts[0].get("fingerprint", "default") if alert.alerts else "default"
    config = {"configurable": {"thread_id": f"alert-{fingerprint}"}}
    inputs = {"messages": [HumanMessage(content=prompt)]}
    sre_agent_app.invoke(inputs, config=config)

@router.post("/webhook/prometheus")
async def receive_alert(alert: PrometheusAlert, background_tasks: BackgroundTasks):
    background_tasks.add_task(process_alert, alert)
    return {"status": "accepted", "message": "Alert received. SRE Agent is analyzing."}
EOF

cat << 'EOF' > main.py
from fastapi import FastAPI
from app.api import chat, webhook

app = FastAPI(
    title="SRE Meta Agent Platform",
    description="Enterprise AI Agent for R&D efficiency and SRE troubleshooting.",
    version="1.0.0"
)

app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(webhook.router, prefix="/api/v1", tags=["Webhook"])

@app.get("/health")
def health_check():
    return {"status": "healthy"}
EOF

# ==========================================
# 4. Generate Tests & Deployment
# ==========================================
echo "📝 Generating tests & deployment files..."

cat << 'EOF' > tests/test_graph.py
import pytest
from app.core.graph import sre_agent_app

def test_graph_compilation():
    assert sre_agent_app is not None
EOF

cat << 'EOF' > tests/chaos/test_resilience.py
import pytest
from app.tools.k8s_tools import get_pod_logs

def test_tool_oom_detection():
    log = get_pod_logs.invoke({"pod_name": "payment-service-oom", "namespace": "prod"})
    assert "OOMKilled" in log

def test_tool_normal_detection():
    log = get_pod_logs.invoke({"pod_name": "user-service-normal", "namespace": "prod"})
    assert "Normal operation" in log
EOF

cat << 'EOF' > deploy/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# ==========================================
# 5. Final Instructions
# ==========================================
echo ""
echo "🎉 Enterprise MVP (Factory Pattern) Generated Successfully!"
echo "==========================================="
echo "👉 Next Steps:"
echo "  1. cd $PROJECT_NAME"
echo "  2. conda create -n sre-agent python=3.11 -y && conda activate sre-agent"
echo "  3. pip install -r requirements.txt"
echo "  4. cp .env.example .env"
echo ""
echo "👉 IMPORTANT: Edit your .env file to set:"
echo "     LLM_PROVIDER=openai (or deepseek/anthropic/ollama)"
echo "     LLM_MODEL_NAME=gpt-4-turbo (or deepseek-chat, etc.)"
echo "     [YOUR_PROVIDER]_API_KEY=sk-xxx"
echo ""
echo "👉 Finally, run the server:"
echo "  uvicorn main:app --reload"
echo "==========================================="