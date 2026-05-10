Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "D:\Hank\run_watchdog_daemon.bat" & chr(34), 0
Set WshShell = Nothing
