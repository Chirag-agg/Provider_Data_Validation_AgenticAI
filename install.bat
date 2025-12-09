@echo off
REM Install dependencies and prepare the system for running

echo.
echo ================================
echo Dependency Installation Script
echo ================================
echo.

echo [1/3] Installing Python dependencies...
pip install fastapi uvicorn pydantic python-multipart openpyxl pypdf beautifulsoup4 httpx

if errorlevel 1 (
    echo [X] Failed to install Python dependencies
    pause
    exit /b 1
)
echo [OK] Python dependencies installed
echo.

echo [2/3] Installing npm dependencies...
cd external_frontend
call npm install
if errorlevel 1 (
    echo [X] Failed to install npm packages
    pause
    exit /b 1
)
echo [OK] npm dependencies installed
cd ..
echo.

echo [3/3] Verifying installation...
python -c "import fastapi; print('FastAPI version:', fastapi.__version__)" || goto :error
echo [OK] All dependencies verified
echo.

echo.
echo ================================
echo Installation Complete!
echo ================================
echo.
echo You can now run: start_system.bat
echo.
pause
exit /b 0

:error
echo [X] Installation verification failed
pause
exit /b 1
