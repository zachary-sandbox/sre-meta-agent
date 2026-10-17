from fastapi import APIRouter, BackgroundTasks, Request
from app.schemas.payloads import PrometheusAlert
from langchain_core.messages import HumanMessage

router = APIRouter()

async def process_alert(alert: PrometheusAlert, agent_graph):
    alert_summary = alert.alerts[0].get("annotations", {}).get("summary", "Unknown alert") if alert.alerts else "Unknown alert"
    prompt = f"System Alert Triggered: {alert_summary}. Please analyze the root cause and provide troubleshooting steps."
    fingerprint = alert.alerts[0].get("fingerprint", "default") if alert.alerts else "default"
    
    config = {"configurable": {"thread_id": f"alert-{fingerprint}"}}
    inputs = {"messages": [HumanMessage(content=prompt)]}
    
    await agent_graph.ainvoke(inputs, config=config)

@router.post("/webhook/prometheus")
async def receive_alert(alert: PrometheusAlert, background_tasks: BackgroundTasks, request: Request):
    agent_graph = request.app.state.agent_graph
    background_tasks.add_task(process_alert, alert, agent_graph)
    return {"status": "accepted", "message": "Alert received. SRE Agent is analyzing."}