# Comprehensive Workspace Cleanup for D:\Hank
# Removes: __pycache__, .pytest_cache, .mypy_cache, .ruff_cache, dist, build
# SAFE: Excludes .venv, node_modules, .git, data, logs, .antigravity

Write-Host "Starting Safe Workspace Cleanup in D:\Hank..." -ForegroundColor Cyan

$exclude = @(
    [regex]::Escape("D:\Hank\.venv"),
    [regex]::Escape("D:\Hank\node_modules"),
    [regex]::Escape("D:\Hank\.git"),
    [regex]::Escape("D:\Hank\data"),
    [regex]::Escape("D:\Hank\logs"),
    [regex]::Escape("D:\Hank\.antigravity")
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
    $items = Get-ChildItem -Path "D:\Hank" -Directory -Recurse -Force -ErrorAction SilentlyContinue |
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
