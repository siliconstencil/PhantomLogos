@echo off
REM Stop the Watchdog daemon
taskkill /F /IM pythonw.exe /FI "CMDLINE eq *file_watchdog*" 2>nul
echo Watchdog daemon stopped.
