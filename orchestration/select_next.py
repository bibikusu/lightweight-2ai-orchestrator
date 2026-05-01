from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from orchestration.selector.core import build_selector_output
from orchestration.selector.loader import (
    load_project_registry,
    load_queue_policy,
    load_session_definitions_with_skipped,
)
from orchestration.selector.writer import utc_timestamp

_DEFAULT_SESSIONS_DIR = "docs/sessions"
_DEFAULT_REGISTRY = "docs/config/project_registry.json"
_DEFAULT_POLICY = "docs/config/queue_policy.yaml"


def _scan_status_fields(sessions: list[dict[str, Any]]) -> dict[str, int]:
    has_status = sum(1 for s in sessions if "status" in s)
    pending = sum(1 for s in sessions if s.get("status") == "pending")
    return {
        "total_sessions": len(sessions),
        "has_status": has_status,
        "no_status": len(sessions) - has_status,
        "pending_count": pending,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="select_next",
        description="selector CLI dry-run (session-156b)",
    )
    parser.add_argument("--dry-run", action="store_true", help="dry-run mode (required)")
    parser.add_argument(
        "--sessions-dir",
        default=_DEFAULT_SESSIONS_DIR,
        help=f"session definitions directory (default: {_DEFAULT_SESSIONS_DIR})",
    )
    parser.add_argument(
        "--registry",
        default=_DEFAULT_REGISTRY,
        help=f"project registry JSON path (default: {_DEFAULT_REGISTRY})",
    )
    parser.add_argument(
        "--policy",
        default=_DEFAULT_POLICY,
        help=f"queue policy YAML path (default: {_DEFAULT_POLICY})",
    )

    args = parser.parse_args(argv)

    if not args.dry_run:
        print(
            "--dry-run is required in current scope (session-156b)",
            file=sys.stderr,
        )
        return 2

    sessions_pattern = str(Path(args.sessions_dir) / "*.json")
    sessions, skipped_sessions = load_session_definitions_with_skipped(sessions_pattern)
    project_registry = load_project_registry(args.registry)
    queue_policy = load_queue_policy(args.policy)

    timestamp = utc_timestamp()
    output = build_selector_output(
        queue_policy=queue_policy,
        project_registry=project_registry,
        session_definitions=sessions,
        timestamp=timestamp,
        policy_source=args.policy,
        registry_source=args.registry,
        skipped_sessions=skipped_sessions,
    )

    output["metadata"]["status_field_scan"] = _scan_status_fields(sessions)

    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
