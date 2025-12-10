@echo off
echo.
echo ================================
echo Stopping Current Backend
echo ================================
echo.

REM Kill any Python process running uvicorn on port 8000
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo Killing process %%a on port 8000...
    taskkill /F /PID %%a >nul 2>&1
)

timeout /t 2 /nobreak >nul
echo [OK] Port 8000 is now free
echo.
echo ================================
echo Starting Backend with CrewAI
echo ================================
echo.
echo Starting in 3 seconds...
timeout /t 3 /nobreak >nul

REM Start backend using conda run (works without activating)
start "Provider Data Validation API - CrewAI" cmd /k "conda run -n crewai-env python -m uvicorn src.provider_data_validation.api:app --reload --host 127.0.0.1 --port 8000"

echo.
echo [OK] Backend started with CrewAI support!
echo.
echo API:      http://localhost:8000
echo Docs:     http://localhost:8000/docs
echo.
echo Check the new window for backend logs.
echo.
pause
