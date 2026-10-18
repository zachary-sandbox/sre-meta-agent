param (
    [Parameter(Mandatory=$true)]
    [string]$Target
)

$CONDA_ENV = "sre-meta-agent"
$CONDA_RUN = "conda run --no-capture-output -n $CONDA_ENV"

switch ($Target) {
    "backend" { 
        Write-Host "🚀 Starting FastAPI Backend..." -ForegroundColor Green
        Invoke-Expression "$CONDA_RUN uvicorn main:app --reload" 
    }
    "frontend" { 
        Write-Host "🎨 Starting Streamlit Frontend..." -ForegroundColor Green
        Invoke-Expression "$CONDA_RUN streamlit run frontend/app.py" 
    }
    "mcp" { 
        Write-Host "🔧 Starting MCP Server..." -ForegroundColor Green
        Invoke-Expression "$CONDA_RUN python mcp_servers/k8s_server.py" 
    }
    "test" { 
        Write-Host "🧪 Running Tests..." -ForegroundColor Green
        Invoke-Expression "$CONDA_RUN python -m pytest tests/ -v" 
    }
    "install" { 
        Write-Host "📦 Installing Dependencies..." -ForegroundColor Green
        Invoke-Expression "$CONDA_RUN pip install -r requirements.txt" 
    }
    Default {
        Write-Host "[ERROR] Unknown command: $Target" -ForegroundColor Red
        Write-Host "Usage: .\run.ps1 [backend|frontend|mcp|test|install]"
    }
}