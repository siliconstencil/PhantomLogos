@echo off
REM Stop the Morpheus daemon (Kill pythonw.exe running bootstrap)
taskkill /F /FI "IMAGENAME eq pythonw.exe" /FI "CMDLINE eq *bootstrap*" 2>nul
taskkill /F /FI "IMAGENAME eq python.exe" /FI "CMDLINE eq *bootstrap*" 2>nul
echo Morpheus daemon stopped.
