#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Session / acceptance definition drift detection (fail-fast, v0.1)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

EXPECTED_REVIEW_POINTS = [
    "仕様一致（AC達成）",
    "変更範囲遵守",
    "副作用なし（既存破壊なし）",
    "実装過不足なし",
]

SESSION_REQUIRED_KEYS = [
    "session_id",
    "phase_id",
    "title",
    "goal",
    "scope",
    "out_of_scope",
    "constraints",
    "acceptance_ref",
    "allowed_changes",
    "allowed_changes_detail",
    "forbidden_changes",
    "review_points",
    "completion_criteria",
]

COMPLETION_CRITERIA_TYPES = frozenset(
    {
        "document_rule",
        "artifact",
        "non_regression",
        "state_transition_consistent",
        "side_effect_free",
    }
)

COMPLETION_STATUS_ALLOWED = frozenset({"usable_for_self", "review_required", "failed"})

SCOPE_VIOLATION_CODES = frozenset({"SCOPE_COUNT", "OUT_OF_SCOPE_COUNT", "ALLOWED_CHANGES_UNMAPPED"})


def _load_session_json(path: str) -> dict[str, Any]:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("session JSON root must be an object")
    return data


def _load_acceptance_yaml(path: str) -> dict[str, Any]:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("acceptance YAML root must be a mapping")
    return data


def _validate_required_keys(session: dict[str, Any]) -> list[dict[str, str]]:
    missing = sorted(k for k in SESSION_REQUIRED_KEYS if k not in session)
    out: list[dict[str, str]] = []
    for key in missing:
        out.append(
            {
                "code": "SESSION_REQUIRED_KEY",
                "path": f"session.{key}",
                "message": f"missing required key: {key}",
            }
        )
    return out


def _validate_review_points(session: dict[str, Any]) -> list[dict[str, str]]:
    if "review_points" not in session:
        return []
    rp = session.get("review_points")
    if rp != EXPECTED_REVIEW_POINTS:
        return [
            {
                "code": "REVIEW_POINTS_MISMATCH",
                "path": "session.review_points",
                "message": "review_points must exactly match the four fixed axes (order and text)",
            }
        ]
    return []


