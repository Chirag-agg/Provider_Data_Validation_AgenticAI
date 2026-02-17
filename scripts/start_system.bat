@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================
echo Provider Validation System - STARTING
echo ========================================
echo.

REM ---- Resolve project root ----
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."
cd /d "%PROJECT_DIR%"

REM ---- Detect Python environment ----
set "PYTHON_CMD="
set "ENV_NAME="

REM 1) Check for conda env
where conda >nul 2>&1
if %errorlevel%==0 (
    conda env list 2>nul | findstr "crewai-env" >nul 2>&1
    if !errorlevel!==0 (
        set "PYTHON_CMD=conda run -n crewai-env python"
        set "ENV_NAME=conda (crewai-env)"
    )
)

REM 2) Check for .venv
if not defined PYTHON_CMD (
    if exist ".venv\Scripts\python.exe" (
        set "PYTHON_CMD=%PROJECT_DIR%\.venv\Scripts\python"
        set "ENV_NAME=.venv"
    )
)

REM 3) Fallback to system python
if not defined PYTHON_CMD (
    where python >nul 2>&1
    if %errorlevel%==0 (
        set "PYTHON_CMD=python"
        set "ENV_NAME=system python"
    ) else (
        echo [ERROR] No Python found!
        echo         Install Python 3.10+ or run install.bat first.
        pause
        exit /b 1
    )
)

echo [OK] Using: %ENV_NAME%
echo.

REM ---- Kill existing processes on ports ----
echo [1/3] Stopping any existing services...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING 2^>nul') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5173 ^| findstr LISTENING 2^>nul') do taskkill /F /PID %%a >nul 2>&1
timeout /t 2 /nobreak >nul
echo [OK] Ports cleared
echo.

REM ---- Start backend ----
echo [2/3] Starting Backend API...
start "Provider Validation API" cmd /k "cd /d "%PROJECT_DIR%" && %PYTHON_CMD% -m uvicorn src.provider_data_validation.api:app --reload --host 127.0.0.1 --port 8000"
echo [OK] Backend starting...
echo.

REM Wait for backend
echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

REM ---- Start frontend ----
echo [3/3] Starting Frontend...
set "FRONTEND_DIR=%PROJECT_DIR%\external_frontend"

if not exist "%FRONTEND_DIR%" (
    echo [WARN] external_frontend directory not found - skipping frontend.
    goto :done
)

where npm >nul 2>&1
if errorlevel 1 (
    echo [WARN] npm not found - skipping frontend.
    echo        Install Node.js from https://nodejs.org
    goto :done
)

if not exist "%FRONTEND_DIR%\node_modules" (
    echo [INFO] Installing frontend dependencies first...
    cd /d "%FRONTEND_DIR%"
    call npm install
    cd /d "%PROJECT_DIR%"
)

start "Provider Validation Frontend" cmd /k "cd /d "%FRONTEND_DIR%" && npm run dev"
echo [OK] Frontend starting...
echo.

:done
echo.
echo ========================================
echo SYSTEM STARTED!
echo ========================================
echo.
echo Frontend:  http://localhost:5173
echo Backend:   http://localhost:8000
echo API Docs:  http://localhost:8000/docs
echo.
echo Environment: %ENV_NAME%
echo.
echo Windows opened:
echo   1. Backend API  (FastAPI + CrewAI)
echo   2. Frontend     (React + Vite)
echo.
echo Press Ctrl+C in each window to stop.
echo.
echo Opening browser in 3 seconds...
timeout /t 3 /nobreak >nul
start http://localhost:5173
echo.
pause
