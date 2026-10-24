# check-careful.ps1 - PreToolUse hook: intercepts destructive Bash commands
# Reads JSON from stdin, returns permissionDecision JSON to stdout.
# Ported from gstack check-careful.sh for Windows PowerShell compatibility.

$rawInput = [Console]::In.ReadToEnd()
if (-not $rawInput.Trim()) { Write-Output '{}'; exit 0 }

try {
    $json = $rawInput | ConvertFrom-Json
} catch {
    Write-Output '{}'
    exit 0
}

$cmd = $json.tool_input.command
if (-not $cmd) { Write-Output '{}'; exit 0 }

# Safe rm targets - allow without warning
$SAFE_TARGETS = @('node_modules', '\.next', '\bdist\b', '__pycache__', '\.cache', '\bbuild\b', '\.turbo', '\bcoverage\b', '\.venv', '\.pytest_cache')

# If rm -r but only safe targets, allow
if ($cmd -match 'rm\s+(-[a-zA-Z]*r[a-zA-Z]*|--recursive)') {
    $allSafe = $true
    $tokens = $cmd -split '\s+' | Where-Object { $_ -notmatch '^-' -and $_ -ne 'rm' }
    foreach ($token in $tokens) {
        $isSafe = $false
        foreach ($safe in $SAFE_TARGETS) {
            if ($token -match $safe) { $isSafe = $true; break }
        }
        if (-not $isSafe -and $token) { $allSafe = $false; break }
    }
    if ($allSafe -and $tokens.Count -gt 0) { Write-Output '{}'; exit 0 }
}

# Destructive pattern checks
$checks = @(
    @{ P = 'rm\s+(-[a-zA-Z]*r[a-zA-Z]*|--recursive)';        M = 'Recursive delete (rm -r). Permanently removes files.';                           T = 'rm_recursive'      }
    @{ P = '(?i)drop\s+(table|database)';                      M = 'SQL DROP detected. Permanently deletes database objects.';                        T = 'drop_table'        }
    @{ P = '(?i)\btruncate\b';                                 M = 'SQL TRUNCATE. Deletes all rows from a table.';                                    T = 'truncate'          }
    @{ P = 'git\s+push\s+.*(-f\b|--force)';                   M = 'git force-push rewrites remote history. Other contributors may lose work.';       T = 'git_force_push'    }
    @{ P = 'git\s+reset\s+--hard';                             M = 'git reset --hard discards all uncommitted changes permanently.';                   T = 'git_reset_hard'    }
    @{ P = 'git\s+(checkout|restore)\s+\.';                    M = 'Discards all uncommitted changes in the working tree.';                           T = 'git_discard'       }
    @{ P = 'kubectl\s+delete';                                  M = 'kubectl delete removes Kubernetes resources. May impact production.';             T = 'kubectl_delete'    }
    @{ P = 'docker\s+(rm\s+-f|system\s+prune)';               M = 'Docker force-remove or prune. May delete running containers or images.';          T = 'docker_destructive'}
    @{ P = 'alembic\s+downgrade';                              M = 'Alembic downgrade rolls back DB migrations. [SRC:axis_1]';                        T = 'alembic_downgrade' }
    @{ P = 'Remove-Item\s+.*-Recurse.*-Force|rm\s+-rf\s+-Path'; M = 'PowerShell recursive force-delete. Permanently removes files.';                 T = 'ps_rm_rf'          }
)

foreach ($check in $checks) {
    if ($cmd -match $check.P) {
        $msg = $check.M -replace '"', '\"'
        Write-Output "{`"permissionDecision`":`"ask`",`"message`":`"[careful] $msg`"}"
        exit 0
    }
}

Write-Output '{}'
