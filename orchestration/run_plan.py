"""M02: plan loader + sequential executor (minimal)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from orchestration.plan_schema import load_and_validate_plan

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_PLAN_ID = "plan-01"
DEFAULT_STOP_POLICY = "stop_on_fail"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan-id", default=DEFAULT_PLAN_ID, help="e.g. plan-01")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="構造検証のみを実行し、session 実行は開始しない",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="M02 sequential executor を有効化して session を順次実行する",
    )
    return parser.parse_args()


def resolve_plan_path(plan_id: str) -> Path:
    return ROOT_DIR / "docs" / "plans" / f"{plan_id}.yaml"


def resolve_session_report_path(session_id: str) -> Path:
    return ROOT_DIR / "artifacts" / session_id / "report.json"


def load_session_report_minimum(session_id: str) -> dict[str, Any]:
    report_path = resolve_session_report_path(session_id)
    if not report_path.exists():
        return {
            "status": "failed",
            "changed_files": [],
            "checks": {"success": False, "reason": "report_not_found"},
        }

    with report_path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    status = str(raw.get("status", "unknown"))
    changed_files = raw.get("changed_files")
    checks = raw.get("checks")
    if not isinstance(changed_files, list):
        changed_files = []
    if not isinstance(checks, dict):
        checks = {}
    return {
        "status": status,
        "changed_files": changed_files,
        "checks": checks,
    }


def invoke_session_executor(session_id: str) -> int:
    command = [
        sys.executable,
        str(ROOT_DIR / "orchestration" / "run_session.py"),
        "--session-id",
        session_id,
    ]
    completed = subprocess.run(command, cwd=ROOT_DIR, check=False)
    return int(completed.returncode)


def build_aggregate_report(
    *,
    plan_id: str,
    stop_policy: str,
    session_results: list[dict[str, Any]],
    total_sessions: int,
    stopped_on: str | None,
) -> dict[str, Any]:
    succeeded = sum(1 for item in session_results if item.get("status") == "success")
    failed = sum(1 for item in session_results if item.get("status") != "success")
    return {
        "plan_id": plan_id,
        "stop_policy": stop_policy,
        "total_sessions": total_sessions,
        "executed_sessions": len(session_results),
        "succeeded_sessions": succeeded,
        "failed_sessions": failed,
        "stopped": stopped_on is not None,
        "stopped_on": stopped_on,
        "sessions": session_results,
    }


def write_aggregate_report(plan_id: str, report: dict[str, Any]) -> Path:
    out_dir = ROOT_DIR / "artifacts" / "plans" / plan_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "aggregate_report.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def execute_sessions(plan_data: dict[str, Any], plan_id: str) -> tuple[int, Path]:
    session_source = plan_data.get("session_source", {})
    if session_source.get("type") != "explicit_list":
        raise ValueError("M02 supports only session_source.type=explicit_list")

    session_ids = session_source.get("session_ids", [])
    if not isinstance(session_ids, list) or any(not isinstance(sid, str) for sid in session_ids):
        raise ValueError("session_source.session_ids must be list[str]")

    stop_policy = str(plan_data.get("stop_policy", DEFAULT_STOP_POLICY))
    if stop_policy != DEFAULT_STOP_POLICY:
        raise ValueError(
            f"unsupported stop_policy in M02: {stop_policy} (supported: {DEFAULT_STOP_POLICY})"
        )

    results: list[dict[str, Any]] = []
    stopped_on: str | None = None
    any_failure = False

    for session_id in session_ids:
        return_code = invoke_session_executor(session_id)
        report = load_session_report_minimum(session_id)
        report_status = str(report.get("status", "")).strip()
        if report_status in {"success", "failed"}:
            status = report_status
        else:
            status = "success" if return_code == 0 else "failed"
        if status != "success":
            any_failure = True
        results.append(
            {
                "session_id": session_id,
                "status": status,
                "changed_files": report.get("changed_files", []),
                "checks": report.get("checks", {}),
                "return_code": return_code,
            }
        )
        if status != "success":
            stopped_on = session_id
            break

    aggregate = build_aggregate_report(
        plan_id=plan_id,
        stop_policy=stop_policy,
        session_results=results,
        total_sessions=len(session_ids),
        stopped_on=stopped_on,
    )
    path = write_aggregate_report(plan_id, aggregate)
    return (1 if any_failure else 0), path


def main() -> int:
    args = parse_args()
    plan_path = resolve_plan_path(args.plan_id)

    try:
        plan_data = load_and_validate_plan(plan_path)
    except Exception as exc:  # pragma: no cover
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"[OK] dry-run validation passed: {plan_path}")
        return 0

    if not args.execute:
        print(f"[OK] validation passed (execution skipped): {plan_path}")
        return 0

    try:
        rc, aggregate_path = execute_sessions(plan_data, args.plan_id)
    except Exception as exc:  # pragma: no cover
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    print(f"[OK] aggregate report generated: {aggregate_path}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
