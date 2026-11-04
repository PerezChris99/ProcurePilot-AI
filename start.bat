@echo off
setlocal EnableExtensions

REM ProcurePilot AI - Windows local development bootstrap.
REM Run from PowerShell or a VS Code terminal. This script installs dependencies,
REM then opens a dedicated VS Code window. The workspace-folder task starts the
REM build gate and application terminals automatically after workspace trust.

cd /d "%~dp0"
set "PROJECT_ROOT=%CD%"

echo.
echo ============================================================
echo  ProcurePilot AI - Local Development Setup
echo ============================================================
echo.

where npm >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Node.js and npm were not found on PATH.
    echo Install Node.js LTS, reopen your terminal, and retry.
    pause
    exit /b 1
)

REM Vite 7 requires Node 20.19+ or 22.12+. Fail before installing dependencies.
where node >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Node.js was not found on PATH.
    pause
    exit /b 1
)
node "%PROJECT_ROOT%\frontend\scripts\check-node-version.cjs"
if errorlevel 1 (
    echo [ERROR] Node.js does not meet the minimum Vite 7 version.
    echo Install Node.js 20.19 or newer, or Node.js 22.12 or newer.
    node --version
    pause
    exit /b 1
)

set "PYTHON_LAUNCHER=python"
python "%PROJECT_ROOT%\backend\scripts\check_python_version.py" >nul 2>nul
if errorlevel 1 (
    set "PYTHON_LAUNCHER=py -3"
    py -3 "%PROJECT_ROOT%\backend\scripts\check_python_version.py" >nul 2>nul
    if errorlevel 1 (
        echo [ERROR] Python 3.12 or newer could not be found.
        echo Run "python --version" and "py -0p" to inspect installed versions.
        pause
        exit /b 1
    )
)

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
    echo Found package-lock.json. Attempting a clean, reproducible install...
    call npm ci --no-audit --no-fund
    if errorlevel 1 (
        echo.
        echo [WARNING] npm ci rejected the local lockfile.
        echo Reconciling it with package.json using npm install...
        call npm install --no-audit --no-fund
    )
) else (
    echo No package-lock.json found. Resolving dependencies from package.json...
    call npm install --no-audit --no-fund
)
if errorlevel 1 (
    popd
    echo [ERROR] Frontend dependency installation failed.
    echo Review the npm error above, resolve it, and run start.bat again.
    pause
    exit /b 1
)
popd

echo.
echo [5/5] Applying database migrations...
pushd "backend"
"%PROJECT_ROOT%\backend\.venv\Scripts\python.exe" -m alembic upgrade head
if errorlevel 1 (
    popd
    echo [ERROR] Database migrations failed. The application was not started.
    echo Check PostgreSQL is running, DATABASE_URL in the root .env is correct,
    echo and the procurepilot database exists. Then rerun start.bat.
    pause
    exit /b 1
)
popd

echo.
echo ============================================================
echo  Dependencies and database migrations are ready.
echo.
echo  Opening ProcurePilot in a dedicated VS Code window.
echo  VS Code will automatically:
echo    1. Run the frontend production build.
echo    2. Confirm database migrations are current.
echo    3. Start the backend terminal if setup succeeds.
echo    4. Start the frontend terminal when the backend is ready.
echo.
echo  First run: trust this workspace and allow automatic tasks.
echo  Frontend: http://localhost:5173
echo  Backend:  http://localhost:8000
echo  API docs: http://localhost:8000/docs
echo ============================================================
echo.

where code >nul 2>nul
if errorlevel 1 (
    echo [ERROR] VS Code command-line launcher "code" is not on PATH.
    echo Open VS Code, press Ctrl+Shift+P, and run:
    echo Shell Command: Install 'code' command in PATH
    echo Then reopen the terminal and run start.bat again.
    pause
    exit /b 1
)

code --new-window "%PROJECT_ROOT%"
if errorlevel 1 (
    echo [ERROR] Could not open the project in VS Code.
    echo Run "code --help" to diagnose the VS Code command-line installation.
    pause
    exit /b 1
)

exit /b 0
