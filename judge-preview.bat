@echo off
setlocal EnableExtensions
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 goto python_launcher
where python >nul 2>nul
if not errorlevel 1 goto python_direct
echo [ERROR] Install Python 3.12+ before running the judge preview.
exit /b 1

:python_launcher
py -3 "%~dp0judge-preview.py" %*
exit /b %errorlevel%

:python_direct
python "%~dp0judge-preview.py" %*
exit /b %errorlevel%
