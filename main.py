# main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api import chat, webhook
from langchain.mcp import MCPAdapter
from app.core.graph import build_graph

# We will store the graph in app.state so routes can access it
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting up: Connecting to K8s MCP Server...")
    
    # Configure the MCP Adapter (v2 syntax)
    config = {
        "mcpServers": {
            "k8s": {
                "command": "python",
                "args": ["mcp_servers/k8s_server.py"]
            }
        }
    }
    
    # Connect and load tools
    async with MCPAdapter(config) as adapter:
        mcp_tools = await adapter.list_tools()
        print(f"✅ Loaded {len(mcp_tools)} tools from MCP: {[t.name for t in mcp_tools]}")
        
        # Build the graph with the real MCP tools
        app.state.agent_graph = build_graph(mcp_tools)
        
    yield # The app runs here
    
    print("🛑 Shutting down: Disconnecting MCP Server...")

app = FastAPI(
    title="SRE Meta Agent Platform",
    description="Enterprise AI Agent for R&D efficiency and SRE troubleshooting.",
    version="0.2.0",
    lifespan=lifespan # Register the lifespan
)

# Register routers
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(webhook.router, prefix="/api/v1", tags=["Webhook"])

@app.get("/health")
def health_check():
    return {"status": "healthy"}