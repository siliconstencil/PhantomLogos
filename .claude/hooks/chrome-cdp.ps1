# chrome-cdp.ps1 — Launch headless Chromium via CDP for gstack browse (Windows)
# Usage: & 'D:\Hank\.claude\hooks\chrome-cdp.ps1' [--port PORT]
# Outputs the CDP port number on stdout when ready.

param(
    [int]$Port = 0
)

$ErrorActionPreference = 'Stop'

# Resolve port: env var > param > default 9222
if ($Port -eq 0) {
    $Port = if ($env:GSTACK_PORT) { [int]$env:GSTACK_PORT } else { 9222 }
}

# Check if CDP is already listening on this port
$existing = netstat -ano 2>$null | Select-String ":$Port\s"
if ($existing) {
    Write-Output $Port
    exit 0
}

# Locate newest playwright-managed chromium
$playwrightRoot = "$env:USERPROFILE\AppData\Local\ms-playwright"
$chromePath = Get-ChildItem "$playwrightRoot\chromium-*\chrome-win64\chrome.exe" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1 -ExpandProperty FullName

if (-not $chromePath) {
    # Fallback: chromium-*/chrome-win/chrome.exe (older playwright layout)
    $chromePath = Get-ChildItem "$playwrightRoot\chromium-*\chrome-win\chrome.exe" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1 -ExpandProperty FullName
}

if (-not $chromePath) {
    Write-Error "Chromium not found. Run: npx playwright install chromium"
    exit 1
}

$userDataDir = "$env:TEMP\gstack-cdp-profile"
New-Item -ItemType Directory -Force -Path $userDataDir | Out-Null

$chromeArgs = @(
    "--remote-debugging-port=$Port",
    "--headless=new",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-extensions",
    "--disable-background-networking",
    "--user-data-dir=$userDataDir"
)

Start-Process -FilePath $chromePath -ArgumentList $chromeArgs -WindowStyle Hidden

# Wait up to 5 seconds for CDP port to open
$deadline = (Get-Date).AddSeconds(5)
while ((Get-Date) -lt $deadline) {
    $check = netstat -ano 2>$null | Select-String ":$Port\s"
    if ($check) {
        Write-Output $Port
        exit 0
    }
    Start-Sleep -Milliseconds 200
}

Write-Error "Chromium CDP did not open on port $Port within 5 seconds."
exit 1
