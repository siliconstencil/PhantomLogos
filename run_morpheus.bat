@echo off
REM Morpheus VRAM Management Daemon (PowerShell Launcher)
REM Launched via: wscript.exe scripts\hide_morpheus.vbs
REM Stop: scripts\stop_morpheus.bat

set ROOT=D:\Hank
set LOG_DIR=%ROOT%\logs\system\morpheus
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set LOG_FILE=%LOG_DIR%\morpheus.log
set PYTHONW=%ROOT%\.venv\Scripts\pythonw.exe
set SCRIPT=%ROOT%\src\clotho\bootstrap.py

if not exist "%PYTHONW%" echo [HATA] pythonw.exe bulunamadi & exit /b 1
if not exist "%SCRIPT%" echo [HATA] bootstrap.py bulunamadi & exit /b 1

echo [%DATE% %TIME%] Morpheus Daemon baslatiliyor...

powershell -NoProfile -ExecutionPolicy Bypass -Command "$env:PYTHONPATH='%ROOT%'; $env:PYTHONWARNINGS='ignore::FutureWarning:google.generativeai'; $p=Start-Process -FilePath '%PYTHONW%' -ArgumentList '-u','%SCRIPT%','--daemon' -WorkingDirectory '%ROOT%' -WindowStyle Hidden -PassThru -ErrorAction Stop; Add-Content '%LOG_FILE%' ''; Add-Content '%LOG_FILE%' ('[{0}] ====== Yeni oturum basliyo PID:{1} ======' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'),$p.Id); Start-Sleep 12; if($p.HasExited){Write-Host ('[HATA] Morpheus PID:{0} oldu. Exit:{1}' -f $p.Id,$p.ExitCode); Get-Content '%LOG_FILE%' -Tail 10|%%{Write-Host ('  {0}' -f $_)}; exit 1}else{Write-Host ('[OK] Morpheus calisiyor (PID:{0}).' -f $p.Id)}"
