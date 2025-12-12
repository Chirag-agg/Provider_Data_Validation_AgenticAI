@echo off
echo.
echo ======================================
echo Provider Validation - Test All Crews
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

echo Testing all crews sequentially...
echo.

echo ============================================
echo Test 1: Data Validation Crew
echo ============================================
echo.
conda run -n crewai-env python -m provider_data_validation.main validation
echo.

echo.
echo ============================================
echo Test 2: Drift Monitoring Crew
echo ============================================
echo.
conda run -n crewai-env python -m provider_data_validation.main drift
echo.

echo.
echo ============================================
echo All Tests Complete!
echo ============================================
echo.
pause
