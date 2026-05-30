@echo off
REM Morpheus VRAM Management Daemon (PowerShell Launcher)
REM Launched via: wscript.exe scripts\hide_morpheus.vbs
REM Stop: scripts\stop_morpheus.bat

set ROOT=%~dp0
if "%ROOT:~-1%"=="\" set ROOT=%ROOT:~0,-1%
set LOG_DIR=%ROOT%\logs\system\morpheus
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set LOG_FILE=%LOG_DIR%\morpheus.log
set PYTHONW=%ROOT%\.venv\Scripts\pythonw.exe
set SCRIPT=%ROOT%\src\clotho\bootstrap.py

if not exist "%PYTHONW%" echo [ERROR] pythonw.exe not found & exit /b 1
if not exist "%SCRIPT%" echo [ERROR] bootstrap.py not found & exit /b 1

echo [%DATE% %TIME%] Starting Morpheus Daemon...

powershell -NoProfile -ExecutionPolicy Bypass -Command "$env:PYTHONPATH='%ROOT%'; $env:PYTHONWARNINGS='ignore::FutureWarning:google.generativeai'; $p=Start-Process -FilePath '%PYTHONW%' -ArgumentList '-u','%SCRIPT%','--daemon' -WorkingDirectory '%ROOT%' -WindowStyle Hidden -PassThru -ErrorAction Stop; Add-Content '%LOG_FILE%' ''; Add-Content '%LOG_FILE%' ('[{0}] ====== New session starting PID:{1} ======' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'),$p.Id); Start-Sleep 12; if($p.HasExited){Write-Host ('[ERROR] Morpheus PID:{0} terminated. Exit:{1}' -f $p.Id,$p.ExitCode); Get-Content '%LOG_FILE%' -Tail 10|%%{Write-Host ('  {0}' -f $_)}; exit 1}else{Write-Host ('[OK] Morpheus is running (PID:{0}).' -f $p.Id)}"
