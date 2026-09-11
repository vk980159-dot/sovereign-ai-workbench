@echo off
REM ==============================================================================
REM Sovereign On-Premise Agentic AI Workbench (SIH26117)
REM Start Public Share Mode with Secure Cloudflare Tunnel
REM ==============================================================================

set SCRIPT_DIR=%~dp0..
cd /d "%SCRIPT_DIR%"

echo ========================================================================
echo     SOVEREIGN AI WORKBENCH - LAUNCHING PUBLIC SHARE MODE
echo ========================================================================

REM Activate virtualenv if present
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    python scripts\public_share_runner.py
) else (
    python scripts\public_share_runner.py
)

pause
