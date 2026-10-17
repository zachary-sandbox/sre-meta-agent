from fastapi import APIRouter, BackgroundTasks
from app.schemas.payloads import PrometheusAlert
from app.core.graph import sre_agent_app
from langchain_core.messages import HumanMessage

router = APIRouter()

def process_alert(alert: PrometheusAlert):
    # Extract alert summary
    alert_summary = alert.alerts[0].get("annotations", {}).get("summary", "Unknown alert") if alert.alerts else "Unknown alert"
    prompt = f"System Alert Triggered: {alert_summary}. Please analyze the root cause and provide troubleshooting steps."
    
    fingerprint = alert.alerts[0].get("fingerprint", "default") if alert.alerts else "default"
    config = {"configurable": {"thread_id": f"alert-{fingerprint}"}}
    inputs = {"messages": [HumanMessage(content=prompt)]}
    
    # Execute Agent in background
    sre_agent_app.invoke(inputs, config=config)

@router.post("/webhook/prometheus")
async def receive_alert(alert: PrometheusAlert, background_tasks: BackgroundTasks):
    """Receive Prometheus alerts and trigger Agent automatically."""
    background_tasks.add_task(process_alert, alert)
    return {"status": "accepted", "message": "Alert received. SRE Agent is analyzing."}
