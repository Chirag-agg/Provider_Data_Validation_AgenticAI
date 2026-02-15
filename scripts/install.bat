@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================
echo Provider Validation System - INSTALLER
echo ========================================
echo.
echo This will:
echo   1. Set up a Python environment (conda or venv)
echo   2. Install all Python dependencies
echo   3. Install frontend dependencies
echo.
echo Supports: conda, venv, or system pip
echo.
pause

set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."
cd /d "%PROJECT_DIR%"

REM ---- Detect Python environment strategy ----
set "USE_CONDA=0"
set "USE_VENV=0"

where conda >nul 2>&1
if %errorlevel%==0 (
    set "USE_CONDA=1"
    echo [INFO] Conda detected.
) else (
    echo [INFO] Conda not found - will use Python venv instead.
    set "USE_VENV=1"
)

echo.

REM ============================================
REM  STEP 1: Create environment
REM ============================================

if "%USE_CONDA%"=="1" (
    echo [1/4] Setting up conda environment "crewai-env"...
    conda env remove -n crewai-env -y >nul 2>&1
    conda create -n crewai-env python=3.11 -y
    if errorlevel 1 (
        echo [WARN] Conda env creation failed. Falling back to venv...
        set "USE_CONDA=0"
        set "USE_VENV=1"
    ) else (
        echo [OK] Conda environment created
    )
)

if "%USE_VENV%"=="1" (
    echo [1/4] Setting up Python virtual environment...
    where python >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Python not found! Install Python 3.10+ and add to PATH.
        pause
        exit /b 1
    )
    if exist ".venv" (
        echo [INFO] Removing old .venv...
        rmdir /s /q ".venv"
    )
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created at .venv
)

echo.

REM ============================================
REM  STEP 2: Install Python packages
REM ============================================
echo [2/4] Installing Python packages (this may take 2-3 minutes)...

if "%USE_CONDA%"=="1" (
    call conda run -n crewai-env pip install -r requirements.txt
) else (
    call .venv\Scripts\pip install -r requirements.txt
)
if errorlevel 1 (
    echo [ERROR] Failed to install Python packages.
    pause
    exit /b 1
)
echo [OK] Python packages installed
echo.

REM ============================================
REM  STEP 3: Install frontend dependencies
REM ============================================
echo [3/4] Installing frontend dependencies...

where npm >nul 2>&1
if errorlevel 1 (
    echo [WARN] npm not found! Skipping frontend install.
    echo        Install Node.js from https://nodejs.org if you need the frontend.
    goto :skip_frontend
)

if not exist "%PROJECT_DIR%\external_frontend" (
    echo [WARN] external_frontend directory not found. Skipping.
    goto :skip_frontend
)

cd /d "%PROJECT_DIR%\external_frontend"
call npm install
if errorlevel 1 (
    echo [ERROR] Failed to install npm packages.
    cd /d "%PROJECT_DIR%"
    pause
    exit /b 1
)
cd /d "%PROJECT_DIR%"
echo [OK] Frontend dependencies installed

:skip_frontend
echo.

REM ============================================
REM  STEP 4: Create .env if missing
REM ============================================
echo [4/4] Checking .env file...
if not exist ".env" (
    echo # Provider Data Validation System > .env
    echo # Add your API keys and config here >> .env
    echo # OPENAI_API_KEY=your_key_here >> .env
    echo # TWILIO_ACCOUNT_SID=your_sid >> .env
    echo # TWILIO_AUTH_TOKEN=your_token >> .env
    echo # TWILIO_FROM_NUMBER=+1234567890 >> .env
    echo [OK] Created template .env file - edit it with your API keys.
) else (
    echo [OK] .env file already exists
)

echo.
echo ========================================
echo INSTALLATION COMPLETE!
echo ========================================
echo.
if "%USE_CONDA%"=="1" (
    echo Environment: conda "crewai-env"
    echo Activate:    conda activate crewai-env
) else (
    echo Environment: .venv  (Python virtual environment^)
    echo Activate:    .venv\Scripts\activate
)
echo Python deps:  FastAPI, CrewAI, Uvicorn, etc.
echo Frontend:     React + Vite
echo.
echo Next step: Run start_system.bat
echo.
pause
