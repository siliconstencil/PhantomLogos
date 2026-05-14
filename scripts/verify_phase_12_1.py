import sys
from pathlib import Path


def get_project_root():
    return Path(__file__).parent.parent


def verify_skill(skill_name, min_lines):
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

    if len(lines) < min_lines:
        print(f"FAIL: {skill_name} has only {len(lines)} lines, expected {min_lines}")
        return False

    if missing:
        print(f"FAIL: {skill_name} missing headers: {missing}")
        return False

    print(f"PASS: {skill_name} verified.")
    return True


if __name__ == "__main__":
    skills_to_verify = [
        ("prompt-compression", 25),
        ("file-operations", 25),
        ("error-self-recovery", 25),
        ("logic-deadlock-resolver", 25),
        ("mcp-orchestration", 25),
        ("telemetry", 15),
        ("resource-scheduling", 15),
        ("system-vram-profiler", 15),
    ]

    results = [verify_skill(s, m) for s, m in skills_to_verify]

    if all(results):
        print("\nALL PHASE 12.1 SKILLS VERIFIED SUCCESSFULLY.")
        sys.exit(0)
    else:
        print("\nPHASE 12.1 VERIFICATION FAILED.")
        sys.exit(1)
