"""M01: plan loader + validation only."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from orchestration.plan_schema import load_and_validate_plan

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_PLAN_ID = "plan-01"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan-id", default=DEFAULT_PLAN_ID, help="e.g. plan-01")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="構造検証のみを実行し、session 実行は開始しない",
    )
    return parser.parse_args()


def resolve_plan_path(plan_id: str) -> Path:
    return ROOT_DIR / "docs" / "plans" / f"{plan_id}.yaml"


def main() -> int:
    args = parse_args()
    plan_path = resolve_plan_path(args.plan_id)

    try:
        load_and_validate_plan(plan_path)
    except Exception as exc:  # pragma: no cover
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"[OK] dry-run validation passed: {plan_path}")
        return 0

    # M01 では実行導線を持たない（検証のみ）
    print(f"[OK] plan validation passed: {plan_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
