import pytest
from unittest.mock import MagicMock
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from app.core.graph import build_graph
from langchain_core.tools import tool

# We need to mock the LLM *before* importing the graph
with MagicMock() as mock_llm:
    with pytest.MonkeyPatch.context() as mp:
        # Mock the app.services.llm.llm variable
        mp.setattr("app.services.llm.llm", mock_llm)
        mp.setattr("app.services.llm.llm.bind_tools", return_value=mock_llm)

def test_graph_routes_to_tools(monkeypatch):
    """Test if the graph routes to the tool node when the LLM returns a tool call."""
    from app.core.graph import build_graph
    
    # 1. Create a mock LLM
    class MockLLM:
        def bind_tools(self, tools):
            return self
            
        def invoke(self, messages):
            # Simulate LLM deciding to call a tool
            msg = AIMessage(content="", tool_calls=[
                {"name": "get_pod_logs", "args": {"pod_name": "test-pod"}, "id": "call_1"}
            ])
            return msg

    # 2. Patch the LLM in the graph module
    monkeypatch.setattr("app.core.graph.llm_with_tools", MockLLM())
    
    # 3. Build graph and invoke
    graph = build_graph()
    inputs = {"messages": [HumanMessage(content="Check pod logs")]}
    config = {"configurable": {"thread_id": "test-1"}}
    
    result = graph.invoke(inputs, config=config)
    
    # 4. Assertions
    messages = result["messages"]
    # Should have: HumanMessage, AIMessage (tool_call), ToolMessage, AIMessage (final answer)
    assert len(messages) >= 3
    # Check if the ToolMessage exists (meaning tool_node executed)
    assert any(isinstance(msg, ToolMessage) for msg in messages)

@tool
def mock_tool_for_test():
    """A dummy tool for testing graph compilation."""
    return "dummy result"

def test_graph_compilation():
    """Verify that the LangGraph state machine compiles successfully with injected tools."""
    graph = build_graph([mock_tool_for_test])
    assert graph is not None