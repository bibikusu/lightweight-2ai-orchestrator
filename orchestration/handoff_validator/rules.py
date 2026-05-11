"""Validation rule functions for handoff validator."""

from __future__ import annotations

REQUIRED_KEYS: frozenset = frozenset({
    "schema_version",
    "source_session_id",
    "session_summary",
    "acceptance_summary",
    "completion_summary",
    "reports_summary",
    "inputs",
    "handoff_ready",
    "warnings",
})

FORBIDDEN_TOPLEVEL_FIELDS: frozenset = frozenset({
    "dependency_graph",
    "judge_result",
    "dependencies",
})
# 'ready' は handoff_ready と紛らわしいため禁止集合に含めない (司令塔判定反映)


def check_required_keys(context_pack: dict) -> list:
    errors = []
    for key in REQUIRED_KEYS:
        if key not in context_pack:
            errors.append(f"required key missing: {key}")
    return errors


def check_ac_cc_referential_integrity(session_json: dict, acceptance_yaml: dict) -> list:
    errors = []

    cc_items = session_json.get("completion_criteria", [])
    cc_ids = {c.get("id") for c in cc_items}

    ac_items = acceptance_yaml.get("acceptance", [])
    referenced_cc_ids: set = set()

    for ac in ac_items:
        ac_id = ac.get("id")
        for cc_id in ac.get("completion_criteria_refs", []):
            referenced_cc_ids.add(cc_id)
            if cc_id not in cc_ids:
                errors.append(f"AC {ac_id} references non-existent CC: {cc_id}")

    for cc_id in cc_ids:
        if cc_id not in referenced_cc_ids:
            errors.append(f"orphan CC (not referenced by any AC): {cc_id}")

    return errors


def check_scope_invasion_fields(context_pack: dict) -> list:
    errors = []
    for key in FORBIDDEN_TOPLEVEL_FIELDS:
        if key in context_pack:
            errors.append(f"scope invasion field detected: {key}")
    return errors
