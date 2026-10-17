# app/core/graph.py
from langgraph.types import interrupt, Command
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage, ToolMessage

from app.core.state import AgentState
from app.services.prompts import SRE_SYSTEM_PROMPT
from app.services.llm import llm

# ==========================================
# 1. Define Nodes
# ==========================================
async def planner_node(state: AgentState, llm_with_tools):
    messages = state["messages"]
    system_msg = SystemMessage(content=SRE_SYSTEM_PROMPT)
    # Asynchronously invoke the LLM with the bound tools
    response = await llm_with_tools.ainvoke([system_msg] + list(messages))
    return {"messages": [response]}

async def approval_node(state: AgentState):
    """Pauses the graph for high-risk operations (HITL)."""
    last_message = state["messages"][-1]
    
    # If there are no tool calls, return early
    if not getattr(last_message, "tool_calls", None):
        return {}

    tool_call = last_message.tool_calls[0]

    # Add all high-risk tools to the interception list
    HIGH_RISK_TOOLS = {
        "restart_pod", 
        "run_kubectl_command", 
        "apply_yaml_manifest"
    }
    
    # Define high-risk tools that require human approval
    if tool_call["name"] in HIGH_RISK_TOOLS:
        # Pause execution and suspend the state
        approved = interrupt(f"[WARN] Agent wants to execute {tool_call['name']}. Approve?")
        
        # If rejected by the SRE, generate a ToolMessage to inform the LLM
        if not approved:
            return {"messages": [ToolMessage(
                tool_call_id=tool_call["id"], 
                content="Operation rejected by SRE. Please tell the user it was cancelled."
            )]}
    
    # If it's a low-risk tool or approved by SRE, return an empty dict to continue the flow
    return {}

async def tool_node(state: AgentState, tools_map):
    messages = state["messages"]
    last_message = messages[-1]
    tool_messages = []
    
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        if tool_name in tools_map:
            try:
                # Asynchronously execute the MCP tool
                result = await tools_map[tool_name].ainvoke(tool_call["args"])
                tool_messages.append(ToolMessage(tool_call_id=tool_call["id"], content=str(result)))
            except Exception as e:
                tool_messages.append(ToolMessage(tool_call_id=tool_call["id"], content=f"Tool execution error: {str(e)}"))
        else:
            tool_messages.append(ToolMessage(tool_call_id=tool_call["id"], content="Unknown tool"))
    
    return {"messages": tool_messages}


# ==========================================
# 2. Graph Builder
# ==========================================
def build_graph(tools: list):
    # Dynamically bind the provided MCP tools
    tools_map = {t.name: t for t in tools}
    llm_with_tools = llm.bind_tools(tools)

    # Wrap node functions to pass the tool dependencies
    async def _planner(state): return await planner_node(state, llm_with_tools)
    async def _tools(state): return await tool_node(state, tools_map)

    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("planner", _planner)
    workflow.add_node("approval", approval_node)
    workflow.add_node("tools", _tools)
    
    # Set entry point
    workflow.set_entry_point("planner")

    # 1. Routing logic after Planner
    def should_continue(state: AgentState):
        if getattr(state["messages"][-1], "tool_calls", None):
            return "approval" # Always go to the approval node first
        return "end"

    # 2. Routing logic after Approval
    def route_after_approval(state: AgentState):
        # If the last message is a ToolMessage, it was rejected. Route back to planner.
        if isinstance(state["messages"][-1], ToolMessage):
            return "planner"
        # Otherwise, it was approved (or no approval needed). Proceed to tools.
        return "tools"

    # Add edges
    workflow.add_conditional_edges("planner", should_continue, {"approval": "approval", "end": END})
    workflow.add_conditional_edges("approval", route_after_approval, {"tools": "tools", "planner": "planner"})
    workflow.add_edge("tools", "planner")

    # Compile the graph with memory
    return workflow.compile(checkpointer=MemorySaver())