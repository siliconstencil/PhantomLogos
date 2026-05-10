@echo off
REM File Integrity Watchdog Daemon
REM Launched via: wscript.exe scripts\hide_watchdog.vbs
REM Stop:  scripts\stop_watchdog_daemon.bat

set ROOT=D:\Hank
cd /d "%ROOT%"
set PYTHONPATH=%ROOT%

if not exist "logs\system\watchdog" mkdir logs\system\watchdog

echo [%DATE% %TIME%] Starting File Integrity Watchdog...
"%ROOT%\.venv\Scripts\pythonw.exe" -u src\lachesis\file_watchdog.py --root "%ROOT%" >> "logs\system\watchdog\watchdog.log" 2>&1
