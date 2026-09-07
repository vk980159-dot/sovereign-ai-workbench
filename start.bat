@echo off
REM ==============================================================================
REM Sovereign On-Premise Agentic AI Workbench (SIH26117)
REM One-Click Air-Gapped Launch Script (Windows Command Prompt / PowerShell)
REM ==============================================================================

echo ========================================================================
echo     SOVEREIGN AI WORKBENCH - 100%% LOCAL AIR-GAPPED BOOT
echo ========================================================================

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

set PYTHONPATH=%SCRIPT_DIR%backend;%PYTHONPATH%
set WORKBENCH_AIR_GAP_STRICT_MODE=True
set HF_HUB_OFFLINE=1
set TRANSFORMERS_OFFLINE=1

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not found in system PATH.
    pause
    exit /b 1
)

if not exist "venv" (
    echo [SETUP] Initializing local isolated virtual environment 'venv'...
    python -m venv venv
)

echo [SETUP] Activating virtual environment...
call venv\Scripts\activate.bat

echo [SETUP] Verifying dependencies from requirements.txt...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt

echo ========================================================================
echo   [SUCCESS] LAUNCHING SOVEREIGN WORKBENCH SERVER
echo   Access Dashboard:   http://127.0.0.1:8000
echo   API Documentation:  http://127.0.0.1:8000/docs
echo ========================================================================

cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level info
pause
