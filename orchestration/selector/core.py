from __future__ import annotations

from typing import Any

SELECTOR_VERSION = "0.1.0"


def _session_id(session: dict[str, Any]) -> str:
    value = session.get("session_id")
    if value is None:
        raise ValueError("session definition missing session_id")
    return str(value)


def _candidate_sessions(session_definitions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        session
        for session in session_definitions
        if session.get("session_id") not in (None, "")
    ]


def _registry_projects(project_registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    projects = project_registry.get("projects", [])
    if not isinstance(projects, list):
        return {}
    indexed: dict[str, dict[str, Any]] = {}
    for project in projects:
        if isinstance(project, dict) and project.get("project_id") is not None:
            indexed[str(project["project_id"])] = project
    return indexed


def _priority_rank_value(
    session: dict[str, Any],
    queue_policy: dict[str, Any],
    project_registry: dict[str, Any],
) -> int:
    explicit_value = session.get("priority_rank_value")
    if explicit_value is not None:
        return int(explicit_value)

    project_id = session.get("project_id")
    projects = _registry_projects(project_registry)
    project = projects.get(str(project_id)) if project_id is not None else None
    deploy_risk = project.get("deploy_risk") if project is not None else None

    risk_to_priority = (
        queue_policy.get("project_priority", {}).get("risk_to_priority", {})
        if isinstance(queue_policy.get("project_priority"), dict)
        else {}
    )
    priority_name = risk_to_priority.get(deploy_risk, session.get("priority", "low"))
    priority_order = (
        queue_policy.get("queues", {}).get("daytime", {}).get("priority_order", [])
        if isinstance(queue_policy.get("queues"), dict)
        else []
    )
    if isinstance(priority_order, list) and priority_name in priority_order:
        return len(priority_order) - priority_order.index(priority_name)
    return 0


def generate_candidates(session_definitions: list[dict[str, Any]]) -> list[str]:
    return sorted(_session_id(session) for session in _candidate_sessions(session_definitions))


def generate_skipped_sessions(
    session_definitions: list[dict[str, Any]],
) -> list[dict[str, str]]:
    skipped_sessions: list[dict[str, str]] = []
    for session in session_definitions:
        session_id = session.get("session_id")
        if session_id in (None, ""):
            skipped_sessions.append(
                {
                    "session_id": "",
                    "reason": "session_id missing",
                }
            )
    return skipped_sessions


def select(
    queue_policy: dict[str, Any],
    project_registry: dict[str, Any],
    session_definitions: list[dict[str, Any]],
) -> str:
    candidates = _candidate_sessions(session_definitions)
    if not candidates:
        return ""
    ranked = sorted(
        candidates,
        key=lambda session: (
            -_priority_rank_value(session, queue_policy, project_registry),
            _session_id(session),
        ),
    )
    return _session_id(ranked[0])


def build_selector_output(
    queue_policy: dict[str, Any],
    project_registry: dict[str, Any],
    session_definitions: list[dict[str, Any]],
    timestamp: str,
    policy_source: str = "docs/config/queue_policy.yaml",
    registry_source: str = "docs/config/project_registry.json",
) -> dict[str, Any]:
    candidate_sessions = generate_candidates(session_definitions)
    skipped_sessions = generate_skipped_sessions(session_definitions)
    selected_session_id = select(queue_policy, project_registry, session_definitions)
    selected_session = next(
        (
            session
            for session in _candidate_sessions(session_definitions)
            if _session_id(session) == selected_session_id
        ),
        {},
    )
    priority_rank_value = (
        _priority_rank_value(selected_session, queue_policy, project_registry)
        if selected_session
        else 0
    )
    selection_reason = (
        f"priority_rank_value 最高位 ({priority_rank_value}) により選定"
        if selected_session_id
        else "候補 session が存在しないため未選定"
    )
    return {
        "candidate_sessions": candidate_sessions,
        "selected_session_id": selected_session_id,
        "selection_reason": selection_reason,
        "metadata": {
            "selector_version": SELECTOR_VERSION,
            "timestamp": timestamp,
            "policy_source": policy_source,
            "registry_source": registry_source,
            "session_count_scanned": len(session_definitions),
            "skipped_sessions": skipped_sessions,
        },
    }
