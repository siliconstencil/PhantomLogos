@echo off
REM Stop the File Integrity Watchdog daemon
taskkill /F /IM pythonw.exe /FI "WINDOWTITLE eq file_watchdog*" 2>nul
taskkill /F /FI "IMAGENAME eq pythonw.exe" /FI "CMDLINE eq *file_watchdog*" 2>nul
echo Watchdog daemon stopped.
