from fastapi import FastAPI
from app.api import chat, webhook

app = FastAPI(
    title="SRE Meta Agent Platform",
    description="Enterprise AI Agent for R&D efficiency and SRE troubleshooting.",
    version="1.0.0"
)

# Register routers
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(webhook.router, prefix="/api/v1", tags=["Webhook"])

@app.get("/health")
def health_check():
    return {"status": "healthy"}
