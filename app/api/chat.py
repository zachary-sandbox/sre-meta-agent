from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from app.schemas.payloads import ChatRequest
from langchain_core.messages import HumanMessage
from langgraph.types import Command
import json

router = APIRouter()

def extract_text(content) -> str:
    """Helper function to parse LangChain's list-of-dicts content."""
    if isinstance(content, list):
        return "".join(block.get("text", "") for block in content if isinstance(block, dict))
    return str(content) if content else ""

async def generate_sse_stream(graph, inputs_or_command, config):
    """Generator for both initial chat and approval resumption."""
    try:
        async for event in graph.astream(inputs_or_command, config=config):
            for node_name, node_state in event.items():
                # Skip if node_state is None
                if node_state is None:
                    continue
                
                # Detect HITL Interrupt
                if node_name == "__interrupt__":
                    yield f"data: {json.dumps({'type': 'approval', 'content': 'pending'})}\n\n"
                    return 

                if "messages" in node_state:
                    last_msg = node_state["messages"][-1]
                    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                        tool_name = last_msg.tool_calls[0]["name"]
                        yield f"data: {json.dumps({'type': 'status', 'content': f'[TOOL] Executing: {tool_name}...'})}\n\n"
                    elif last_msg.content:
                        text_content = extract_text(last_msg.content)
                        for i in range(0, len(text_content), 5):
                            yield f"data: {json.dumps({'type': 'token', 'content': text_content[i:i+5]})}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        print(f"[ERROR] Backend Stream Error: {e}")
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        yield "data: [DONE]\n\n"

@router.post("/chat/stream")
async def chat_stream(chat_request: ChatRequest, request: Request):
    config = {"configurable": {"thread_id": chat_request.session_id}}
    inputs = {"messages": [HumanMessage(content=chat_request.message)]}
    
    headers = {"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"}
    return StreamingResponse(
        generate_sse_stream(request.app.state.agent_graph, inputs, config), 
        media_type="text/event-stream", 
        headers=headers
    )

@router.post("/chat/approve")
async def approve_chat(chat_request: ChatRequest, request: Request, approved: bool = True):
    """Resume the graph after human approval and stream the result."""
    config = {"configurable": {"thread_id": chat_request.session_id}}
    resume_command = Command(resume=approved)
    
    headers = {"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"}
    return StreamingResponse(
        generate_sse_stream(request.app.state.agent_graph, resume_command, config), 
        media_type="text/event-stream", 
        headers=headers
    )