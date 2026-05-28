# check-freeze.ps1 - PreToolUse hook: blocks Edit/Write outside freeze boundary
# Reads JSON from stdin, returns permissionDecision JSON to stdout.
# Ported from gstack check-freeze.sh for Windows PowerShell compatibility.

$rawInput = [Console]::In.ReadToEnd()
if (-not $rawInput.Trim()) { Write-Output '{}'; exit 0 }

try {
    $json = $rawInput | ConvertFrom-Json
} catch {
    Write-Output '{}'
    exit 0
}

# Get file path from tool input
$filePath = $json.tool_input.file_path
if (-not $filePath) { Write-Output '{}'; exit 0 }

# Check freeze state file
$freezeFile = "D:\Hank\.claude\freeze-dir.txt"
if (-not (Test-Path $freezeFile)) { Write-Output '{}'; exit 0 }

$freezeDir = (Get-Content $freezeFile -Raw -ErrorAction SilentlyContinue).Trim()
if (-not $freezeDir) { Write-Output '{}'; exit 0 }

# Resolve to absolute paths
if (-not [System.IO.Path]::IsPathRooted($filePath)) {
    $filePath = Join-Path (Get-Location).Path $filePath
}
$filePath  = [System.IO.Path]::GetFullPath($filePath)
$freezeDir = [System.IO.Path]::GetFullPath($freezeDir)

# Ensure freeze dir ends without trailing separator for clean prefix check
$freezeDir = $freezeDir.TrimEnd('\', '/')

# Allow if inside boundary
if ($filePath.StartsWith($freezeDir + '\', [System.StringComparison]::OrdinalIgnoreCase) -or
    $filePath.Equals($freezeDir, [System.StringComparison]::OrdinalIgnoreCase)) {
    Write-Output '{}'
} else {
    $msg = "[freeze] Blocked: $filePath is outside the freeze boundary ($freezeDir). Only edits within the frozen directory are allowed." -replace '"', '\"'
    Write-Output "{`"permissionDecision`":`"deny`",`"message`":`"$msg`"}"
}
