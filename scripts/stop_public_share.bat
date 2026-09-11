@echo off
REM ==============================================================================
REM Sovereign On-Premise Agentic AI Workbench (SIH26117)
REM Stop Public Share Mode and Close Cloudflare Tunnel
REM ==============================================================================

set SCRIPT_DIR=%~dp0..
cd /d "%SCRIPT_DIR%"

echo ========================================================================
echo     SOVEREIGN AI WORKBENCH - STOPPING PUBLIC SHARE MODE
echo ========================================================================

REM Kill cloudflared tunnel processes
taskkill /F /IM cloudflared.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Cloudflare tunnel process terminated successfully.
) else (
    echo [INFO] No active cloudflared tunnel process found.
)

REM Remove public URL registration file
if exist ".public_share_url" (
    del /f /q ".public_share_url"
    echo [OK] Removed .public_share_url tracking file.
)

echo.
echo Sovereign AI Workbench has returned to 100%% Local-Only operation.
echo ========================================================================
pause
