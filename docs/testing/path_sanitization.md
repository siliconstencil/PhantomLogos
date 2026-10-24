# Path Sanitization and Security Audit Test Plan

This document was prepared to verify that hardcoded paths have been removed from the codebase, and to verify the platform-agnostic path validation mechanisms and the SQL injection / path traversal protections. [2:45 PM PT]

## 1. Test Scenarios

### Scenario A: Hardcoded Path Audit
- **Steps:**
  1. In the project root directory, run the following PowerShell command to check whether any hardcoded absolute paths remain:
     `Get-ChildItem -Path src/, scripts/ -Recurse -Include *.py | Select-String -Pattern "<your-old-absolute-path>"`
- **Expected Result:** The command must return zero (0) results.

### Scenario B: Path Traversal Protection
- **Steps:**
  1. Try to access a path outside the project root directory (for example `../../Windows/` or `/etc/`) through `ls` or file reading tools.
- **Expected Result:** The system must block access with `os.path.commonpath` or similar protections and raise an "Unsafe path detected" or "Access denied" error.
