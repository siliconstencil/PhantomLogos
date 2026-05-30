import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))

from cognition.sophia.hephaestus import get_mapper
from src.utils.project_path import to_absolute_path


def update_mapper(output_path: str | None = None):
    output_path = output_path or to_absolute_path("logs/mapper_report.json")

    print("[MAPPER] Initializing CodebaseMapper (Axis 5)...")
    mapper = get_mapper()

    print("[MAPPER] Starting deep scan of codebase...")
    success = mapper.map_codebase(deep=True)

    if not success:
        print("[ERROR] Mapper failed to initialize or scan.")
        return

    print("[MAPPER] Generating comprehensive JSON report...")
    report = mapper.generate_report()

    summary = report["summary"]
    print(f"[MAPPER] Modules: {summary['total_modules']}")
    print(f"[MAPPER] Total lines: {summary['total_lines']}")
    print(f"[MAPPER] Dependencies: {summary['total_dependencies']}")
    print(f"[MAPPER] Circular deps: {summary['circular_dependencies']}")
    print(f"[MAPPER] ORM models: {summary['orm_models']}")
    print(f"[MAPPER] Dead code modules: {summary['dead_code_modules']}")
    print(f"[MAPPER] Layer violations: {summary['layer_violations']}")

    report_path = mapper.write_report(output_path)
    print(f"[MAPPER] Full report written to: {report_path}")

    circular = report.get("circular_dependencies", [])
    if circular:
        print(f"\n[ALERT] {len(circular)} circular dependency chains:")
        for entry in circular[:5]:
            print(f"  -> {' -> '.join(entry['cycle'])}")

    violations = report.get("layer_violations", [])
    if violations:
        print(f"\n[LAYER] {len(violations)} layer violations:")
        for v in violations[:10]:
            print(f"  {v['source']} -> {v['target']}  ({v['violation']})")

    dead = report.get("dead_code", [])
    if dead:
        print(f"\n[DEAD] {len(dead)} potentially dead modules:")
        for d in dead[:10]:
            print(f"  {d['module']}  ({d['line_count']} lines)")

    print("\n[MAPPER] Done.")


if __name__ == "__main__":
    update_mapper()
