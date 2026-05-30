@echo off
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "ENV_FILE=%SCRIPT_DIR%..\.env"
for /f "tokens=*" %%a in ('powershell -Command "(Get-Content '%ENV_FILE%' | Where-Object { $_ -match '^GITHUB_PERSONAL_ACCESS_TOKEN=' } | ForEach-Object { $_.Substring($_.IndexOf('=')+1) })"') do set "GITHUB_TOKEN=%%a"
npx -y @modelcontextprotocol/server-github
