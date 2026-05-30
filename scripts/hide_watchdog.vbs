Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
projectRoot = fso.GetParentFolderName(scriptDir)
WshShell.Run chr(34) & projectRoot & "\run_watchdog_daemon.bat" & chr(34), 0
Set WshShell = Nothing
Set fso = Nothing
