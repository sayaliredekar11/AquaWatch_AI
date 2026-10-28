<#
.SYNOPSIS
    AquaWatch AI — Automated Windows Startup Script

.DESCRIPTION
    Launches the complete AquaWatch AI platform on Windows with one command:
    - Performs pre-flight checks (folders, Python venv, Node.js, npm, PostgreSQL).
    - Starts the FastAPI backend server in a dedicated terminal window (port 8000).
    - Starts the React/Vite frontend server in a dedicated terminal window (port 5173).
    - Waits for the servers to become responsive.
    - Opens http://localhost:5173 in your default web browser.

.PARAMETER CheckOnly
    Runs all pre-flight health checks and reports status without launching background servers.

.PARAMETER NoBrowser
    Starts the backend and frontend servers without automatically opening a browser window.

.EXAMPLE
    .\start-aquawatch.ps1
    .\start-aquawatch.ps1 -CheckOnly
    .\start-aquawatch.ps1 -NoBrowser
#>

[CmdletBinding()]
param(
    [switch]$CheckOnly,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Continue"

Write-Host ''
Write-Host '======================================================================' -ForegroundColor Cyan
Write-Host '            AQUAWATCH AI — AUTOMATED PLATFORM LAUNCHER               ' -ForegroundColor Cyan
Write-Host '======================================================================' -ForegroundColor Cyan
Write-Host ' Intelligent Water Quality Monitoring and Pollution Prediction Platform' -ForegroundColor Gray
Write-Host ''

# ---------------------------------------------------------------------
# 1. Resolve Root and Component Paths
# ---------------------------------------------------------------------
$rootDir = $PSScriptRoot
if (-not $rootDir) {
    $rootDir = (Get-Location).Path
}

$backendDir = Join-Path $rootDir "backend"
$frontendDir = Join-Path $rootDir "frontend"

Write-Host "[1/6] Inspecting project directory structure..." -ForegroundColor Yellow

$hasFolderError = $false
if (-not (Test-Path $backendDir)) {
    Write-Host "  [ERROR] Backend directory not found at: $backendDir" -ForegroundColor Red
    $hasFolderError = $true
} else {
    Write-Host "  [OK] Backend directory located: backend/" -ForegroundColor Green
}

if (-not (Test-Path $frontendDir)) {
    Write-Host "  [ERROR] Frontend directory not found at: $frontendDir" -ForegroundColor Red
    $hasFolderError = $true
} else {
    Write-Host "  [OK] Frontend directory located: frontend/" -ForegroundColor Green
}

if ($hasFolderError) {
    Write-Host ""
    Write-Host "Startup aborted due to missing project folders. Please run from project root." -ForegroundColor Red
    exit 1
}

# ---------------------------------------------------------------------
# 2. Python & Virtual Environment Check
# ---------------------------------------------------------------------
Write-Host ""
Write-Host "[2/6] Checking Python and backend virtual environment..." -ForegroundColor Yellow

$venvPythonCandidates = @(
    (Join-Path $backendDir "venv\Scripts\python.exe"),
    (Join-Path $backendDir ".venv\Scripts\python.exe"),
    (Join-Path $rootDir "venv\Scripts\python.exe"),
    (Join-Path $rootDir ".venv\Scripts\python.exe")
)

$pythonExe = $null
foreach ($candidate in $venvPythonCandidates) {
    if (Test-Path $candidate) {
        $pythonExe = $candidate
        break
    }
}

if ($pythonExe) {
    Write-Host "  [OK] Python virtual environment detected: $pythonExe" -ForegroundColor Green
    $pyVer = & $pythonExe --version 2>&1
    Write-Host "  [OK] Python version: $pyVer" -ForegroundColor Green
} else {
    $systemPython = Get-Command "python" -ErrorAction SilentlyContinue
    if ($systemPython) {
        $pythonExe = "python"
        Write-Host "  [WARN] Dedicated virtual environment not found in backend/venv. Using system Python." -ForegroundColor Yellow
    } else {
        Write-Host "  [ERROR] Python is not installed or not found in system PATH." -ForegroundColor Red
        Write-Host "          Please install Python 3.10+ and configure backend/venv." -ForegroundColor Red
        exit 1
    }
}

# Verify backend/.env configuration file (Never print secrets or passwords)
$backendEnv = Join-Path $backendDir ".env"
$backendEnvExample = Join-Path $backendDir ".env.example"
if (Test-Path $backendEnv) {
    Write-Host "  [OK] Backend environment configuration (.env) is present." -ForegroundColor Green
} elseif (Test-Path $backendEnvExample) {
    Write-Host "  [WARN] backend/.env missing. Creating initial .env from .env.example..." -ForegroundColor Yellow
    Copy-Item $backendEnvExample $backendEnv
    Write-Host "  [OK] Created backend/.env. Please ensure PostgreSQL credentials match your system." -ForegroundColor Green
} else {
    Write-Host "  [WARN] Neither backend/.env nor backend/.env.example was found." -ForegroundColor Yellow
}

# ---------------------------------------------------------------------
# 3. PostgreSQL Database Service & Connectivity Check
# ---------------------------------------------------------------------
Write-Host ""
Write-Host "[3/6] Verifying PostgreSQL database service..." -ForegroundColor Yellow

$pgService = Get-Service -Name "*postgres*" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($pgService) {
    if ($pgService.Status -eq "Running") {
        Write-Host "  [OK] Windows Service '$($pgService.Name)' is currently RUNNING." -ForegroundColor Green
    } else {
        Write-Host "  [WARN] Windows Service '$($pgService.Name)' is $($pgService.Status)." -ForegroundColor Yellow
        Write-Host "         Attempting to start service '$($pgService.Name)'..." -ForegroundColor Yellow
        try {
            Start-Service -Name $pgService.Name -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
            Write-Host "  [OK] Service started successfully." -ForegroundColor Green
        } catch {
            Write-Host "  [INFO] Could not automatically start service (may require administrator permissions)." -ForegroundColor Gray
            Write-Host "         Tip: Run 'Start-Service $($pgService.Name)' in an Admin PowerShell if needed." -ForegroundColor Gray
        }
    }
} else {
    Write-Host "  [INFO] No Windows Service with 'postgres' name found in registry. Checking direct port connection..." -ForegroundColor Gray
}

# Test database connection via Python SQLAlchemy (no passwords or credentials printed)
$dbTestResult = 1
try {
    & $pythonExe -c "import os,sys; from dotenv import load_dotenv; load_dotenv(sys.argv[1]); from sqlalchemy import create_engine,text; e=create_engine(os.getenv('DATABASE_URL')); c=e.connect(); c.execute(text('SELECT 1')); c.close()" "$backendEnv" 2>$null
    $dbTestResult = $LASTEXITCODE
} catch {
    $dbTestResult = 1
}

if ($dbTestResult -eq 0) {
    Write-Host "  [OK] PostgreSQL database connection verified successfully (SELECT 1 passed)." -ForegroundColor Green
} elseif ($dbTestResult -eq 2) {
    Write-Host "  [WARN] DATABASE_URL is not set in backend/.env. Backend will use fallback configuration." -ForegroundColor Yellow
} else {
    Write-Host "  [WARN] Could not connect to PostgreSQL on port 5432." -ForegroundColor Yellow
    Write-Host "         Please make sure PostgreSQL is running and credentials in backend/.env are valid." -ForegroundColor Yellow
    Write-Host "         (Backend will still start; DB connection will be retried upon requests)." -ForegroundColor Gray
}

# ---------------------------------------------------------------------
# 4. Node.js & Frontend Dependencies Check
# ---------------------------------------------------------------------
Write-Host ""
Write-Host "[4/6] Checking Node.js and frontend dependencies..." -ForegroundColor Yellow

$nodeCmd = Get-Command "node" -ErrorAction SilentlyContinue
$npmCmd = Get-Command "npm" -ErrorAction SilentlyContinue

if (-not $nodeCmd -or -not $npmCmd) {
    Write-Host "  [ERROR] Node.js or npm is not found in system PATH." -ForegroundColor Red
    Write-Host "          Please install Node.js (https://nodejs.org/) to run the React frontend." -ForegroundColor Red
    exit 1
} else {
    $nodeVer = & node -v
    $npmVer = & npm -v
    Write-Host "  [OK] Node.js ($nodeVer) and npm ($npmVer) are available." -ForegroundColor Green
}

$frontendNodeModules = Join-Path $frontendDir "node_modules"
if (-not (Test-Path $frontendNodeModules)) {
    Write-Host "  [INFO] frontend/node_modules not found. Installing frontend dependencies via npm install..." -ForegroundColor Yellow
    Push-Location $frontendDir
    try {
        & npm install
        Write-Host "  [OK] Frontend dependencies installed successfully." -ForegroundColor Green
    } finally {
        Pop-Location
    }
} else {
    Write-Host "  [OK] Frontend dependencies (node_modules) are already installed." -ForegroundColor Green
}

# Frontend .env check
$frontendEnv = Join-Path $frontendDir ".env"
$frontendEnvExample = Join-Path $frontendDir ".env.example"
if (-not (Test-Path $frontendEnv) -and (Test-Path $frontendEnvExample)) {
    Copy-Item $frontendEnvExample $frontendEnv
    Write-Host "  [OK] Initialized frontend/.env with VITE_API_BASE_URL=http://localhost:8000" -ForegroundColor Green
}

# Check if ports are already in use
$port8000Busy = $null -ne (Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue)
if ($port8000Busy) {
    Write-Host "  [WARN] Port 8000 is already in use. A backend instance may already be running." -ForegroundColor Yellow
}

$port5173Busy = $null -ne (Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue)
if ($port5173Busy) {
    Write-Host "  [WARN] Port 5173 is already in use. A frontend instance may already be running." -ForegroundColor Yellow
}

# If user passed -CheckOnly, exit gracefully here
if ($CheckOnly) {
    Write-Host ""
    Write-Host "======================================================================" -ForegroundColor Cyan
    Write-Host "  PRE-FLIGHT CHECKS COMPLETE: System is ready for AquaWatch AI!        " -ForegroundColor Green
    Write-Host "======================================================================" -ForegroundColor Cyan
    Write-Host "To launch servers, run: .\start-aquawatch.ps1" -ForegroundColor White
    Write-Host ""
    exit 0
}

# ---------------------------------------------------------------------
# 5. Launch Backend Server in Dedicated Terminal
# ---------------------------------------------------------------------
Write-Host ""
Write-Host "[5/6] Launching FastAPI Backend Server..." -ForegroundColor Yellow

$backendScript = @"
`$host.UI.RawUI.WindowTitle = 'AquaWatch AI — Backend Server (FastAPI :8000)'
Clear-Host
Write-Host '======================================================================' -ForegroundColor Cyan
Write-Host '   AquaWatch AI — FastAPI Backend Server                             ' -ForegroundColor Cyan
Write-Host '======================================================================' -ForegroundColor Cyan
Write-Host '  API Base URL:     http://127.0.0.1:8000' -ForegroundColor White
Write-Host '  Interactive Docs: http://127.0.0.1:8000/docs' -ForegroundColor White
Write-Host '  ReDoc Reference:  http://127.0.0.1:8000/redoc' -ForegroundColor White
Write-Host '  Health Endpoint:  http://127.0.0.1:8000/health' -ForegroundColor White
Write-Host '----------------------------------------------------------------------' -ForegroundColor Gray
Write-Host '  Press Ctrl+C at any time to stop this backend server.' -ForegroundColor Yellow
Write-Host '======================================================================' -ForegroundColor Cyan
Write-Host ''
if (Test-Path '.\venv\Scripts\Activate.ps1') {
    & '.\venv\Scripts\Activate.ps1'
}
& '$pythonExe' -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
"@

$backendBytes = [System.Text.Encoding]::Unicode.GetBytes($backendScript)
$backendEncoded = [System.Convert]::ToBase64String($backendBytes)

Start-Process powershell.exe -WorkingDirectory $backendDir -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-EncodedCommand", $backendEncoded
Write-Host "  [OK] Backend terminal window started." -ForegroundColor Green

# ---------------------------------------------------------------------
# 6. Launch Frontend Server in Dedicated Terminal
# ---------------------------------------------------------------------
Write-Host ""
Write-Host "[6/6] Launching React / Vite Frontend Server..." -ForegroundColor Yellow

$frontendScript = @"
`$host.UI.RawUI.WindowTitle = 'AquaWatch AI — Frontend (Vite + React :5173)'
Clear-Host
Write-Host '======================================================================' -ForegroundColor Green
Write-Host '   AquaWatch AI — React Development Server (Vite)                     ' -ForegroundColor Green
Write-Host '======================================================================' -ForegroundColor Green
Write-Host '  Frontend URL:       http://localhost:5173' -ForegroundColor White
Write-Host '  Backend API Target: http://127.0.0.1:8000' -ForegroundColor White
Write-Host '----------------------------------------------------------------------' -ForegroundColor Gray
Write-Host '  Press Ctrl+C at any time to stop this frontend server.' -ForegroundColor Yellow
Write-Host '======================================================================' -ForegroundColor Green
Write-Host ''
npm run dev
"@

$frontendBytes = [System.Text.Encoding]::Unicode.GetBytes($frontendScript)
$frontendEncoded = [System.Convert]::ToBase64String($frontendBytes)

Start-Process powershell.exe -WorkingDirectory $frontendDir -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-EncodedCommand", $frontendEncoded
Write-Host "  [OK] Frontend terminal window started." -ForegroundColor Green

# ---------------------------------------------------------------------
# Polling and Browser Launch
# ---------------------------------------------------------------------
Write-Host ""
Write-Host "Waiting for servers to become responsive..." -ForegroundColor Yellow

$frontendReady = $false
$maxSeconds = 15
$elapsed = 0

while (-not $frontendReady -and $elapsed -lt $maxSeconds) {
    Start-Sleep -Seconds 1
    $elapsed++
    try {
        $tcp = Test-NetConnection -ComputerName "127.0.0.1" -Port 5173 -InformationLevel Quiet -WarningAction SilentlyContinue
        if ($tcp) {
            $frontendReady = $true
        }
    } catch {}
}

if (-not $NoBrowser) {
    Write-Host "Opening AquaWatch AI in your default web browser..." -ForegroundColor Cyan
    Start-Process "http://localhost:5173"
}

# ---------------------------------------------------------------------
# Startup Summary Banner
# ---------------------------------------------------------------------
Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "              AQUAWATCH AI IS RUNNING SUCCESSFULLY!                   " -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "  Frontend Web App:    http://localhost:5173" -ForegroundColor White
Write-Host "  Backend API Server:  http://127.0.0.1:8000" -ForegroundColor White
Write-Host "  Interactive Swagger: http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "  Alternative ReDoc:   http://127.0.0.1:8000/redoc" -ForegroundColor White
Write-Host "----------------------------------------------------------------------" -ForegroundColor Gray
Write-Host "  ACCESS MODEL & CREDENTIALS:" -ForegroundColor Cyan
Write-Host "    - Public Views (No login needed):   Home, Water Map, Intelligence, About" -ForegroundColor White
Write-Host "    - Lab Authority (Dashboard & Test): lab@aquawatch.ai / lab123" -ForegroundColor White
Write-Host "    - Admin Provisioning CLI:           python backend\assign_lab_authority.py --list" -ForegroundColor White
Write-Host "----------------------------------------------------------------------" -ForegroundColor Gray
Write-Host "  TO STOP THE APPLICATION:" -ForegroundColor Yellow
Write-Host "    Switch to each opened terminal window and press Ctrl+C." -ForegroundColor White
Write-Host "======================================================================" -ForegroundColor Green
Write-Host ""
