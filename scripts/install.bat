@echo off
echo.
echo ========================================
echo Provider Validation System - INSTALLER
echo ========================================
echo.
echo This will:
echo 1. Create a fresh conda environment
echo 2. Install all Python dependencies
echo 3. Install frontend dependencies
echo.
pause

REM Remove old environment if exists
echo.
echo [1/5] Removing old environment (if exists)...
conda env remove -n crewai-env -y >nul 2>&1
echo [OK] Ready for fresh install
echo.

REM Create new environment
echo [2/5] Creating conda environment...
conda create -n crewai-env python=3.11 -y
if errorlevel 1 (
    echo [ERROR] Failed to create conda environment
    pause
    exit /b 1
)
echo [OK] Environment created
echo.

REM Install Python packages
echo [3/5] Installing Python packages (this may take 2-3 minutes)...
call conda run -n crewai-env pip install fastapi uvicorn pydantic python-multipart openpyxl pypdf beautifulsoup4 httpx lxml requests python-dotenv aiofiles pydantic-settings
if errorlevel 1 (
    echo [ERROR] Failed to install Python packages
    pause
    exit /b 1
)
echo [OK] Python packages installed
echo.

REM Install CrewAI
echo [4/5] Installing CrewAI...
call conda run -n crewai-env pip install "crewai[tools]==1.6.1"
if errorlevel 1 (
    echo [ERROR] Failed to install CrewAI
    pause
    exit /b 1
)
echo [OK] CrewAI installed
echo.

REM Install frontend dependencies
echo [5/5] Installing frontend dependencies...
cd external_frontend
if not exist node_modules (
    call npm install
    if errorlevel 1 (
        echo [ERROR] Failed to install npm packages
        cd ..
        pause
        exit /b 1
    )
)
cd ..
echo [OK] Frontend dependencies installed
echo.

echo.
echo ========================================
echo INSTALLATION COMPLETE!
echo ========================================
echo.
echo Environment: crewai-env
echo Python packages: FastAPI, CrewAI, etc.
echo Frontend: React + Vite
echo.
echo Next step: Run start_system.bat
echo.
pause
