from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.core.graph import sre_agent_app
from app.schemas.payloads import ChatRequest
from langchain_core.messages import HumanMessage
import json

router = APIRouter()

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Stream Agent reasoning and tool execution via SSE."""
    config = {"configurable": {"thread_id": request.session_id}}
    inputs = {"messages": [HumanMessage(content=request.message)]}

    async def event_generator():
        async for event in sre_agent_app.astream_events(inputs, config=config, version="v1"):
            kind = event["event"]
            
            # Stream LLM tokens
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"
            
            # Stream Tool Execution status
            elif kind == "on_tool_start":
                tool_name = event["name"]
                yield f"data: {json.dumps({'type': 'status', 'content': f'Executing tool: {tool_name}...'})}\n\n"
        
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
