import json
import os
import re
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))

from cognition.mnemosyne.rational_store import MnemosyneRationalStore

EXTRA_RULES = [
    {
        "id": "THREE_STRIKE_RULE",
        "description": "If an error persists with >80% code similarity in changes, maximum 3 retries allowed. After 3rd failure, agent must stop and provide detailed post-mortem to L0.",
        "agent_id": "system",
        "severity": 5,
        "source": "AGENTS.md",
    },
    {
        "id": "WRITE_TO_FILE_FORBIDDEN",
        "description": "write_to_file is FORBIDDEN for modifying existing files. Creates new files only. Use replace_file_content or multi_replace_file_content for edits on existing files.",
        "agent_id": "system",
        "severity": 5,
        "source": "DEEPSEEK_CMD.md",
    },
    {
        "id": "ANTI_FLASH_PACING",
        "description": "Agents must pause and reflect after each step to prevent Flash-model throughput bias. Speed must never compromise the Meaning-Importance-Value equation.",
        "agent_id": "system",
        "severity": 3,
        "source": "AGENTS.md",
    },
    {
        "id": "WORKSPACE_HYGIENE",
        "description": "D: Workspace (Primary) for all project files, code, and temporary scratch scripts. C: drive strictly reserved for system-generated artifacts within .gemini/antigravity/brain path. All Python commands must use local .venv.",
        "agent_id": "system",
        "severity": 4,
        "source": "AGENTS.md",
    },
    {
        "id": "OUTPUT_GOVERNANCE",
        "description": "All long plans, research, and analysis must be stored in .md files (Artifact-First Mandate). Terminal must remain clean, used only for strategic summaries and L0 interaction.",
        "agent_id": "system",
        "severity": 4,
        "source": "AGENTS.md",
    },
    {
        "id": "DEFAULT_API_PARAMS",
        "description": "Default API parameters: model=deepseek-v4-pro, temperature=0.2, thinking enabled, reasoning_effort=high, max_tokens=4096.",
        "agent_id": "system",
        "severity": 3,
        "source": "DEEPSEEK_CMD.md",
    },
    {
        "id": "HERMES_BRIDGE_PROTOCOL",
        "description": "Hermes bridge commands map to Mnemosyne operations: init->POST session, load->Axis 6 hybrid search (RRF+Jina), save->semantic store persist, list->OperationalStore sessions, close->session closure.",
        "agent_id": "system",
        "severity": 3,
        "source": "DEEPSEEK_CMD.md",
    },
]

RULES_JSON_PATH = ".antigravity/rules.json"
MD_SOURCES = [
    "AGENTS.md",
    "DEEPSEEK_CMD.md",
    ".antigravity/CONSTITUTION.md",
    ".antigravity/IDENTITY.md",
    ".cursorrules",
]

SEVERITY_MAP = {"CRITICAL": 5, "HIGH": 4, "MEDIUM": 3, "LOW": 2, "INFO": 1}


def extract_md_rules(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    rules = []
    current_section = ""
    for line in content.splitlines():
        ls = line.strip()
        m = re.match(r"^##+\s+(.+)", ls)
        if m:
            current_section = m.group(1).strip()

        m = re.match(r"\*\*([A-Z][A-Z_0-9]+)\*\*:\s*(.+)", ls)
        if m and current_section:
            rid = m.group(1)
            desc = f"[{current_section}] {m.group(2).strip()[:200]}"
            rules.append((rid, desc, os.path.basename(filepath)))

    return rules


def sync(dry_run=False):
    store = None if dry_run else MnemosyneRationalStore()
    count = 0
    seen_ids = set()

    # 1. rules.json (primary structured source)
    if os.path.exists(RULES_JSON_PATH):
        with open(RULES_JSON_PATH, encoding="utf-8") as f:
            data = json.load(f)

        rules = data.get("governance_rules", [])
        print(f"[rules.json] {len(rules)} rules")
        for r in rules:
            rid = r["id"]
            desc = r["description"]
            sev = SEVERITY_MAP.get(r.get("severity", "MEDIUM"), 3)
            seen_ids.add(rid)
            if not dry_run and store:
                store.add_rule(rule_id=rid, description=desc, severity=sev)
            count += 1

        if not dry_run and store:
            store.add_fact(
                subject="Project Name",
                obj=data.get("project", "Phantom Logos"),
                source="rules.json",
            )
            store.add_fact(
                subject="System Identity", obj="Antigravity Sovereign OS", source="system"
            )
            store.add_fact(
                subject="Core Philosophy",
                obj="Cloud Brain + Local Brain + Local Muscle",
                source="GEMINI.md",
            )
    else:
        print("[rules.json] NOT FOUND")

    # 2. EXTRA_RULES (from AGENTS.md, DEEPSEEK_CMD.md, etc.)
    print(f"\n[EXTRA_RULES] {len(EXTRA_RULES)} extra rules (from AGENTS.md, DEEPSEEK_CMD.md)")
    for r in EXTRA_RULES:
        if r["id"] in seen_ids:
            continue
        seen_ids.add(r["id"])
        if not dry_run and store:
            store.add_rule(
                rule_id=r["id"],
                description=r["description"],
                agent_id=r["agent_id"],
                severity=r["severity"],
            )
        print("  {} (from {})".format(r["id"], r["source"]))
        count += 1

    # 3. Dynamic extraction from Markdown files (catches any new rules not hardcoded)
    print(f"\n[MD_EXTRACT] Scanning {len(MD_SOURCES)} files for additional rules...")
    for src in MD_SOURCES:
        extracted = extract_md_rules(src)
        for rid, desc, origin in extracted:
            if rid in seen_ids:
                continue
            seen_ids.add(rid)
            if not dry_run and store:
                store.add_rule(rule_id=rid[:50], description=desc[:200], severity=3)
            print(f"  {rid} (from {origin} - dynamic)")
            count += 1

    print(f"\nTotal: {count} rules synced ({len(seen_ids)} unique)")
    if dry_run:
        print("[DRY RUN - no changes made]")
    else:
        print("Success: Governance synchronization complete.")


if __name__ == "__main__":
    if "--dry-run" in sys.argv:
        sync(dry_run=True)
    else:
        sync()
