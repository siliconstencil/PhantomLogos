@echo off
setlocal enabledelayedexpansion
for /f "tokens=*" %%a in ('powershell -Command "(Get-Content 'D:\Hank\.env' | Where-Object { $_ -match '^GITHUB_PERSONAL_ACCESS_TOKEN=' } | ForEach-Object { $_.Substring($_.IndexOf('=')+1) })"') do set "GITHUB_TOKEN=%%a"
npx -y @modelcontextprotocol/server-github
