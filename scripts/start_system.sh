#!/bin/bash

# Start the Provider Data Validation System - Complete Stack
# This script starts both backend API and frontend

echo "================================"
echo "Provider Data Validation System"
echo "================================"
echo ""

# Check if running on Windows (Git Bash or WSL)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    WINDOWS=true
else
    WINDOWS=false
fi

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Ollama is running
echo -e "${YELLOW}[1/3] Checking Ollama...${NC}"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Ollama is running${NC}"
else
    echo -e "${RED}✗ Ollama is not running on port 11434${NC}"
    echo "  Start Ollama with: ollama serve"
    echo "  Or run: ollama pull llama3.1"
fi
echo ""

# Start backend API
echo -e "${YELLOW}[2/3] Starting Backend API on port 8000...${NC}"
if [ -f ".env" ]; then
    source .env
else
    echo "  No .env file found, using defaults"
fi

cd "$(dirname "$0")"

# Start in background
if $WINDOWS; then
    start "Provider Data Validation API" python -m uvicorn src.provider_data_validation.api:app --reload --host 0.0.0.0 --port 8000
else
    python -m uvicorn src.provider_data_validation.api:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
fi
echo -e "${GREEN}✓ Backend starting at http://localhost:8000${NC}"
echo "  Documentation: http://localhost:8000/docs"
echo ""

# Start frontend
echo -e "${YELLOW}[3/3] Starting Frontend on port 5173...${NC}"
cd external_frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "  Installing dependencies..."
    npm install
fi

if $WINDOWS; then
    start "Provider Data Validation Frontend" npm run dev
else
    npm run dev &
    FRONTEND_PID=$!
fi
echo -e "${GREEN}✓ Frontend starting at http://localhost:5173${NC}"
echo ""

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}System is starting...${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "Frontend:     http://localhost:5173"
echo "API Docs:     http://localhost:8000/docs"
echo "API Endpoint: http://localhost:8000"
echo ""

if [ $WINDOWS = false ]; then
    echo "Press Ctrl+C to stop all services"
    wait
fi
