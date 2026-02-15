#!/bin/bash

# Start the Provider Data Validation System - Complete Stack
# Works on Linux / macOS / Git Bash (Windows)

set -e

echo ""
echo "========================================"
echo "Provider Validation System - STARTING"
echo "========================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ---- Resolve project root ----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

# ---- Detect OS ----
WINDOWS=false
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    WINDOWS=true
fi

# ---- Detect Python environment ----
PYTHON_CMD=""
ENV_NAME=""

# 1) Check for conda env
if command -v conda &>/dev/null; then
    if conda env list 2>/dev/null | grep -q "crewai-env"; then
        PYTHON_CMD="conda run --no-banner -n crewai-env python"
        ENV_NAME="conda (crewai-env)"
    fi
fi

# 2) Check for .venv
if [ -z "$PYTHON_CMD" ]; then
    if [ -f ".venv/bin/python" ]; then
        PYTHON_CMD=".venv/bin/python"
        ENV_NAME=".venv"
    elif [ -f ".venv/Scripts/python.exe" ]; then
        PYTHON_CMD=".venv/Scripts/python.exe"
        ENV_NAME=".venv (Windows)"
    fi
fi

# 3) Check for active virtualenv
if [ -z "$PYTHON_CMD" ] && [ -n "$VIRTUAL_ENV" ]; then
    PYTHON_CMD="python"
    ENV_NAME="active venv ($VIRTUAL_ENV)"
fi

# 4) Fallback to system python
if [ -z "$PYTHON_CMD" ]; then
    if command -v python3 &>/dev/null; then
        PYTHON_CMD="python3"
        ENV_NAME="system python3"
    elif command -v python &>/dev/null; then
        PYTHON_CMD="python"
        ENV_NAME="system python"
    else
        echo -e "${RED}[ERROR] No Python found! Install Python 3.10+ first.${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}[OK] Using: ${ENV_NAME}${NC}"
echo ""

# ---- Kill existing processes ----
echo -e "${YELLOW}[1/3] Stopping any existing services...${NC}"
if $WINDOWS; then
    # Windows (Git Bash): use netstat + taskkill
    for pid in $(netstat -aon 2>/dev/null | grep ':8000.*LISTENING' | awk '{print $NF}'); do
        taskkill //F //PID "$pid" &>/dev/null || true
    done
    for pid in $(netstat -aon 2>/dev/null | grep ':5173.*LISTENING' | awk '{print $NF}'); do
        taskkill //F //PID "$pid" &>/dev/null || true
    done
else
    # Linux/macOS: use lsof + kill
    lsof -ti :8000 2>/dev/null | xargs -r kill -9 2>/dev/null || true
    lsof -ti :5173 2>/dev/null | xargs -r kill -9 2>/dev/null || true
fi
sleep 1
echo -e "${GREEN}[OK] Ports cleared${NC}"
echo ""

# ---- Start backend ----
echo -e "${YELLOW}[2/3] Starting Backend API on port 8000...${NC}"

if [ -f ".env" ]; then
    set -a; source .env; set +a
fi

$PYTHON_CMD -m uvicorn src.provider_data_validation.api:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo -e "${GREEN}[OK] Backend starting (PID: $BACKEND_PID)${NC}"
echo "     API Docs: http://localhost:8000/docs"
echo ""

# Wait for backend
sleep 4

# ---- Start frontend ----
echo -e "${YELLOW}[3/3] Starting Frontend on port 5173...${NC}"

FRONTEND_DIR="$PROJECT_DIR/external_frontend"

if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}[WARN] external_frontend directory not found - skipping frontend.${NC}"
else
    cd "$FRONTEND_DIR"

    if ! command -v npm &>/dev/null; then
        echo -e "${RED}[WARN] npm not found - skipping frontend. Install Node.js from https://nodejs.org${NC}"
    else
        if [ ! -d "node_modules" ]; then
            echo "  Installing frontend dependencies..."
            npm install
        fi
        npm run dev &
        FRONTEND_PID=$!
        echo -e "${GREEN}[OK] Frontend starting (PID: $FRONTEND_PID)${NC}"
    fi

    cd "$PROJECT_DIR"
fi

echo ""
echo -e "${GREEN}========================================"
echo "SYSTEM STARTED!"
echo "========================================${NC}"
echo ""
echo "Frontend:  http://localhost:5173"
echo "Backend:   http://localhost:8000"
echo "API Docs:  http://localhost:8000/docs"
echo ""
echo "Environment: $ENV_NAME"
echo ""
echo "Press Ctrl+C to stop all services."
echo ""

# ---- Cleanup on exit ----
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down...${NC}"
    [ -n "$BACKEND_PID" ] && kill $BACKEND_PID 2>/dev/null
    [ -n "$FRONTEND_PID" ] && kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}All services stopped.${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Wait for background processes
wait
