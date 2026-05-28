"""
SLM Metadata Migration Script (AUDIT-01)
Converts old m:json tag format to new meta:key:value format.
v1.1.21+ _normalize_result() still reads both formats, but migration enables
cleaner tag-based querying at the SLM server level.
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.architrave.mcp import get_slm_client
from src.architrave.mcp.slm_client import _deserialize_meta
from src.utils.logging_config import setup_logger

logger = setup_logger("migrate_slm_metadata")

SEED_QUERIES = [
    "memory",
    "error",
    "rule",
    "fact",
    "event",
    "observation",
    "system",
    "agent",
    "context",
    "reflection",
    "insight",
    "learning",
]

PROJECTS = ["default", "semantic_memory", "failure_memory"]


def _has_old_format(tags: list[str]) -> bool:
    return any(t.startswith("m:") for t in tags)


def _convert_tags(tags: list[str]) -> list[str]:
    new_tags = []
    for tag in tags:
        if tag.startswith("m:"):
            try:
                meta = _deserialize_meta(tag[2:])
                if isinstance(meta, dict):
                    for key, value in meta.items():
                        if key in ("session_id", "agent_id", "axis_id", "timestamp"):
                            continue
                        if value is None:
                            continue
                        if isinstance(value, str):
                            new_tags.append(f"meta:{key}:{value}")
                        elif isinstance(value, bool):
                            new_tags.append(f"meta:{key}:{'true' if value else 'false'}")
                        elif isinstance(value, (int, float)):
                            new_tags.append(f"meta:{key}:{value}")
            except Exception:
                new_tags.append(tag)
        else:
            new_tags.append(tag)
    return new_tags


def migrate_project(slm, project: str, dry_run: bool = True) -> dict:
    migrated = 0
    skipped = 0
    failed = 0

    for query in SEED_QUERIES:
        try:
            results = slm.search(query=query, limit=20, table_name=project)
            for r in results:
                tags = getattr(r, "tags", r.get("tags", r.get("_tags", [])))
                if not isinstance(tags, list):
                    continue
                if not _has_old_format(tags):
                    skipped += 1
                    continue

                new_tags = _convert_tags(tags)

                if dry_run:
                    logger.info(f"[DRY-RUN] Would migrate entry: {str(r.get('text', ''))[:60]}...")
                    migrated += 1
                    continue

                content = r.get("text") or r.get("content") or ""
                entry = {
                    "text": content,
                    "tags": new_tags,
                    "importance": float(r.get("importance", 0.5)),
                    "session_id": r.get("session_id", "default"),
                    "project": project,
                }

                slm.remember(entry, table_name=project)
                migrated += 1

            time.sleep(0.1)
        except Exception as e:
            logger.warning(f"Migration failed for query '{query}' in '{project}': {e}")
            failed += 1

    return {"migrated": migrated, "skipped": skipped, "failed": failed}


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Migrate SLM tags from m:json to meta:key:value")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Preview without writing (default: True)",
    )
    parser.add_argument(
        "--execute", action="store_true", help="Actually perform migration (overrides --dry-run)"
    )
    args = parser.parse_args()

    dry_run = not args.execute

    logger.info("=== SLM Metadata Migration (AUDIT-01) ===")
    logger.info(f"Mode: {'DRY-RUN' if dry_run else 'EXECUTE'}")

    slm = get_slm_client()
    if not slm.health():
        logger.error("SLM server is not healthy. Aborting.")
        sys.exit(1)

    totals = {"migrated": 0, "skipped": 0, "failed": 0}

    for project in PROJECTS:
        logger.info(f"Scanning project '{project}'...")
        stats = migrate_project(slm, project, dry_run=dry_run)
        for k in totals:
            totals[k] += stats[k]
        logger.info(f"  -> {stats}")

    logger.info("=== Migration Summary ===")
    logger.info(f"  Migrated: {totals['migrated']}")
    logger.info(f"  Skipped:  {totals['skipped']}")
    logger.info(f"  Failed:   {totals['failed']}")

    if dry_run and totals["migrated"] > 0:
        logger.info(f"\nRun with --execute to perform {totals['migrated']} migrations.")


if __name__ == "__main__":
    main()
