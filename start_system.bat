@echo off
REM Start the Provider Data Validation System - Complete Stack
REM This script starts backend API and frontend

echo.
echo ================================
echo Provider Data Validation System
echo ================================
echo.

REM Check dependencies
echo [0/3] Checking dependencies...
python -m pip show fastapi > nul 2>&1
if errorlevel 1 (
    echo [*] Installing dependencies...
    pip install fastapi uvicorn pydantic python-multipart openpyxl pypdf beautifulsoup4 httpx
    if errorlevel 1 (
        echo [X] Failed to install dependencies
        pause
        exit /b 1
    )
    echo [OK] Dependencies installed
) else (
    echo [OK] Dependencies already installed
)
echo.

REM Set default port
set PORT=8000
set HOST=127.0.0.1
echo.

REM Check if Ollama is running (optional)
echo [1/3] Checking Ollama (optional)...
curl -s http://127.0.0.1:11434/api/tags > nul 2>&1
if errorlevel 1 (
    echo [!] Ollama is not running on port 11434 (optional, not required for validation)
) else (
    echo [OK] Ollama is running
)
echo.

REM Start backend API
echo [2/3] Starting Backend API on port %PORT%...
start "Provider Data Validation API" cmd /k "cd /d %CD% && python -m uvicorn src.provider_data_validation.api:app --reload --host 127.0.0.1 --port 8000"
echo [OK] Backend starting at http://localhost:8000
echo      Documentation: http://localhost:8000/docs
echo.

REM Start frontend
echo [3/3] Starting Frontend on port 5173...

REM Check if node_modules exists
if not exist "external_frontend\node_modules" (
    echo [*] Installing npm dependencies...
    cd external_frontend
    call npm install
    cd ..
    if errorlevel 1 (
        echo [X] Failed to install npm packages
        pause
        exit /b 1
    )
)

REM Start frontend development server
start "Provider Data Validation Frontend" cmd /k "cd /d %CD%\external_frontend && npm run dev"
echo [OK] Frontend starting at http://localhost:5173
echo.

echo.
echo ================================
echo System is starting...
echo ================================
echo.
echo Frontend:      http://localhost:5173
echo API:           http://localhost:8000
echo API Docs:      http://localhost:8000/docs
echo.
echo Press Ctrl+C in each window to stop
echo.
pause
