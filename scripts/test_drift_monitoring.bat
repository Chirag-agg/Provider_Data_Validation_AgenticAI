@echo off
echo.
echo ======================================
echo Testing Drift Monitoring Crew
echo ======================================
echo.

REM Check if environment exists
conda env list | findstr "crewai-env" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Environment 'crewai-env' not found!
    echo.
    echo Please run install.bat first.
    echo.
    pause
    exit /b 1
)

echo [OK] Environment found
echo.
echo Running drift monitoring test...
echo.

conda run -n crewai-env python -m provider_data_validation.main drift

echo.
echo Test complete!
echo.
pause
