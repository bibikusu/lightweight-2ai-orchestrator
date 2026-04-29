from __future__ import annotations

import json
from glob import glob
from pathlib import Path
from typing import Any

import yaml


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


def load_session_definitions(pattern: str | Path) -> list[dict[str, Any]]:
    sessions: list[dict[str, Any]] = []
    for file_name in sorted(glob(str(pattern))):
        try:
            data = json.loads(Path(file_name).read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            sessions.append(data)
    return sessions
