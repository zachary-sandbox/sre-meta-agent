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
