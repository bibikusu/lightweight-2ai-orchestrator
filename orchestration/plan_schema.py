"""M01: minimal plan schema validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_BACKLOG_REF = "docs/backlogs/backlog-01.yaml"
ALLOWED_EXECUTION_MODE = "run_existing_sessions"
REQUIRED_KEYS = ("plan_id", "execution_mode", "session_source", "backlog_ref")


def _validate_required_keys(plan_data: dict[str, Any]) -> None:
    missing_keys = sorted(key for key in REQUIRED_KEYS if key not in plan_data)
    if missing_keys:
        raise ValueError(f"missing required keys: {', '.join(missing_keys)}")


def _validate_execution_mode(execution_mode: Any) -> None:
    if execution_mode == ALLOWED_EXECUTION_MODE:
        return
    if execution_mode in {"generate_sessions", "mixed"}:
        raise ValueError(
            "execution_mode must be run_existing_sessions before M04; "
            f"got {execution_mode}"
        )
    raise ValueError(f"unsupported execution_mode: {execution_mode}")


def _validate_session_source(session_source: Any) -> None:
    if not isinstance(session_source, dict):
        raise ValueError("session_source must be a mapping")

    if session_source.get("type") != "explicit_list":
        raise ValueError("session_source.type must be explicit_list")

    session_ids = session_source.get("session_ids")
    if not isinstance(session_ids, list) or any(not isinstance(x, str) for x in session_ids):
        raise ValueError("session_source.session_ids must be list[str]")


def _validate_backlog_ref(backlog_ref: Any) -> None:
    if backlog_ref != DEFAULT_BACKLOG_REF:
        raise ValueError(f"backlog_ref must be {DEFAULT_BACKLOG_REF}")

    backlog_path = ROOT_DIR / backlog_ref
    if not backlog_path.exists():
        raise FileNotFoundError(f"backlog file not found: {backlog_path}")


def validate_plan_schema(plan_data: dict[str, Any]) -> None:
    _validate_required_keys(plan_data)
    _validate_execution_mode(plan_data["execution_mode"])
    _validate_session_source(plan_data["session_source"])
    _validate_backlog_ref(plan_data["backlog_ref"])


def load_and_validate_plan(plan_path: Path) -> dict[str, Any]:
    if not plan_path.exists():
        raise FileNotFoundError(f"plan file not found: {plan_path}")

    with plan_path.open("r", encoding="utf-8") as f:
        plan_data = yaml.safe_load(f)

    if not isinstance(plan_data, dict):
        raise ValueError("plan file must contain a mapping at top level")

    validate_plan_schema(plan_data)
    return plan_data
