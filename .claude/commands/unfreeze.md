# /unfreeze - Remove Directory Edit Restrictions

Remove the active freeze boundary. All directories become editable again.

```powershell
Remove-Item "D:\Hank\.claude\freeze-dir.txt" -ErrorAction SilentlyContinue
Write-Output "Freeze removed."
```

Confirm to the user: "Freeze boundary removed. All directories are now editable."
