from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage, ToolMessage
from app.core.state import AgentState
from app.tools.k8s_tools import get_pod_logs, restart_pod
from app.services.prompts import SRE_SYSTEM_PROMPT
from app.services.llm import llm

# Bind tools to LLM
tools = [get_pod_logs, restart_pod]
llm_with_tools = llm.bind_tools(tools)

def planner_node(state: AgentState):
    messages = state["messages"]
    system_msg = SystemMessage(content=SRE_SYSTEM_PROMPT)
    response = llm_with_tools.invoke([system_msg] + list(messages))
    return {"messages": [response]}

def tool_node(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    tool_messages = []
    
    for tool_call in last_message.tool_calls:
        if tool_call["name"] == "get_pod_logs":
            result = get_pod_logs.invoke(tool_call["args"])
        elif tool_call["name"] == "restart_pod":
            result = restart_pod.invoke(tool_call["args"])
        else:
            result = "Unknown tool"
            
        tool_messages.append(ToolMessage(tool_call_id=tool_call["id"], content=result))
    
    return {"messages": tool_messages}

def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("planner", planner_node)
    workflow.add_node("tools", tool_node)
    workflow.set_entry_point("planner")

    def should_continue(state: AgentState):
        last_message = state["messages"][-1]
        if getattr(last_message, "tool_calls", None):
            return "continue"
        return "end"

    workflow.add_conditional_edges(
        "planner", should_continue, {"continue": "tools", "end": END}
    )
    workflow.add_edge("tools", "planner")

    memory = MemorySaver()
    # To enable HITL, you can add interrupt_before=["tools"] here in the future
    # return workflow.compile(checkpointer=memory)

    # Compile the graph with an interrupt before the tools node
    # This means the graph will PAUSE before executing any tool
    return workflow.compile(
        checkpointer=memory,
        # interrupt_before=["tools"] # <--- Add this
    )

sre_agent_app = build_graph()
