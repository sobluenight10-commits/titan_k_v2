@echo off
title Refresh Olympus Dashboard
cd /d "%~dp0"

echo.
echo  Refreshing Olympus (OLYMPUS_LIVE.html)...
echo.

py refresh_olympus.py %*
if errorlevel 1 (
    python refresh_olympus.py %*
)
pause
