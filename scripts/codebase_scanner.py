import ast
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from typing import Any

# Enforce absolute pathing
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Target directories to scan
TARGET_DIRS = ["src", "cognition", "scripts", "tests"]
REPORT_PATH = os.path.join(project_root, "logs", "codebase_scan_report.md")
JSON_REPORT_PATH = os.path.join(project_root, "logs", "codebase_scan_report.json")


class CodebaseScanner:
    """
    Pure Codebase Scanner & Static Auditor.
    Scans files recursively, runs Ruff/Pyright, and performs AST anti-pattern analysis.
    """

    def __init__(self) -> None:
        self.issues: list[dict[str, Any]] = []
        self.stats = {
            "total_files": 0,
            "total_lines": 0,
            "custom_violations": 0,
            "ruff_errors": 0,
            "pyright_errors": 0,
        }
        self.cloud_provider_regex = re.compile(r"\b(openai|anthropic|google\.generativeai)\b")
        # Basic high-entropy secret regex (API keys, tokens, credentials)
        self.secret_regex = re.compile(
            r"\b(api_key|client_secret|auth_token|password|private_key)\b\s*=\s*['\"][a-zA-Z0-9_\-\.]{12,}['\"]",
            re.IGNORECASE,
        )

    def scan(self) -> None:
        print("[*] Starting codebase scan...")
        self._scan_files()
        self._run_ruff()
        self._run_pyright()
        self._generate_report()
        print(f"[+] Scan complete. Report saved to: {REPORT_PATH}")

    def _scan_files(self) -> None:
        for directory in TARGET_DIRS:
            dir_path = os.path.join(project_root, directory)
            if not os.path.exists(dir_path):
                continue

            for root, _, files in os.walk(dir_path):
                for file in files:
                    if file.endswith(".py"):
                        filepath = os.path.join(root, file)
                        self.stats["total_files"] += 1
                        self._analyze_file(filepath)

    def _analyze_file(self, filepath: str) -> None:
        rel_path = os.path.relpath(filepath, project_root)
        try:
            with open(filepath, encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines = content.splitlines()
                self.stats["total_lines"] += len(lines)

            # 1. Custom Regex Check: Secrets Detection
            for line_idx, line in enumerate(lines, 1):
                if self.secret_regex.search(line):
                    self.issues.append(
                        {
                            "file": rel_path,
                            "line": line_idx,
                            "type": "SECRET",
                            "severity": "CRITICAL",
                            "message": "Potential hardcoded secret or API key detected.",
                            "snippet": line.strip(),
                        }
                    )
                    self.stats["custom_violations"] += 1

            # 2. AST Code Quality & Layer Rules Check
            tree = ast.parse(content, filename=filepath)
            for node in ast.walk(tree):
                # Check for direct cloud LLM library usage (bypassing middleware)
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    for name in node.names:
                        full_name = name.name
                        if self.cloud_provider_regex.search(full_name):
                            self.issues.append(
                                {
                                    "file": rel_path,
                                    "line": node.lineno,
                                    "type": "BYPASS_VIOLATION",
                                    "severity": "WARNING",
                                    "message": f"Direct cloud provider import '{full_name}' detected. Ensure calls route through Sovereign Middleware.",
                                    "snippet": f"import {full_name}"
                                    if isinstance(node, ast.Import)
                                    else f"from ... import {full_name}",
                                }
                            )
                            self.stats["custom_violations"] += 1

                # Check for empty except blocks (silent failures)
                if isinstance(node, ast.Try):
                    for handler in node.handlers:
                        if handler.type is None or (
                            isinstance(handler.type, ast.Name) and handler.type.id == "Exception"
                        ):
                            # Check if the block body is empty or just 'pass'
                            is_silent = False
                            if len(handler.body) == 1 and isinstance(handler.body[0], ast.Pass):
                                is_silent = True
                            elif (
                                len(handler.body) == 1
                                and isinstance(handler.body[0], ast.Expr)
                                and isinstance(handler.body[0].value, ast.Constant)
                                and isinstance(handler.body[0].value.value, str)
                            ):
                                is_silent = True  # just a docstring

                            if is_silent:
                                self.issues.append(
                                    {
                                        "file": rel_path,
                                        "line": handler.lineno,
                                        "type": "SILENT_FAIL",
                                        "severity": "LOW",
                                        "message": "Silent exception handler ('pass' on Exception) detected.",
                                        "snippet": "except Exception: pass",
                                    }
                                )
                                self.stats["custom_violations"] += 1

        except Exception as e:
            self.issues.append(
                {
                    "file": rel_path,
                    "line": 0,
                    "type": "SCAN_ERROR",
                    "severity": "HIGH",
                    "message": f"Failed to parse file: {e}",
                    "snippet": "",
                }
            )

    def _run_ruff(self) -> None:
        print("[*] Running Ruff linter...")
        try:
            venv_ruff = os.path.join(project_root, ".venv", "Scripts", "ruff.exe")
            ruff_executable = venv_ruff if os.path.exists(venv_ruff) else shutil.which("ruff")
            if not ruff_executable:
                print("[-] Ruff executable not found. Skipping Ruff scan.")
                return

            proc = subprocess.run(
                [ruff_executable, "check", "--format=json", "."],
                cwd=project_root,
                capture_output=True,
                check=False,
            )

            if proc.stdout:
                data = json.loads(proc.stdout.decode("utf-8"))
                for err in data:
                    self.issues.append(
                        {
                            "file": err.get("filename"),
                            "line": err.get("location", {}).get("row", 0),
                            "type": "LINT",
                            "severity": "MEDIUM",
                            "message": f"Ruff: {err.get('code')} - {err.get('message')}",
                            "snippet": err.get("noqa_row"),
                        }
                    )
                    self.stats["ruff_errors"] += 1
        except Exception as e:
            print(f"[-] Ruff scan execution failed: {e}")

    def _run_pyright(self) -> None:
        print("[*] Running Pyright type checker...")
        try:
            # Avoid shell=True by locating correct executable
            npx_executable = shutil.which("npx.cmd") if os.name == "nt" else shutil.which("npx")
            if not npx_executable:
                print("[-] npx executable not found. Skipping Pyright scan.")
                return

            proc = subprocess.run(
                [npx_executable, "pyright", "--outputjson"],
                cwd=project_root,
                capture_output=True,
                check=False,
            )

            stdout_str = proc.stdout.decode("utf-8")
            # Pyright JSON output sometimes starts after some npm notices, search for opening brace
            json_start = stdout_str.find("{")
            if json_start != -1:
                data = json.loads(stdout_str[json_start:])
                diagnostics = data.get("generalDiagnostics", [])
                for diag in diagnostics:
                    severity = diag.get("severity", "error")
                    self.issues.append(
                        {
                            "file": os.path.relpath(diag.get("file"), project_root),
                            "line": diag.get("range", {}).get("start", {}).get("line", 0) + 1,
                            "type": "TYPE",
                            "severity": severity.upper(),
                            "message": f"Pyright: {diag.get('message')}",
                            "snippet": "",
                        }
                    )
                    if severity == "error":
                        self.stats["pyright_errors"] += 1
        except Exception as e:
            print(f"[-] Pyright scan execution failed: {e}")

    def _generate_report(self) -> None:
        now_str = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p PT")

        # Sort issues: Critical -> High -> Medium -> Low, then by file and line
        severity_order = {
            "CRITICAL": 0,
            "ERROR": 1,
            "HIGH": 2,
            "WARNING": 3,
            "MEDIUM": 4,
            "LOW": 5,
            "INFORMATION": 6,
        }
        sorted_issues = sorted(
            self.issues, key=lambda x: (severity_order.get(x["severity"], 10), x["file"], x["line"])
        )

        # 1. Generate Markdown Report
        md = []
        md.append("# Codebase Scan & Gap Analysis Report")
        md.append(f"Generated at: `{now_str}`\n")

        md.append("## 1. Scan Statistics")
        md.append(f"- **Total Files Scanned**: {self.stats['total_files']}")
        md.append(f"- **Total Lines of Code**: {self.stats['total_lines']}")
        md.append(f"- **Custom Violations (AST/Secrets)**: {self.stats['custom_violations']}")
        md.append(f"- **Ruff Lint Errors**: {self.stats['ruff_errors']}")
        md.append(f"- **Pyright Type Errors**: {self.stats['pyright_errors']}")
        md.append("")

        md.append("## 2. Identified Issues & Code Gaps")
        if not sorted_issues:
            md.append("No issues found! Your codebase is 100% compliant.")
        else:
            md.append("| File | Line | Type | Severity | Message |")
            md.append("|---|---|---|---|---|")
            for issue in sorted_issues:
                msg = issue["message"].replace("|", "\\|")
                md.append(
                    f"| [{issue['file']}](file:///{project_root.replace('\\', '/')}/{issue['file'].replace('\\', '/')}#L{issue['line']}) | {issue['line']} | {issue['type']} | **{issue['severity']}** | {msg} |"
                )

        os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(md))

        # 2. Generate JSON Report
        json_data = {"timestamp": now_str, "stats": self.stats, "issues": sorted_issues}
        with open(JSON_REPORT_PATH, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2)


if __name__ == "__main__":
    scanner = CodebaseScanner()
    scanner.scan()
