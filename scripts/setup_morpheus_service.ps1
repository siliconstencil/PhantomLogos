# Antigravity Morpheus Daemon Setup Script
# This script creates a Windows Scheduled Task to run the VRAM daemon at logon.

$ProjectRoot = "D:\Hank"
$PythonPath = "python" # Assumes python is in PATH
$ScriptPath = "$ProjectRoot\src\clotho\bootstrap.py"
$TaskName = "AntigravityMorpheusDaemon"
$Arguments = "$ScriptPath --daemon"

Write-Host "--- Antigravity: Morpheus Daemon Windows Startup Setup ---" -ForegroundColor Cyan

# 1. Create the Scheduled Task
# Run at logon, hidden window, with highest privileges if possible
$Action = New-ScheduledTaskAction -Execute $PythonPath -Argument $Arguments -WorkingDirectory $ProjectRoot
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Phantom Logos VRAM Management Daemon" -Force

Write-Host "Success: Scheduled Task '$TaskName' created." -ForegroundColor Green
Write-Host "The daemon will now start automatically every time you log in." -ForegroundColor Yellow
Write-Host "To start it manually now, run: Start-ScheduledTask -TaskName $TaskName" -ForegroundColor Cyan
