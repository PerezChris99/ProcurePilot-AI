@echo off
setlocal EnableExtensions
cd /d "%~dp0.."
echo.
echo ============================================================
echo  ProcurePilot AI - Offline Tests and Production Build
echo ============================================================
echo.
if not exist "backend\.venv\Scripts\python.exe" (
  echo [ERROR] Backend virtual environment missing.
  echo Run qa\setup.bat once.
  exit /b 2
)
"backend\.venv\Scripts\python.exe" "qa\run.py" %*
set "QA_EXIT=%ERRORLEVEL%"
echo.
echo Report: qa\reports\summary.md
exit /b %QA_EXIT%
