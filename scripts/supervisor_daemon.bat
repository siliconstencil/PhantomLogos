@echo off
:: Component 9: Supervisor Daemon for Morpheus and SLM services monitoring
title Antigravity Supervisor Daemon
echo [SUPERVISOR] Starting daemon observer...

:loop
tasklist /FI "IMAGENAME eq python.exe" /FO CSV > %TEMP%\python_tasks.txt
findstr /I "bootstrap.py" %TEMP%\python_tasks.txt >nul
if errorlevel 1 (
    echo [%TIME%] [WARNING] Morpheus Daemon (bootstrap.py) is NOT running! Restarting...
    for %%I in ("%~dp0..") do set "ROOT=%%~fI"
    start /B python "%ROOT%\src\clotho\bootstrap.py" --daemon
)

:: Wait 30 seconds before next check
timeout /t 30 /nobreak >nul
goto loop
