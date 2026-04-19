# -*- coding: utf-8 -*-
"""session-135 P6B: project_registry.json / queue_policy.yaml 統合の結合テスト。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from orchestration.run_session import (
    RESUME_SKIP_ELIGIBLE_STAGES,
    PIPELINE_STAGES,
    decide_human_gate,
    decide_isolation,
    decide_night_batch,
    decide_retry_route,
    evaluate_all_conditions,
    evaluate_condition,
    load_project_registry,
    load_queue_policy,
    parse_args,
)

_EXPECTED_PIPELINE_STAGES = [
    "loading",
    "validating",
    "git_guard",
    "prepared_spec",
    "implementation",
    "patch_apply",
    "retry_instruction",
    "implementation_retry",
    "drift_check",
    "completed",
]

_EXPECTED_RESUME_SKIP_ELIGIBLE = {
    "git_guard",
    "prepared_spec",
    "implementation",
    "patch_apply",
    "retry_instruction",
    "implementation_retry",
    "drift_check",
}

_STANDARD_ERROR_HANDLING = {
    "undefined_field": "forbidden",
    "type_mismatch": "forbidden",
    "undefined_operator": "parse_error_abort",
}


def test_load_project_registry_returns_10_projects() -> None:
    reg = load_project_registry()
    projects = reg.get("projects")
    assert isinstance(projects, list)
    assert len(projects) == 10
    required_keys = {
        "project_id",
        "category",
        "status",
        "repo_path",
        "db_touch_allowed",
        "night_batch_allowed",
        "deploy_risk",
    }
    for p in projects:
        assert isinstance(p, dict)
        for k in required_keys:
            assert k in p


def test_load_queue_policy_returns_condition_dsl() -> None:
    policy = load_queue_policy()
    dsl = policy.get("condition_dsl")
    assert isinstance(dsl, dict)
    assert "operators" in dsl
    assert "field_source" in dsl
    assert "combination_logic" in dsl
    assert "error_handling" in dsl


def test_condition_dsl_evaluator_operators_and_error_handling() -> None:
    eh = dict(_STANDARD_ERROR_HANDLING)
    base = {
        "project_id": "X",
        "db_touch_allowed": False,
        "deploy_risk": "medium",
        "night_batch_allowed": True,
        "score": 10,
    }

    assert evaluate_condition(base, {"field": "db_touch_allowed", "operator": "eq", "value": False}, eh) is True
    assert evaluate_condition(base, {"field": "db_touch_allowed", "operator": "ne", "value": True}, eh) is True
    assert evaluate_condition(base, {"field": "deploy_risk", "operator": "in", "value": ["low", "medium"]}, eh) is True
    assert evaluate_condition(base, {"field": "deploy_risk", "operator": "not_in", "value": ["critical"]}, eh) is True
    assert evaluate_condition(base, {"field": "score", "operator": "gt", "value": 5}, eh) is True
    assert evaluate_condition(base, {"field": "score", "operator": "lt", "value": 20}, eh) is True
    assert evaluate_condition(base, {"field": "score", "operator": "gte", "value": 10}, eh) is True
    assert evaluate_condition(base, {"field": "score", "operator": "lte", "value": 10}, eh) is True

    assert (
        evaluate_condition(base, {"field": "missing_field", "operator": "eq", "value": 1}, eh) is False
    )

    assert evaluate_condition(base, {"field": "score", "operator": "gt", "value": "nope"}, eh) is False

    not_list = dict(base)
    not_list["bad"] = "x"
    assert evaluate_condition(not_list, {"field": "bad", "operator": "in", "value": "not-a-list"}, eh) is False

    with pytest.raises(ValueError, match="undefined condition_dsl operator"):
        evaluate_condition(base, {"field": "score", "operator": "bogus", "value": 1}, eh)

    assert evaluate_all_conditions(base, [], eh) is True
    assert (
        evaluate_all_conditions(
            base,
            [
                {"field": "db_touch_allowed", "operator": "eq", "value": False},
                {"field": "deploy_risk", "operator": "in", "value": ["medium"]},
            ],
            eh,
        )
        is True
    )


def test_four_decision_functions_against_all_projects() -> None:
    expected: dict[str, tuple[str, bool, bool]] = {
        "A01_Card_task": ("parallel", True, False),
        "A02_fina": ("parallel", True, False),
        "A03_mane_bikusu": ("parallel", True, False),
        "A04_deli_customer_management": ("serial", False, True),
        "A05_CAST_PRO": ("serial", False, True),
        "A06_cecare": ("serial", False, True),
        "A07_pochadeli_work": ("parallel", True, False),
        "A08_AI_video_creation": ("parallel", True, False),
        "A09_AI_movie_production": ("parallel", True, False),
        "A10_fina_date": ("serial", False, True),
    }
    reg = load_project_registry()
    ids = [p.get("project_id") for p in reg.get("projects", []) if isinstance(p, dict)]
    assert len(ids) == 10
    for pid in ids:
        assert isinstance(pid, str)
        iso, night, hg = expected[pid]
        assert decide_isolation(pid) == iso
        assert decide_night_batch(pid) is night
        assert decide_human_gate(pid) is hg

    assert decide_retry_route("A02_fina", "test_failure") == "retry"
    assert decide_retry_route("A02_fina", "scope_violation") == "waiting_human"
    assert decide_retry_route("A02_fina", "unknown_error_kind") == "retry"


def test_project_cli_argument_coexists_with_existing_args(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_session.py",
            "--session-id",
            "session-01",
            "--max-retries",
            "3",
            "--dry-run",
            "--skip-build",
            "--project",
            "A02_fina",
        ],
    )
    args = parse_args()
    assert args.session_id == "session-01"
    assert args.max_retries == 3
    assert args.dry_run is True
    assert args.skip_build is True
    assert args.project == "A02_fina"

    monkeypatch.setattr(sys, "argv", ["run_session.py", "--session-id", "session-02"])
    args2 = parse_args()
    assert args2.session_id == "session-02"
    assert args2.project is None


def test_session_135_non_regression_and_4cmd_gate() -> None:
    import orchestration.run_session as rs

    assert PIPELINE_STAGES == _EXPECTED_PIPELINE_STAGES
    assert len(PIPELINE_STAGES) == 10
    assert PIPELINE_STAGES[-1] == "completed"
    assert RESUME_SKIP_ELIGIBLE_STAGES == _EXPECTED_RESUME_SKIP_ELIGIBLE

    assert callable(rs._resume_load_state)
    assert callable(rs._resume_validate_state)
    assert callable(rs._write_retry_history_artifact)

    src = Path(rs.__file__).read_text(encoding="utf-8")
    assert "state.json" in src
    assert "retry_history.json" in src
