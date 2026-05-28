@echo off
REM DEPRECATED: Watchdog is now part of Morpheus Daemon.
REM Redirecting to unified daemon entry point.
echo [%DATE% %TIME%] run_watchdog_daemon.bat is deprecated - Watchdog now runs inside Morpheus.
echo [%DATE% %TIME%] Delegating to run_morpheus.bat...
call "%~dp0run_morpheus.bat"
