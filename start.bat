@echo off
setlocal EnableExtensions

REM ProcurePilot AI - Windows local development launcher.
REM Run this file from Explorer or from any Command Prompt / PowerShell location.

cd /d "%~dp0"
set "PROJECT_ROOT=%CD%"

echo.
echo ============================================================
echo  ProcurePilot AI - Local Development Setup
echo ============================================================
echo.

REM Check required tools before changing the environment.
where npm >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Node.js and npm were not found on PATH.
    echo Install the current Node.js LTS release, reopen the terminal, and retry.
    pause
    exit /b 1
)

where py >nul 2>nul
if errorlevel 1 (
    where python >nul 2>nul
    if errorlevel 1 (
        echo [ERROR] Python 3.12+ was not found on PATH.
        echo Install Python 3.12 or newer and enable "Add Python to PATH".
        pause
        exit /b 1
    )
    set "PYTHON_LAUNCHER=python"
) else (
    set "PYTHON_LAUNCHER=py -3.12"
)

%PYTHON_LAUNCHER% --version
if errorlevel 1 (
    echo [ERROR] Python 3.12 could not be launched. Install Python 3.12+.
    pause
    exit /b 1
)

echo.
echo [1/5] Preparing the backend virtual environment...
if not exist "backend\.venv\Scripts\python.exe" (
    %PYTHON_LAUNCHER% -m venv "backend\.venv"
    if errorlevel 1 (
        echo [ERROR] Could not create backend virtual environment.
        pause
        exit /b 1
    )
)

echo.
echo [2/5] Installing Python dependencies...
call "backend\.venv\Scripts\activate.bat"
if errorlevel 1 (
    echo [ERROR] Could not activate the backend virtual environment.
    pause
    exit /b 1
)
python -m pip install --upgrade pip
if errorlevel 1 (
    echo [ERROR] Could not upgrade pip.
    pause
    exit /b 1
)
python -m pip install -r "backend\requirements.txt"
if errorlevel 1 (
    echo [ERROR] Python dependency installation failed.
    pause
    exit /b 1
)


echo.
echo [3/5] Preparing local environment files...
if not exist ".env" (
    copy ".env.example" ".env" >nul
    if errorlevel 1 (
        echo [ERROR] Could not create .env from .env.example.
        pause
        exit /b 1
    )
    echo Created .env. Review DATABASE_URL and add provider credentials when needed.
)
if not exist "frontend\.env" (
    copy "frontend\.env.example" "frontend\.env" >nul
    if errorlevel 1 (
        echo [ERROR] Could not create frontend\.env.
        pause
        exit /b 1
    )
    echo Created frontend\.env.
)

echo.
echo [4/5] Installing frontend dependencies...
pushd "frontend"
if exist "package-lock.json" (
    call npm ci
) else (
    call npm install
)
if errorlevel 1 (
    popd
    echo [ERROR] Frontend dependency installation failed.
    pause
    exit /b 1
)
popd

echo.
echo [5/5] Starting backend and frontend in separate terminal windows...
start "ProcurePilot Backend" /D "%PROJECT_ROOT%\backend" cmd /k "call .venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
start "ProcurePilot Frontend" /D "%PROJECT_ROOT%\frontend" cmd /k "npm run dev -- --host 127.0.0.1"

echo.
echo ============================================================
echo  Startup commands launched.
echo.
echo  Frontend: http://localhost:5173
echo  Backend:  http://localhost:8000
echo  API docs: http://localhost:8000/docs
echo.
echo  IMPORTANT:
echo  - The backend environment file defaults to local PostgreSQL.
echo    Ensure PostgreSQL is running and the procurepilot database
echo    exists, or edit DATABASE_URL in the root .env file.
echo  - Apply database migrations from backend with:
echo      .venv\Scripts\activate
echo      alembic upgrade head
echo  - Provider keys are optional for basic local startup, but
echo    Gemini, Channel3 and PayPal features need valid credentials.
echo  - This script does not install PostgreSQL or create cloud
echo    provider accounts.
echo ============================================================
echo.
pause
exit /b 0
