# start_all.ps1 - Launch server + Expo frontend (all agents on port 8000)
# Usage: .\start_all.ps1

$ErrorActionPreference = "Continue"
$root = $PSScriptRoot
if (-not $root) { $root = Get-Location }

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  HealthScan Multi-Agent Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Activate venv if it exists
$venvActivate = Join-Path $root ".venv\Scripts\Activate.ps1"
$activateCmd = ""
if (Test-Path $venvActivate) {
    $activateCmd = ". '$venvActivate'; "
    Write-Host "[OK] Virtual environment found" -ForegroundColor Green
} else {
    Write-Host "[WARN] No .venv found - using system Python" -ForegroundColor Yellow
}

# Single server - all agents mounted on port 8000
$scriptPath = Join-Path $root "backend\server.py"
if (-not (Test-Path $scriptPath)) {
    Write-Host "[ERROR] server.py not found" -ForegroundColor Red
    exit 1
}

$pids = @()

Write-Host "[START] HealthScan API (all agents) on port 8000..." -ForegroundColor Green
$backendDir = Join-Path $root "backend"
$serverCmd = "${activateCmd}cd '$backendDir'; python 'server.py'"
$proc = Start-Process powershell -ArgumentList "-NoExit", "-Command", $serverCmd -PassThru
$pids += $proc.Id
Start-Sleep -Milliseconds 500

Write-Host ""
Write-Host "Backend started on port 8000!" -ForegroundColor Green
Write-Host ""
Write-Host "  API + all agents:   http://localhost:8000" -ForegroundColor White
Write-Host "    Doctor:           /agent/doctor/analyze" -ForegroundColor DarkGray
Write-Host "    Fitness:          /agent/fitness/analyze" -ForegroundColor DarkGray
Write-Host "    Health:           /agent/health/analyze" -ForegroundColor DarkGray
Write-Host "    Nutritionist:     /agent/nutritionist/analyze" -ForegroundColor DarkGray
Write-Host "    Chemi:            /agent/chemi/analyze" -ForegroundColor DarkGray
Write-Host ""

# Start Expo frontend
Write-Host "[START] Expo frontend..." -ForegroundColor Green
$expoCmd = "cd '$root'; npx expo start"
$expoProc = Start-Process powershell -ArgumentList "-NoExit", "-Command", $expoCmd -PassThru
$pids += $expoProc.Id

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  All services running!" -ForegroundColor Cyan
Write-Host "  Press Ctrl+C in each window to stop" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Process IDs: $($pids -join ', ')"
Write-Host "To stop all:" -ForegroundColor DarkGray
foreach ($p in $pids) { Write-Host "  Stop-Process -Id $p" -ForegroundColor DarkGray }
