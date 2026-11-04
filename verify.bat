@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo.
echo ============================================================
echo  ProcurePilot AI - Local Code Verification
echo ============================================================
if not exist "backend\.venv\Scripts\python.exe" (
    echo [ERROR] Backend environment missing. Run start.bat first.
    exit /b 1
)
where npm >nul 2>nul
if errorlevel 1 (
    echo [ERROR] npm not found. Install Node.js LTS.
    exit /b 1
)
if not exist "frontend\node_modules" (
    echo [ERROR] Frontend dependencies missing. Run start.bat first.
    exit /b 1
)
echo [1/5] Python syntax and importable source check
pushd "backend"
".venv\Scripts\python.exe" -m compileall -q app tests
if errorlevel 1 (
    popd
    echo [FAILED] Python compileall
    exit /b 1
)
popd
echo.
echo [2/5] Backend tests
pushd "backend"
".venv\Scripts\python.exe" -m pytest -q
if errorlevel 1 (
    popd
    echo [FAILED] Backend tests
    exit /b 1
)
popd
echo.
echo [3/5] Frontend lint
pushd "frontend"
call npm run lint
if errorlevel 1 (
    popd
    echo [FAILED] Frontend lint
    exit /b 1
)
echo.
echo [4/5] Frontend tests
call npm test
if errorlevel 1 (
    popd
    echo [FAILED] Frontend tests
    exit /b 1
)
echo.
echo     Frontend Node version and deployment URL tests
call npm run test:deploy-config
if errorlevel 1 (
    popd
    echo [FAILED] Frontend deployment URL tests
    exit /b 1
)
echo.
echo [5/5] Frontend production build
call npm run build
if errorlevel 1 (
    popd
    echo [FAILED] Frontend build
    exit /b 1
)
popd
echo.
echo [PASSED] All local code checks.
echo Provider credentials, live Sandbox checkout and HTTPS webhooks must be checked separately.
exit /b 0