def _validate_allowed_changes_detail(session: dict[str, Any]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    if "allowed_changes_detail" not in session:
        return []

    detail = session.get("allowed_changes_detail")
    if not isinstance(detail, list):
        return [
            {
                "code": "ALLOWED_CHANGES_DETAIL_TYPE",
                "path": "session.allowed_changes_detail",
                "message": "allowed_changes_detail must be a list of strings",
            }
        ]

    for i, entry in enumerate(detail):
        if not isinstance(entry, str) or not entry.strip():
            out.append(
                {
                    "code": "ALLOWED_CHANGES_DETAIL_ENTRY",
                    "path": f"session.allowed_changes_detail[{i}]",
                    "message": "each entry must be a non-empty string",
                }
            )
            continue
        if ":" not in entry:
            out.append(
                {
                    "code": "ALLOWED_CHANGES_DETAIL_FORMAT",
                    "path": f"session.allowed_changes_detail[{i}]",
                    "message": 'each entry must be "path: description" (missing ":")',
                }
            )
            continue
        head, tail = entry.split(":", 1)
        if not head.strip() or not tail.strip():
            out.append(
                {
                    "code": "ALLOWED_CHANGES_DETAIL_FORMAT",
                    "path": f"session.allowed_changes_detail[{i}]",
                    "message": "path and description parts must be non-empty",
                }
            )

    allowed = session.get("allowed_changes")
    if not isinstance(allowed, list):
        if "allowed_changes" in session:
            out.append(
                {
                    "code": "ALLOWED_CHANGES_TYPE",
                    "path": "session.allowed_changes",
                    "message": "allowed_changes must be a list of strings",
                }
            )
        return out

    path_prefixes: list[str] = []
    for entry in detail:
        if isinstance(entry, str) and ":" in entry:
            head, _tail = entry.split(":", 1)
            if head.strip() and _tail.strip():
                path_prefixes.append(head.strip())

    for ac in allowed:
        if not isinstance(ac, str) or not str(ac).strip():
            out.append(
                {
                    "code": "ALLOWED_CHANGES_ENTRY",
                    "path": "session.allowed_changes",
                    "message": "each allowed_changes entry must be a non-empty string",
                }
            )
            continue
        needle = str(ac).strip()
        if not any(p == needle for p in path_prefixes):
            out.append(
                {
                    "code": "ALLOWED_CHANGES_UNMAPPED",
                    "path": "session.allowed_changes",
                    "message": f"no allowed_changes_detail line for: {needle}",
                }
            )

    return out


def _validate_acceptance_test_names(acceptance: dict[str, Any]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    items = acceptance.get("acceptance")
    if items is None:
        return [
            {
                "code": "ACCEPTANCE_ROOT",
                "path": "acceptance",
                "message": "missing top-level 'acceptance' key",
            }
        ]
    if not isinstance(items, list):
        return [
            {
                "code": "ACCEPTANCE_TYPE",
                "path": "acceptance",
                "message": "acceptance must be a list",
            }
        ]

    names: list[str] = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            out.append(
                {
                    "code": "ACCEPTANCE_ITEM_TYPE",
                    "path": f"acceptance[{i}]",
                    "message": "each acceptance item must be a mapping",
                }
            )
            continue
        for field in ("id", "description", "test_name"):
            if field not in item:
                out.append(
                    {
                        "code": "ACCEPTANCE_FIELD_MISSING",
                        "path": f"acceptance[{i}].{field}",
                        "message": f"missing required field: {field}",
                    }
                )
        tn = item.get("test_name")
        if isinstance(tn, str) and tn.strip():
            names.append(tn.strip())

    seen: dict[str, int] = {}
    for n in names:
        seen[n] = seen.get(n, 0) + 1
    for n, cnt in sorted(seen.items()):
        if cnt > 1:
            out.append(
                {
                    "code": "ACCEPTANCE_TEST_NAME_DUPLICATE",
                    "path": "acceptance",
                    "message": f"duplicate test_name: {n} ({cnt} occurrences)",
                }
            )
    return out


def _validate_completion_criteria(session: dict[str, Any]) -> list[dict[str, str]]:
    if "completion_criteria" not in session:
        return []
    cc = session.get("completion_criteria")
    if not isinstance(cc, list):
        return [
            {
                "code": "COMPLETION_CRITERIA_TYPE",
                "path": "session.completion_criteria",
                "message": "completion_criteria must be a list",
            }
        ]
    out: list[dict[str, str]] = []
    for i, item in enumerate(cc):
        if not isinstance(item, dict):
            out.append(
                {
                    "code": "COMPLETION_CRITERIA_ITEM_TYPE",
                    "path": f"session.completion_criteria[{i}]",
                    "message": "each item must be a mapping",
                }
            )
            continue
        cid = item.get("id")
        if not isinstance(cid, str) or not cid.strip():
            out.append(
                {
                    "code": "COMPLETION_CRITERIA_ID",
                    "path": f"session.completion_criteria[{i}].id",
                    "message": "id must be a non-empty string",
                }
            )
        ctype = item.get("type")
        if ctype not in COMPLETION_CRITERIA_TYPES:
            out.append(
                {
                    "code": "COMPLETION_CRITERIA_TYPE_ENUM",
                    "path": f"session.completion_criteria[{i}].type",
                    "message": f"invalid type: {ctype!r}",
                }
            )
        cond = item.get("condition")
        if not isinstance(cond, str) or not cond.strip():
            out.append(
                {
                    "code": "COMPLETION_CRITERIA_CONDITION",
                    "path": f"session.completion_criteria[{i}].condition",
                    "message": "condition must be a non-empty string",
                }
            )
    return out


def _validate_completion_status(session: dict[str, Any]) -> list[dict[str, str]]:
    if "completion_status" not in session:
        return []
    val = session.get("completion_status")
    if val not in COMPLETION_STATUS_ALLOWED:
        return [
            {
                "code": "COMPLETION_STATUS_INVALID",
                "path": "session.completion_status",
                "message": f"must be one of {sorted(COMPLETION_STATUS_ALLOWED)}, got {val!r}",
            }
        ]
    return []


def _build_drift_result(violations: list[dict[str, str]]) -> dict[str, Any]:
    ok = len(violations) == 0
    failure_type: str | None = None
    summary: str | None = None
    if not ok:
        if any(v.get("code") in SCOPE_VIOLATION_CODES for v in violations):
            failure_type = "scope_violation"
        else:
            failure_type = "spec_missing"
        summary = f"drift check failed with {len(violations)} violation(s)"
    return {
        "ok": ok,
        "failure_type": failure_type,
        "violations": violations,
        "summary": summary,
    }


def run_drift_check(session_path: str, acceptance_path: str) -> dict[str, Any]:
    violations: list[dict[str, str]] = []

    session: dict[str, Any] = {}
    session_loaded = False
    try:
        session = _load_session_json(session_path)
        session_loaded = True
    except Exception as exc:
        violations.append(
            {
                "code": "SESSION_LOAD_FAILED",
                "path": session_path,
                "message": str(exc),
            }
        )

    acceptance: dict[str, Any] = {}
    try:
        acceptance = _load_acceptance_yaml(acceptance_path)
    except Exception as exc:
        violations.append(
            {
                "code": "ACCEPTANCE_LOAD_FAILED",
                "path": acceptance_path,
                "message": str(exc),
            }
        )

    if session_loaded:
        violations.extend(_validate_required_keys(session))

        if "scope" in session:
            sc = session.get("scope")
            if isinstance(sc, list):
                if len(sc) > 6:
                    violations.append(
                        {
                            "code": "SCOPE_COUNT",
                            "path": "session.scope",
                            "message": f"scope must have at most 6 items (got {len(sc)})",
                        }
                    )
            else:
                violations.append(
                    {
                        "code": "SCOPE_TYPE",
                        "path": "session.scope",
                        "message": "scope must be a list",
                    }
                )

        if "out_of_scope" in session:
            os_val = session.get("out_of_scope")
            if isinstance(os_val, list):
                if len(os_val) > 8:
                    violations.append(
                        {
                            "code": "OUT_OF_SCOPE_COUNT",
                            "path": "session.out_of_scope",
                            "message": (
                                f"out_of_scope must have at most 8 items (got {len(os_val)})"
                            ),
                        }
                    )
            else:
                violations.append(
                    {
                        "code": "OUT_OF_SCOPE_TYPE",
                        "path": "session.out_of_scope",
                        "message": "out_of_scope must be a list",
                    }
                )

        violations.extend(_validate_review_points(session))
        violations.extend(_validate_allowed_changes_detail(session))
        violations.extend(_validate_completion_criteria(session))
        violations.extend(_validate_completion_status(session))

    violations.extend(_validate_acceptance_test_names(acceptance))

    return _build_drift_result(violations)
