# ==========================================
# Variables
# ==========================================
CONDA_ENV = sre-meta-agent
CONDA_RUN = conda run --no-capture-output -n $(CONDA_ENV)

APP_MODULE = main:app
FRONTEND_APP = frontend/app.py
MCP_SERVER = mcp_servers/k8s_server.py

# ==========================================
# Phony Targets
# ==========================================
.PHONY: help install backend frontend mcp test clean docker-build docker-up docker-down

# ==========================================
# Targets
# ==========================================

help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies in $(CONDA_ENV)"
	@echo "  make backend      - Start FastAPI backend (Uvicorn)"
	@echo "  make frontend     - Start Streamlit UI"
	@echo "  make mcp          - Run MCP Server standalone"
	@echo "  make test         - Run pytest suite"
	@echo "  make docker-build - Build all Docker images"
	@echo "  make docker-up    - Start all containers in background"
	@echo "  make docker-down  - Stop and remove containers"
	@echo "  make clean        - Remove caches"

install:
	@echo "[INFO] Installing dependencies in $(CONDA_ENV)..."
	$(CONDA_RUN) pip install -r requirements.txt

backend:
	@echo "[START] FastAPI Backend -> http://127.0.0.1:8000"
	$(CONDA_RUN) uvicorn $(APP_MODULE) --reload

frontend:
	@echo "[START] Streamlit Frontend -> http://localhost:8501"
	$(CONDA_RUN) streamlit run $(FRONTEND_APP)

mcp:
	@echo "[START] K8s MCP Server..."
	$(CONDA_RUN) python $(MCP_SERVER)

test:
	@echo "[TEST] Running pytest..."
	$(CONDA_RUN) python -m pytest tests/ -v

docker-build:
	@echo "[INFO] Building Docker images via docker-compose..."
	docker-compose build

docker-up:
	@echo "[START] Starting all containers via docker-compose..."
	docker-compose up -d
	@echo "[INFO] Backend is on http://localhost:8000"
	@echo "[INFO] Frontend is on http://localhost:8501"

docker-down:
	@echo "[CLEAN] Stopping containers..."
	docker-compose down

clean:
	@echo "[CLEAN] Removing Python caches..."
	$(CONDA_RUN) python -c "import shutil, pathlib; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__')]; shutil.rmtree('.pytest_cache', ignore_errors=True)"