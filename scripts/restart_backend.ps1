# Restart Backend with CrewAI
Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Restarting Backend with CrewAI" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Stop existing backend
Write-Host "[1/2] Stopping existing backend..." -ForegroundColor Yellow
Get-Process | Where-Object {$_.MainWindowTitle -like "*Provider Data Validation API*"} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Write-Host "[OK] Existing backend stopped" -ForegroundColor Green
Write-Host ""

# Start backend with conda
Write-Host "[2/2] Starting Backend with CrewAI..." -ForegroundColor Yellow
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptPath'; conda activate crewai-env; python -m uvicorn src.provider_data_validation.api:app --reload --host 127.0.0.1 --port 8000" -WindowStyle Normal
Write-Host ""

Write-Host "================================" -ForegroundColor Green
Write-Host "Backend Restarted!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "API:           http://localhost:8000" -ForegroundColor White
Write-Host "API Docs:      http://localhost:8000/docs" -ForegroundColor White
Write-Host "Environment:   crewai-env (with CrewAI)" -ForegroundColor White
Write-Host ""
Write-Host "Backend is now running with AI validation support!" -ForegroundColor Green
Write-Host ""
Read-Host "Press Enter to close"
