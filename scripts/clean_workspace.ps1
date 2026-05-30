# Comprehensive Workspace Cleanup
# Removes: __pycache__, .pytest_cache, .mypy_cache, .ruff_cache, dist, build
# SAFE: Excludes .venv, node_modules, .git, data, logs, .antigravity

$Root = (Get-Item $PSScriptRoot).Parent.FullName

Write-Host "Starting Safe Workspace Cleanup in $Root..." -ForegroundColor Cyan

$exclude = @(
    [regex]::Escape("$Root\.venv"),
    [regex]::Escape("$Root\node_modules"),
    [regex]::Escape("$Root\.git"),
    [regex]::Escape("$Root\data"),
    [regex]::Escape("$Root\logs"),
    [regex]::Escape("$Root\.antigravity"),
    [regex]::Escape("$Root\opencode")
)

$targets = @("__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "dist", "build")

function Test-Excluded {
    param([string]$Path)
    foreach ($pattern in $exclude) {
        if ($Path -match $pattern) {
            return $true
        }
    }
    return $false
}

$removed = 0

foreach ($target in $targets) {
    Write-Host "Searching for: $target" -ForegroundColor Gray
    $items = Get-ChildItem -Path $Root -Directory -Recurse -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -eq $target -or $_.Name -like $target }

    if ($items) {
        foreach ($item in $items) {
            if (Test-Path $item.FullName) {
                if (Test-Excluded $item.FullName) {
                    Write-Host "SKIPPED (protected): $($item.FullName)" -ForegroundColor DarkGray
                    continue
                }
                Write-Host "Removing: $($item.FullName)" -ForegroundColor Yellow
                Remove-Item -Path $item.FullName -Recurse -Force -ErrorAction SilentlyContinue
                if ($?) { $removed++ }
            }
        }
    }
}

Write-Host "Cleanup complete. $removed item(s) removed safely." -ForegroundColor Green
