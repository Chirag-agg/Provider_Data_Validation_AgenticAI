@echo off
setlocal enabledelayedexpansion

echo.
echo ================================
echo Restarting Backend Server
echo ================================
echo.

REM ---- Resolve project root ----
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."
cd /d "%PROJECT_DIR%"

REM ---- Detect Python environment ----
set "PYTHON_CMD="
set "ENV_NAME="

where conda >nul 2>&1
if %errorlevel%==0 (
    conda env list 2>nul | findstr "crewai-env" >nul 2>&1
    if !errorlevel!==0 (
        set "PYTHON_CMD=conda run -n crewai-env python"
        set "ENV_NAME=conda (crewai-env)"
    )
)

if not defined PYTHON_CMD (
    if exist ".venv\Scripts\python.exe" (
        set "PYTHON_CMD=%PROJECT_DIR%\.venv\Scripts\python"
        set "ENV_NAME=.venv"
    )
)

if not defined PYTHON_CMD (
    where python >nul 2>&1
    if %errorlevel%==0 (
        set "PYTHON_CMD=python"
        set "ENV_NAME=system python"
    ) else (
        echo [ERROR] No Python found! Run install.bat first.
        pause
        exit /b 1
    )
)

REM ---- Kill backend on port 8000 ----
echo [1/2] Stopping current backend...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING 2^>nul') do (
    echo Killing process %%a on port 8000...
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 2 /nobreak >nul
echo [OK] Port 8000 is free
echo.

REM ---- Start backend ----
echo [2/2] Starting Backend (%ENV_NAME%)...
timeout /t 2 /nobreak >nul

start "Provider Data Validation API" cmd /k "cd /d "%PROJECT_DIR%" && %PYTHON_CMD% -m uvicorn src.provider_data_validation.api:app --reload --host 127.0.0.1 --port 8000"

echo.
echo [OK] Backend restarted!
echo.
echo API:      http://localhost:8000
echo Docs:     http://localhost:8000/docs
echo Env:      %ENV_NAME%
echo.
echo Check the new window for backend logs.
echo.
pause
