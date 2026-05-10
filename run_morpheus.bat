@echo off
REM Morpheus VRAM Management Daemon (Root Launcher)
REM Launched via: wscript.exe scripts\hide_morpheus.vbs
REM Stop: scripts\stop_morpheus.bat

set ROOT=D:\Hank
cd /d "%ROOT%"
set PYTHONPATH=%ROOT%

if not exist "logs\system\morpheus" mkdir logs\system\morpheus
set PYTHONWARNINGS=ignore::FutureWarning:google.generativeai

echo [%DATE% %TIME%] Starting Morpheus Daemon...
"%ROOT%\.venv\Scripts\pythonw.exe" -u src\clotho\bootstrap.py --daemon >> "logs\system\morpheus\morpheus.log" 2>&1
