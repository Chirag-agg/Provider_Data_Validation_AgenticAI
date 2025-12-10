@echo off
echo.
echo ========================================
echo Provider Validation System - STARTING
echo ========================================
echo.

REM Check if environment exists
conda env list | findstr "crewai-env" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Environment not found!
    echo.
    echo Please run install.bat first to set up the environment.
    echo.
    pause
    exit /b 1
)

echo [OK] Environment found
echo.

REM Kill any existing processes on ports
echo [1/3] Stopping any existing services...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5173 ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>&1
timeout /t 2 /nobreak >nul
echo [OK] Ports cleared
echo.

REM Start backend with conda environment
echo [2/3] Starting Backend API (with CrewAI)...
start "Provider Validation API" cmd /k "conda run -n crewai-env python -m uvicorn src.provider_data_validation.api:app --reload --host 127.0.0.1 --port 8000"
echo [OK] Backend starting...
echo.

REM Wait for backend
echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

REM Start frontend
echo [3/3] Starting Frontend...
start "Provider Validation Frontend" cmd /k "cd /d %CD%\external_frontend & npm run dev"
echo [OK] Frontend starting...
echo.

echo.
echo ========================================
echo SYSTEM STARTED!
echo ========================================
echo.
echo Frontend:  http://localhost:5173
echo Backend:   http://localhost:8000
echo API Docs:  http://localhost:8000/docs
echo.
echo Environment: crewai-env (with CrewAI)
echo.
echo Two windows opened:
echo 1. Backend API (with AI agents)
echo 2. Frontend (React app)
echo.
echo Press Ctrl+C in each window to stop
echo.
echo Opening browser in 3 seconds...
timeout /t 3 /nobreak >nul
start http://localhost:5173
echo.
pause
