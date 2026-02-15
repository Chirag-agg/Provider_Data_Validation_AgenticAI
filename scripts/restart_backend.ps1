# Restart Backend - Auto-detects conda / venv / system python

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Restarting Backend" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Resolve project root (one level up from scripts/)
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
Set-Location $projectRoot

# ---- Detect Python environment ----
$pythonCmd = $null
$envName = $null

# 1) conda env
if (Get-Command conda -ErrorAction SilentlyContinue) {
    $envList = conda env list 2>$null | Out-String
    if ($envList -match "crewai-env") {
        $pythonCmd = "conda run --no-banner -n crewai-env python"
        $envName = "conda (crewai-env)"
    }
}

# 2) .venv
if (-not $pythonCmd -and (Test-Path ".venv\Scripts\python.exe")) {
    $pythonCmd = ".venv\Scripts\python.exe"
    $envName = ".venv"
}

# 3) system python
if (-not $pythonCmd -and (Get-Command python -ErrorAction SilentlyContinue)) {
    $pythonCmd = "python"
    $envName = "system python"
}

if (-not $pythonCmd) {
    Write-Host "[ERROR] No Python found! Run install.bat first." -ForegroundColor Red
    Read-Host "Press Enter to close"
    exit 1
}

Write-Host "[OK] Using: $envName" -ForegroundColor Green
Write-Host ""

# ---- Stop existing backend ----
Write-Host "[1/2] Stopping existing backend..." -ForegroundColor Yellow

# Kill by window title
Get-Process | Where-Object { $_.MainWindowTitle -like "*Provider*Validation*API*" } |
Stop-Process -Force -ErrorAction SilentlyContinue

# Kill anything on port 8000
$connections = netstat -aon 2>$null | Select-String ":8000.*LISTENING"
foreach ($line in $connections) {
    $pid = ($line -split '\s+')[-1]
    if ($pid -match '^\d+$') {
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    }
}

Start-Sleep -Seconds 2
Write-Host "[OK] Existing backend stopped" -ForegroundColor Green
Write-Host ""

# ---- Start backend ----
Write-Host "[2/2] Starting Backend ($envName)..." -ForegroundColor Yellow

Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "Set-Location '$projectRoot'; $pythonCmd -m uvicorn src.provider_data_validation.api:app --reload --host 127.0.0.1 --port 8000"
) -WindowStyle Normal

Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "Backend Restarted!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "API:           http://localhost:8000" -ForegroundColor White
Write-Host "API Docs:      http://localhost:8000/docs" -ForegroundColor White
Write-Host "Environment:   $envName" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to close"
