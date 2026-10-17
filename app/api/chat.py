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
        try:
            # Use astream instead of astream_events for better stability with Ollama
            async for event in sre_agent_app.astream(inputs, config=config):
                for node_name, node_state in event.items():
                    print(f"🔍 Node finished: {node_name}")
                    
                    if "messages" in node_state:
                        last_msg = node_state["messages"][-1]
                        
                        # 1. Send Tool Execution Status
                        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                            tool_name = last_msg.tool_calls[0]["name"]
                            yield f"data: {json.dumps({'type': 'status', 'content': f'Executing tool: {tool_name}...'})}\n\n"
                        
                        # 2. Send Final Text (Simulate streaming by sending chunks)
                        elif last_msg.content:
                            content = last_msg.content
                            # Send chunk by chunk to simulate a typewriter effect
                            for i in range(0, len(content), 5):
                                chunk = content[i:i+5]
                                yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"
            
            print("✅ Stream finished successfully.")
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            print(f"❌ Backend Error: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
            yield "data: [DONE]\n\n"

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(event_generator(), media_type="text/event-stream", headers=headers)