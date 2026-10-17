from langgraph.types import interrupt, Command
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage, ToolMessage
from contextlib import asynccontextmanager
from app.core.state import AgentState
from app.services.prompts import SRE_SYSTEM_PROMPT
from app.services.llm import llm
# Import your tools (will be replaced by MCP later)
from app.tools.k8s_tools import get_pod_logs, restart_pod

tools = [get_pod_logs, restart_pod]
llm_with_tools = llm.bind_tools(tools)


async def planner_node(state: AgentState, llm_with_tools):
    messages = state["messages"]
    system_msg = SystemMessage(content=SRE_SYSTEM_PROMPT)
    # 🚨 使用 ainvoke 异步调用大模型
    response = await llm_with_tools.ainvoke([system_msg] + list(messages))
    return {"messages": [response]}

async def tool_node(state: AgentState, tools_map):
    messages = state["messages"]
    last_message = messages[-1]
    tool_messages = []
    
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        if tool_name in tools_map:
            try:
                # 🚨 使用 ainvoke 异步执行 MCP 工具
                result = await tools_map[tool_name].ainvoke(tool_call["args"])
                tool_messages.append(ToolMessage(tool_call_id=tool_call["id"], content=str(result)))
            except Exception as e:
                tool_messages.append(ToolMessage(tool_call_id=tool_call["id"], content=f"Tool execution error: {str(e)}"))
        else:
            tool_messages.append(ToolMessage(tool_call_id=tool_call["id"], content="Unknown tool"))
    
    return {"messages": tool_messages}

def build_graph(tools: list):
    tools_map = {t.name: t for t in tools}
    llm_with_tools = llm.bind_tools(tools)

    # 包装为 async lambda
    async def _planner(state): return await planner_node(state, llm_with_tools)
    async def _tools(state): return await tool_node(state, tools_map)

    workflow = StateGraph(AgentState)
    workflow.add_node("planner", _planner)
    workflow.add_node("tools", _tools)
    workflow.set_entry_point("planner")

    def should_continue(state: AgentState):
        last_message = state["messages"][-1]
        if getattr(last_message, "tool_calls", None):
            return "continue"
        return "end"

    workflow.add_conditional_edges("planner", should_continue, {"continue": "tools", "end": END})
    workflow.add_edge("tools", "planner")

    return workflow.compile(checkpointer=MemorySaver())

def approval_node(state: AgentState):
    """Pauses the graph if the tool call is high-risk."""
    last_message = state["messages"][-1]
    tool_name = last_message.tool_calls[0]["name"]
    
    # Define which tools require human approval
    HIGH_RISK_TOOLS = {"restart_pod"}
    
    if tool_name in HIGH_RISK_TOOLS:
        # Pause and wait for SRE approval
        approved = interrupt(f"⚠️ High-risk operation requested: `{tool_name}`. Approve?")
        if not approved:
            # If rejected, return a message and stop the tool execution
            return {"messages": [ToolMessage(
                tool_call_id=last_message.tool_calls[0]["id"], 
                content="Operation rejected by SRE."
            )]}
    
    # For low-risk tools or approved high-risk tools, proceed
    return {}  # Continue to the tool node

@asynccontextmanager
async def get_mcp_tools():
    """Connect to the local K8s MCP server via stdio."""
    client = MultiServerMCPClient({
        "k8s": {
            "command": "python",
            "args": ["mcp_servers/k8s_server.py"],
            "transport": "stdio"
        }
    })
    tools = await client.get_tools()
    yield tools

# Then in your graph building, use these MCP tools instead of k8s_tools.py
# Note: Since MCP tools are loaded asynchronously, you'll need to adapt your graph
# initialization to handle async setup (see LangChain MCP adapter docs).

# sre_agent_app = build_graph()