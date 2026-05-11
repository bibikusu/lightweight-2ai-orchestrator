"""Read-only loaders for session JSON, acceptance YAML, and report paths."""

import json
import pathlib

import yaml


def load_session_json(path: pathlib.Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_acceptance_yaml(path: pathlib.Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def list_report_paths(session_id: str, repo_root: pathlib.Path) -> list:
    reports_dir = repo_root / "artifacts" / session_id / "reports"
    if not reports_dir.is_dir():
        return []
    return sorted(reports_dir.iterdir())
