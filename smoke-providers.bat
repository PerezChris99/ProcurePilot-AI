@echo off
setlocal EnableExtensions
REM Root-level, ADK-only live provider verification for Windows.
REM Do not echo private credentials, run tests from backend/ so ../.env loads.
set "PROJECT_ROOT=%~dp0"
set "PYTHON=%PROJECT_ROOT%backend\.venv\Scripts\python.exe"
set "PROVIDER=%~1"
if "%PROVIDER%"=="" set "PROVIDER=all"

if not exist "%PYTHON%" (
  echo [ERROR] Backend Python environment missing.
  echo Run qa\setup.bat from the repository root first.
  exit /b 2
)

pushd "%PROJECT_ROOT%backend" || exit /b 2
echo Checking %PROVIDER% using ProcurePilot ADK and provider clients...
"%PYTHON%" scripts\provider_smoke.py --provider "%PROVIDER%"
set "STATUS=%ERRORLEVEL%"
popd

echo.
if "%STATUS%"=="0" (
  echo [PASS] Selected live provider checks completed.
) else (
  echo [FAIL] Provider checks returned exit code %STATUS%.
  echo Check the safe JSON category and hint above.
)
exit /b %STATUS%
