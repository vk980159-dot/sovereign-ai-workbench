<#
.SYNOPSIS
    Sovereign AI Workbench - Stop Stable Public Share Mode (SIH26117)
.DESCRIPTION
    Gracefully shuts down Cloudflare Named Tunnel and restores local-only operation.
#>

$ErrorActionPreference = "SilentlyContinue"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location -Path $ProjectRoot

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "     SOVEREIGN AI WORKBENCH - STOPPING STABLE PUBLIC SHARE MODE" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan

# Terminate cloudflared tunnel processes
$cfProcs = Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue
if ($cfProcs) {
    $cfProcs | Stop-Process -Force
    Write-Host "[OK] Cloudflare Named Tunnel process(es) terminated." -ForegroundColor Green
} else {
    Write-Host "[INFO] No active Cloudflare tunnel processes found." -ForegroundColor Yellow
}

# Remove public URL file
$pubFile = Join-Path $ProjectRoot ".public_share_url"
if (Test-Path $pubFile) {
    Remove-Item -Force $pubFile
    Write-Host "[OK] Removed .public_share_url registration file." -ForegroundColor Green
}

# Reset environment variables in current session
$env:PUBLIC_SHARE_MODE = ""
$env:PUBLIC_BASE_URL = ""

Write-Host ""
Write-Host "Sovereign AI Workbench has returned to 100% Local Air-Gapped operation." -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Cyan
