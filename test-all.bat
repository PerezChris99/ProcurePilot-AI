@echo off
setlocal EnableExtensions
call "%~dp0qa\run-all.bat" %*
exit /b %ERRORLEVEL%
