<#
.SYNOPSIS
    Sovereign AI Workbench - Start Public Share Mode (SIH26117)
.DESCRIPTION
    PowerShell launcher for isolated public access (Tailscale Funnel or Cloudflare Quick Tunnel)
    routing securely to the local FastAPI backend (127.0.0.1:8000).
    Enforces that local AI models, database, and system files remain strictly on-premise.
#>

param(
    [string]$PublicUrl = ""
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location -Path $ProjectRoot

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "     SOVEREIGN AI WORKBENCH - LAUNCHING PUBLIC SHARE MODE" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan

# Set environment variable if parameter provided
if ($PublicUrl) {
    $env:PUBLIC_BASE_URL = $PublicUrl
}

$VenvPython = Join-Path $ProjectRoot "venv\Scripts\python.exe"
$RunnerScript = Join-Path $ProjectRoot "scripts\public_share_runner.py"

$ArgsList = @($RunnerScript)
if ($env:PUBLIC_BASE_URL) {
    Write-Host "[CONFIG] Public Base URL configured: $env:PUBLIC_BASE_URL" -ForegroundColor Green
    $ArgsList += @("--url", $env:PUBLIC_BASE_URL)
}

if (Test-Path $VenvPython) {
    Write-Host "[INIT] Using virtual environment Python: $VenvPython" -ForegroundColor Green
    & $VenvPython @ArgsList
} else {
    Write-Host "[INIT] Using system Python..." -ForegroundColor Yellow
    python @ArgsList
}
