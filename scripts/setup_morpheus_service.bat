@echo off
echo --- Antigravity: Morpheus Daemon Windows Startup Setup ---
SET TASKNAME=AntigravityMorpheusDaemon
SET WRAPPER=D:\Hank\scripts\hide_morpheus.vbs

schtasks /create /tn "%TASKNAME%" /tr "wscript.exe \"%WRAPPER%\"" /sc onlogon /rl highest /f /it

if %ERRORLEVEL% EQU 0 (
    echo [PASS] Task created successfully.
    echo The daemon will run via hide_morpheus.vbs in HIDDEN mode.
    echo To start it now: schtasks /run /tn "%TASKNAME%"
) else (
    echo [FAIL] Could not create task. Please run as Administrator.
)
pause
