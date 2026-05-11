"""Build compact context pack for orchestrated handoff."""

import pathlib

from orchestration.context_pack.loader import (
    list_report_paths,
    load_acceptance_yaml,
    load_session_json,
)

_SCHEMA_VERSION = "compact_context_pack.v1"

_SESSION_SUMMARY_KEYS = [
    "session_id",
    "phase_id",
    "title",
    "goal",
    "scope",
    "out_of_scope",
    "constraints",
    "allowed_changes_detail",
    "forbidden_changes",
    "review_points",
    "failure_type",
]


def build_compact_context_pack(session_id: str, repo_root: pathlib.Path) -> dict:
    session_json_path = repo_root / "docs" / "sessions" / f"{session_id}.json"
    acceptance_yaml_path = repo_root / "docs" / "acceptance" / f"{session_id}.yaml"

    session_data = load_session_json(session_json_path)
    acceptance_data = load_acceptance_yaml(acceptance_yaml_path)

    session_summary = {k: session_data[k] for k in _SESSION_SUMMARY_KEYS if k in session_data}

    ac_items = acceptance_data.get("acceptance", [])
    acceptance_summary = {
        "acceptance_count": len(ac_items),
        "items": [
            {"id": a.get("id"), "description": a.get("description"), "test_name": a.get("test_name")}
            for a in ac_items
        ],
    }

    cc_items = session_data.get("completion_criteria", [])
    completion_summary = {
        "completion_count": len(cc_items),
        "items": [
            {"id": c.get("id"), "type": c.get("type"), "condition": c.get("condition")}
            for c in cc_items
        ],
    }

    report_paths = list_report_paths(session_id, repo_root)
    reports_found = len(report_paths) > 0
    reports_summary = {
        "found": reports_found,
        "items": [str(p.relative_to(repo_root)) for p in report_paths],
    }

    warnings: list = []
    if not reports_found:
        warnings.append(f"reports missing for {session_id}")

    inputs = {
        "session_json_path": str(session_json_path.relative_to(repo_root)),
        "acceptance_yaml_path": str(acceptance_yaml_path.relative_to(repo_root)),
        "report_paths": [str(p.relative_to(repo_root)) for p in report_paths],
    }

    handoff_ready = session_json_path.is_file() and acceptance_yaml_path.is_file()

    return {
        "schema_version": _SCHEMA_VERSION,
        "source_session_id": session_id,
        "session_summary": session_summary,
        "acceptance_summary": acceptance_summary,
        "completion_summary": completion_summary,
        "reports_summary": reports_summary,
        "inputs": inputs,
        "handoff_ready": handoff_ready,
        "warnings": warnings,
    }
