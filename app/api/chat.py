from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from app.core.graph import build_graph
from app.schemas.payloads import ChatRequest
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from app.schemas.payloads import ApprovalRequest
import json

router = APIRouter()

@router.post("/chat/stream")
async def chat_stream(chat_request: ChatRequest, request: Request):
    # Access the graph from the FastAPI app state
    agent_graph = request.app.state.agent_graph
    
    config = {"configurable": {"thread_id": chat_request.session_id}}
    inputs = {"messages": [HumanMessage(content=chat_request.message)]}

    async def event_generator():
        try:
            async for event in agent_graph.astream(inputs, config=config):
                for node_name, node_state in event.items():
                    print(f"🔍 Node finished: {node_name}")
                    
                    if "messages" in node_state:
                        last_msg = node_state["messages"][-1]
                        
                        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                            tool_name = last_msg.tool_calls[0]["name"]
                            yield f"data: {json.dumps({'type': 'status', 'content': f'Executing tool: {tool_name}...'})}\n\n"
                        
                        elif last_msg.content:
                            content = last_msg.content
                            
                            # 🚨 Handle LangChain's list-of-dicts content format
                            if isinstance(content, list):
                                text_content = "".join(
                                    block.get("text", "") for block in content if isinstance(block, dict)
                                )
                            else:
                                text_content = str(content)
                            
                            # Stream the extracted text
                            for i in range(0, len(text_content), 5):
                                chunk = text_content[i:i+5]
                                yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"
            
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

@router.post("/chat/approve")
async def approve_tool_execution(request: ApprovalRequest):
    """Resume a paused graph after SRE approval."""
    config = {"configurable": {"thread_id": request.session_id}}
    
    # Check if the graph is actually paused
    state = build_graph.get_state(config)
    if not state.next:
        return {"status": "error", "message": "No pending operations for this session."}
    
    if request.approved:
        # Resume with approval
        build_graph.invoke(Command(resume=True), config=config)
        return {"status": "success", "message": "Tool executed successfully."}
    else:
        # Resume with rejection
        build_graph.invoke(Command(resume=False), config=config)
        return {"status": "rejected", "message": "Operation cancelled by SRE."}
