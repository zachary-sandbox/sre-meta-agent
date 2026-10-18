import pytest
from unittest.mock import MagicMock, AsyncMock
from langchain_core.messages import HumanMessage, AIMessage
from app.core.graph import build_graph
from langchain_core.tools import tool

@tool
def mock_k8s_tool():
    """A dummy tool for testing."""
    return "Mock logs"

@pytest.mark.asyncio
async def test_graph_routes_to_tools(mocker):
    """Verify that the graph correctly routes to the approval node when a tool call is generated."""
    
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value = mock_llm
    
    # [FIX] 必须使用 AsyncMock 替代 MagicMock，因为代码里用的是 await ainvoke
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(
        content="", 
        tool_calls=[{"name": "mock_k8s_tool", "args": {}, "id": "call_123"}]
    ))

    mocker.patch("app.core.graph.llm", mock_llm)
    graph = build_graph([mock_k8s_tool])
    
    inputs = {"messages": [HumanMessage(content="Test troubleshooting")]}
    config = {"configurable": {"thread_id": "test-route"}}
    
    async for event in graph.astream(inputs, config=config):
        if "approval" in event:
            assert True
            return
            
    pytest.fail("Graph did not reach the approval node.")