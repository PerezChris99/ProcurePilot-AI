@echo off
setlocal EnableExtensions
cd /d "%~dp0..\frontend"
echo.
echo ============================================================
echo  ProcurePilot AI - Strict Deployment Production Build
echo ============================================================
echo.
where npm >nul 2>nul
if errorlevel 1 (
  echo [ERROR] npm was not found. Install Node.js and run qa\setup.bat.
  exit /b 2
)
if not exist node_modules (
  echo [ERROR] Frontend dependencies missing. Run qa\setup.bat.
  exit /b 2
)
node scripts\check-node-version.cjs
if errorlevel 1 exit /b 2
echo.
echo Checking VITE_API_BASE_URL and building for public deployment...
echo This build refuses localhost, HTTP and malformed API endpoints.
call npm run build:deploy
if errorlevel 1 (
  echo [FAILED] Production build. Review the error above.
  exit /b 1
)
if not exist dist\index.html (
  echo [FAILED] Vite returned success but dist\index.html was not produced.
  exit /b 1
)
echo.
echo [PASSED] Strict public production build.
echo Output: frontend\dist
echo NOTE: The build is not hosted and real provider transactions are not tested.
exit /b 0
