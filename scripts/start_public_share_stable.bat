@echo off
REM ==============================================================================
REM Sovereign On-Premise Agentic AI Workbench (SIH26117)
REM Start Stable Public Share Mode with Cloudflare Named Tunnel
REM ==============================================================================

set SCRIPT_DIR=%~dp0..
cd /d "%SCRIPT_DIR%"

set PUBLIC_SHARE_MODE=stable

echo ========================================================================
echo     SOVEREIGN AI WORKBENCH - LAUNCHING STABLE PUBLIC SHARE MODE
echo ========================================================================

REM Activate virtualenv if present
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    python scripts\public_share_runner.py --mode stable %*
) else (
    python scripts\public_share_runner.py --mode stable %*
)

pause
