@echo off
setlocal EnableExtensions

REM ProcurePilot AI - Windows + VS Code local development bootstrap.
REM Run from the VS Code integrated terminal after pulling the perez branch.

cd /d "%~dp0"
set "PROJECT_ROOT=%CD%"

echo.
echo ============================================================
echo  ProcurePilot AI - VS Code Development Setup
echo ============================================================
echo.

where npm >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Node.js and npm were not found on PATH.
    echo Install Node.js LTS, reopen VS Code, and retry.
    pause
    exit /b 1
)

REM Prefer the Python executable already available on PATH.
set "PYTHON_LAUNCHER=python"
python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,12) else 1)" >nul 2>nul
if errorlevel 1 (
    set "PYTHON_LAUNCHER=py -3"
    py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3,12) else 1)" >nul 2>nul
    if errorlevel 1 (
        echo [ERROR] Python 3.12 or newer could not be found.
        echo.
        echo Detected Python commands:
        where python 2>nul
        where py 2>nul
        echo.
        echo Run "python --version" and "py -0p" to inspect installed versions.
        pause
        exit /b 1
    )
)

echo [1/4] Preparing the backend virtual environment...
if not exist "backend\.venv\Scripts\python.exe" (
    %PYTHON_LAUNCHER% -m venv "backend\.venv"
    if errorlevel 1 (
        echo [ERROR] Could not create backend virtual environment.
        pause
        exit /b 1
    )
)

echo.
echo [2/4] Installing Python dependencies...
"backend\.venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
    echo [ERROR] Could not upgrade pip.
    pause
    exit /b 1
)
"backend\.venv\Scripts\python.exe" -m pip install -r "backend\requirements.txt"
if errorlevel 1 (
    echo [ERROR] Python dependency installation failed.
    pause
    exit /b 1
)

echo.
echo [3/4] Preparing local environment files...
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
echo [4/4] Installing frontend dependencies...
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
echo ============================================================
echo  Setup complete. Handing startup to VS Code tasks.
echo.
echo  VS Code will run the frontend production build first.
echo  Backend and frontend integrated terminals start only if
echo  that build succeeds.
echo.
echo  In the task picker, select:
echo  ProcurePilot: Build then Start (VS Code Terminals)
echo.
echo  Frontend: http://localhost:5173
echo  Backend:  http://localhost:8000
echo  API docs: http://localhost:8000/docs
echo ============================================================
echo.

where code >nul 2>nul
if errorlevel 1 (
    echo [ERROR] VS Code command-line launcher "code" is not on PATH.
    echo Open this folder in VS Code, then use Terminal ^> Run Task.
    echo Select: ProcurePilot: Build then Start (VS Code Terminals)
    pause
    exit /b 1
)

code --reuse-window "%PROJECT_ROOT%" --command workbench.action.tasks.runTask
if errorlevel 1 (
    echo [ERROR] Could not invoke the VS Code task picker.
    echo In VS Code, use Terminal ^> Run Task and select:
    echo ProcurePilot: Build then Start (VS Code Terminals)
    pause
    exit /b 1
)

exit /b 0
