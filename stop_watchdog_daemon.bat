@echo off
REM DEPRECATED: Watchdog is now part of Morpheus Daemon.
REM Use scripts\stop_morpheus.bat instead.
echo [%DATE% %TIME%] stop_watchdog_daemon.bat is deprecated.
echo [%DATE% %TIME%] Use scripts\stop_morpheus.bat to stop the unified daemon.
echo [%DATE% %TIME%] Attempting legacy cleanup of any orphaned watchdog processes...
taskkill /F /IM pythonw.exe /FI "CMDLINE eq *file_watchdog*" 2>nul
echo Done.
