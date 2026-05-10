Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "<project-root>\run_morpheus.bat" & chr(34), 0
Set WshShell = Nothing
