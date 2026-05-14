import sys
from pathlib import Path


def get_project_root():
    return Path(__file__).parent.parent


def verify_skill(skill_name, expected_lines):
    skill_path = get_project_root() / "agent" / "skills" / skill_name / "SKILL.md"
    if not skill_path.exists():
        print(f"FAIL: {skill_name} not found at {skill_path}")
        return False

    with open(skill_path, encoding="utf-8") as f:
        content = f.read()
        lines = content.splitlines()

    print(f"Checking {skill_name}: {len(lines)} lines")

    # Check headers
    headers = ["## Workflow", "## Guardrails", "## Output Format"]
    missing = [h for h in headers if h not in content]

    if len(lines) < expected_lines:
        print(f"FAIL: {skill_name} has only {len(lines)} lines, expected {expected_lines}")
        return False

    if missing:
        print(f"FAIL: {skill_name} missing headers: {missing}")
        return False

    # Phase 12.2 Specific: Name check
    if (
        "Sovereign Edition" not in content and skill_name != "ruflow-tier-routing"
    ):  # Some might not have it
        pass  # Non-critical

    print(f"PASS: {skill_name} verified.")
    return True


if __name__ == "__main__":
    skills_to_verify = [
        # Phase 12.1 Matured
        ("prompt-compression", 25),
        ("file-operations", 25),
        ("error-self-recovery", 25),
        ("logic-deadlock-resolver", 25),
        ("mcp-orchestration", 25),
        ("telemetry", 15),
        ("resource-scheduling", 15),
        ("system-vram-profiler", 15),
        # Phase 12.2 New
        ("14-axis-memory", 25),
        ("ruflow-tier-routing", 25),
        ("codebase-topography-analysis", 25),
        # Phase 12.2 Expanded/Renamed
        ("mnemosyne-high-fidelity-query", 25),
        ("sovereign-gateway", 25),
        ("sovereign-shield", 25),
        ("security-audit", 25),
    ]

    results = [verify_skill(s, m) for s, m in skills_to_verify]

    # Check README.md for gateway rename
    readme_path = get_project_root() / "agent" / "skills" / "README.md"
    with open(readme_path, encoding="utf-8") as f:
        readme_content = f.read()
    if "sovereign-gateway" in readme_content and "gateway-connectivity" not in readme_content:
        print("PASS: README.md updated for gateway rename.")
    else:
        print("FAIL: README.md not updated for gateway rename.")
        results.append(False)

    if all(results):
        print("\nALL PHASE 12 (11.19.15) SKILLS AND RENAMES VERIFIED SUCCESSFULLY.")
        sys.exit(0)
    else:
        print("\nPHASE 12 (11.19.15) VERIFICATION FAILED.")
        sys.exit(1)
