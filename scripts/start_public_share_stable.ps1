<#
.SYNOPSIS
    Sovereign AI Workbench - Start Stable Public Share Mode (SIH26117)
.DESCRIPTION
    Launches Cloudflare Named Tunnel pointing to local FastAPI backend (127.0.0.1:8000).
    Enforces that local AI models, database, and system files remain strictly on-premise.
    Requires CLOUDFLARE_TUNNEL_TOKEN or CLOUDFLARE_TUNNEL_NAME.
#>

param(
    [string]$Token = "",
    [string]$Name = "",
    [string]$PublicUrl = ""
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location -Path $ProjectRoot

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "  SOVEREIGN AI WORKBENCH - LAUNCHING STABLE PUBLIC SHARE (NAMED TUNNEL)" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan

# Propagate parameters to environment if provided
if ($Token) { $env:CLOUDFLARE_TUNNEL_TOKEN = $Token }
if ($Name) { $env:CLOUDFLARE_TUNNEL_NAME = $Name }
if ($PublicUrl) { $env:PUBLIC_BASE_URL = $PublicUrl }
$env:PUBLIC_SHARE_MODE = "stable"

# Check if credentials are present
$activeToken = $env:CLOUDFLARE_TUNNEL_TOKEN
$activeName = $env:CLOUDFLARE_TUNNEL_NAME

if (-not $activeToken -and -not $activeName) {
    Write-Host "`n============================================================================" -ForegroundColor Red
    Write-Host " [BLOCKED] STABLE HOSTNAME REQUIRES CLOUDFLARE NAMED TUNNEL CONFIGURATION" -ForegroundColor Red
    Write-Host "============================================================================" -ForegroundColor Red
    Write-Host " Reason: Stable named tunnel mode was requested, but neither"
    Write-Host "         CLOUDFLARE_TUNNEL_TOKEN nor CLOUDFLARE_TUNNEL_NAME was provided.`n"
    Write-Host " Operator Setup Instructions to activate a Stable Named Tunnel:"
    Write-Host " -----------------------------------------------------------------"
    Write-Host " 1. Log in to your Cloudflare Zero Trust dashboard:"
    Write-Host "      https://one.dash.cloudflare.com/"
    Write-Host " 2. Navigate to Networks > Tunnels > Add a Tunnel."
    Write-Host " 3. Choose 'Cloudflare' connector, name it (e.g. 'sovereign-workbench')."
    Write-Host " 4. Copy the tunnel token provided in the connector installation section."
    Write-Host " 5. In the tunnel's 'Public Hostname' tab, add a route:"
    Write-Host "      Subdomain/Domain: e.g. ai.yourdomain.com"
    Write-Host "      Type: HTTP"
    Write-Host "      URL: 127.0.0.1:8000"
    Write-Host " 6. Configure environment variables (or add to your .env file):"
    Write-Host "      `$env:CLOUDFLARE_TUNNEL_TOKEN = `"your_tunnel_token_here`""
    Write-Host "      `$env:PUBLIC_BASE_URL = `"https://ai.yourdomain.com`""
    Write-Host "      `$env:PUBLIC_SHARE_MODE = `"stable`""
    Write-Host " 7. Launch stable mode:"
    Write-Host "      .\scripts\start_public_share_stable.ps1 -Token `"your_tunnel_token`""
    Write-Host "      # OR with environment variable set:"
    Write-Host "      .\scripts\start_public_share_stable.ps1`n"
    Write-Host " Fallback to Quick Tunnel (ephemeral trycloudflare.com URL):"
    Write-Host "      .\scripts\start_public_share.ps1"
    Write-Host "============================================================================`n"
    exit 2
}

$VenvPython = Join-Path $ProjectRoot "venv\Scripts\python.exe"
$RunnerScript = Join-Path $ProjectRoot "scripts\public_share_runner.py"

$ArgsList = @($RunnerScript, "--mode", "stable")
if ($activeToken) { $ArgsList += @("--token", $activeToken) }
if ($activeName) { $ArgsList += @("--name", $activeName) }
if ($env:PUBLIC_BASE_URL) { $ArgsList += @("--url", $env:PUBLIC_BASE_URL) }

if (Test-Path $VenvPython) {
    Write-Host "[INIT] Using virtual environment Python: $VenvPython" -ForegroundColor Green
    & $VenvPython @ArgsList
} else {
    Write-Host "[INIT] Using system Python..." -ForegroundColor Yellow
    python @ArgsList
}
