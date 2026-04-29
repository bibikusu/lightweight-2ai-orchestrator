from __future__ import annotations

import json
from glob import glob
from pathlib import Path
from typing import Any

import yaml


JSON_PARSE_ERROR = "json_parse_error"


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def load_queue_policy(path: str | Path) -> dict[str, Any]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("queue_policy.yaml root must be a mapping")
    return data


def load_project_registry(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("project_registry.json root must be a mapping")
    return data


def load_session_definitions_with_skipped(
    pattern: str | Path,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    sessions: list[dict[str, Any]] = []
    skipped_sessions: list[dict[str, str]] = []
    for file_name in sorted(glob(str(pattern))):
        path = Path(file_name)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            skipped_sessions.append(
                {
                    "path": _display_path(path),
                    "reason": JSON_PARSE_ERROR,
                }
            )
        else:
            if isinstance(data, dict):
                sessions.append(data)
    return sessions, skipped_sessions


def load_session_definitions(pattern: str | Path) -> list[dict[str, Any]]:
    sessions, _skipped_sessions = load_session_definitions_with_skipped(pattern)
    return sessions
