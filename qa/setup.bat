@echo off
setlocal EnableExtensions
cd /d "%~dp0.."
echo.
echo ============================================================
echo  QA Setup - Dependencies ONLY, no DB changes or app startup
echo ============================================================
echo.
where node >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Install Node.js 22.12+ or 20.19+.
  exit /b 2
)
where npm >nul 2>nul
if errorlevel 1 exit /b 2
node frontend\scripts\check-node-version.cjs
if errorlevel 1 exit /b 2
if not exist "backend\.venv\Scripts\python.exe" (
  python backend\scripts\check_python_version.py >nul 2>nul
  if not errorlevel 1 (
    python -m venv "backend\.venv"
  ) else (
    py -3 backend\scripts\check_python_version.py >nul 2>nul
    if errorlevel 1 (
      echo [ERROR] Python 3.12+ not detected. Check python --version and py -0p.
      exit /b 2
    )
    py -3 -m venv "backend\.venv"
  )
  if errorlevel 1 exit /b 2
)
echo.
echo [1/2] Installing Python requirements...
"backend\.venv\Scripts\python.exe" -m pip install -r "backend\requirements.txt"
if errorlevel 1 (
  echo [FAILED] Python package setup.
  exit /b 1
)
echo.
echo [2/2] Installing frontend requirements...
pushd frontend
if exist package-lock.json (
  call npm ci --no-audit --no-fund
) else (
  echo [NOTICE] No lockfile: npm must resolve compatible versions.
  call npm install --no-audit --no-fund
)
set "NPM_EXIT=%ERRORLEVEL%"
popd
if not "%NPM_EXIT%"=="0" (
  echo [FAILED] Frontend npm setup.
  exit /b 1
)
echo.
echo [READY] Execute test-all.bat or qa\run-all.bat.
echo No server was started and no database was changed.
exit /b 0
