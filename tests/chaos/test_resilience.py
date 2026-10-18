import pytest
from app.tools.k8s_tools import get_pod_logs
from app.core.graph import build_graph
from unittest.mock import AsyncMock, patch
from langchain_core.messages import HumanMessage, AIMessage

def test_tool_oom_detection():
    """Test tool accurately identifies OOM exceptions."""
    log = get_pod_logs.invoke({"pod_name": "payment-service-oom", "namespace": "prod"})
    assert "OOMKilled" in log

def test_tool_normal_detection():
    """Test tool accurately identifies normal status."""
    log = get_pod_logs.invoke({"pod_name": "user-service-normal", "namespace": "prod"})
    assert "Normal operation" in log


@pytest.mark.asyncio
async def test_llm_timeout_resilience(mocker):
    """Simulate LLM API timeout during planner node execution."""
    mock_tool = mocker.Mock()
    mock_tool.name = "mock_tool"
    
    # Mock LLM to raise a TimeoutError
    mock_llm = mocker.Mock()
    mock_llm.bind_tools.return_value = mock_llm
    mock_llm.ainvoke = AsyncMock(side_effect=TimeoutError("LLM API Timeout"))

    with patch("app.core.graph.llm", mock_llm):
        graph = build_graph([mock_tool])
        inputs = {"messages": [HumanMessage(content="Test timeout")]}
        
        # Graph should raise the error (in a real app, FastAPI catches this and returns SSE error)
        with pytest.raises(TimeoutError):
            await graph.ainvoke(inputs, config={"configurable": {"thread_id": "chaos-1"}})

@pytest.mark.asyncio
async def test_mcp_tool_disconnect(mocker):
    """Simulate MCP Server disconnect during tool execution."""
    
    # 1. Setup Mock Tool that raises an exception
    mock_tool = mocker.Mock()
    mock_tool.name = "mock_tool"
    mock_tool.ainvoke = AsyncMock(side_effect=ConnectionError("MCP Server Disconnected"))

    # 2. Setup Mock LLM with side_effect (First call: Tool Call, Second call: Final Answer)
    mock_llm = mocker.Mock()
    mock_llm.bind_tools.return_value = mock_llm
    
    mock_llm.ainvoke = AsyncMock(side_effect=[
        # First response: LLM decides to call the tool
        AIMessage(content="", tool_calls=[{"name": "mock_tool", "args": {}, "id": "call_1"}]),
        # Second response: LLM sees the error and generates a final text response (no tool_calls)
        AIMessage(content="I tried to execute the tool, but the MCP server disconnected.")
    ])

    # 3. Patch the LLM and build the graph
    mocker.patch("app.core.graph.llm", mock_llm)
    graph = build_graph([mock_tool])
    
    # 4. Run the graph
    inputs = {"messages": [HumanMessage(content="Test disconnect")]}
    config = {"configurable": {"thread_id": "chaos-2"}}
    
    result = await graph.ainvoke(inputs, config=config)
    
    # 5. Assertions
    # Check if the error message was captured in a ToolMessage
    tool_messages = [m for m in result["messages"] if m.type == "tool"]
    assert len(tool_messages) > 0
    assert "Tool execution error: MCP Server Disconnected" in tool_messages[0].content
    
    # Check if the Agent successfully exited the loop with a final response
    assert "MCP server disconnected" in result["messages"][-1].content