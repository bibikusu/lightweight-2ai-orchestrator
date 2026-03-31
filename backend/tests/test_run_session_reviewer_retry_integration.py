# -*- coding: utf-8 -*-

import sys

import orchestration.run_session as rs
from orchestration.run_session import (
    SessionContext,
    build_prepared_spec_prompts,
    build_retry_prompts,
    main,
)

EXPECTED_RETRY_KEYS = [
    "session_id",
    "failure_type",
    "priority",
    "cause_summary",
    "fix_instructions",
    "do_not_change",
    "failed_tests",
    "error_summary",
    "changed_files",
]


def _ctx(session_id: str = "session-52") -> SessionContext:
    return SessionContext(
        session_id=session_id,
        session_data={
            "session_id": session_id,
            "phase_id": "phase12",
            "title": "reviewer retry integration",
            "goal": "retry prompt quality hardening",
            "scope": ["orchestration/run_session.py"],
            "out_of_scope": ["prepared_spec structure change"],
            "constraints": ["minimal changes"],
            "acceptance_ref": "acceptance/session-52.yaml",
        },
        acceptance_data={
            "raw_yaml": "acceptance:\n  - id: AC-1\n    test_name: backend/tests/test_sample.py::test_ok\n",
            "parsed": {},
        },
        master_instruction="master",
        global_rules="rules",
        roadmap_text="roadmap",
        runtime_config={
            "limits": {"max_retries": 1, "max_changed_files": 5},
            "providers": {"openai": {"model": "gpt-test", "timeout_sec": 1}},
        },
    )


def _prepared_spec(session_id: str) -> dict:
    return {
        "session_id": session_id,
        "objective": "o",
        "allowed_changes": ["orchestration/run_session.py"],
        "forbidden_changes": ["docs/sessions", "docs/acceptance"],
        "completion_criteria": [],
        "acceptance_criteria": [],
        "review_points": [],
        "implementation_notes": [],
    }


def _impl() -> dict:
    return {
        "changed_files": ["orchestration/run_session.py"],
        "implementation_summary": ["retry update"],
        "patch_status": "applied",
        "risks": [],
        "open_issues": [],
        "proposed_patch": "",
    }


def _failed_checks() -> dict:
    return {
        "test": {"status": "failed", "command": "pytest", "returncode": 1, "stdout": "", "stderr": "AssertionError: x != y"},
        "lint": {"status": "passed", "command": "ruff", "returncode": 0, "stdout": "", "stderr": ""},
        "typecheck": {"status": "passed", "command": "mypy", "returncode": 0, "stdout": "", "stderr": ""},
        "build": {"status": "passed", "command": "compileall", "returncode": 0, "stdout": "", "stderr": ""},
        "success": False,
    }


def _ok_checks() -> dict:
    return {
        "test": {"status": "passed", "command": "pytest", "returncode": 0, "stdout": "", "stderr": ""},
        "lint": {"status": "passed", "command": "ruff", "returncode": 0, "stdout": "", "stderr": ""},
        "typecheck": {"status": "passed", "command": "mypy", "returncode": 0, "stdout": "", "stderr": ""},
        "build": {"status": "passed", "command": "compileall", "returncode": 0, "stdout": "", "stderr": ""},
        "success": True,
    }


def test_build_retry_prompts_contains_reviewer_contract_constraints():
    """Reviewer 契約の主要拘束が retry の system/user prompt に含まれる。"""
    ctx = _ctx()
    system_prompt, user_prompt = build_retry_prompts(
        ctx, _prepared_spec(ctx.session_id), _impl(), _failed_checks()
    )

    assert "failure_type must be exactly one value." in system_prompt
    assert "Do not expand scope." in system_prompt
    assert "Respect allowed_changes / forbidden_changes strictly." in system_prompt
    assert "do_not_change must stay consistent with forbidden_changes." in system_prompt
    assert "fix_instructions must be limited to the allowed change scope only." in system_prompt
    assert "Do not guess missing facts." in system_prompt

    assert "fix_instructions must stay within allowed_changes only." in user_prompt
    assert "do_not_change must not conflict with forbidden_changes." in user_prompt
    assert "cause_summary must be concrete and specific. Do not use vague words." in user_prompt
    assert "Include failed_tests and error_summary." in user_prompt
    assert "changed_files must be within allowed_changes." in user_prompt


def test_retry_instruction_output_key_structure_is_preserved():
    """retry_instruction のトップレベルキー列挙が既存構造のまま維持される。"""
    _, user_prompt = build_retry_prompts(
        _ctx(),
        _prepared_spec("session-52"),
        _impl(),
        _failed_checks(),
    )
    assert "Return JSON with keys:" in user_prompt
    for key in EXPECTED_RETRY_KEYS:
        assert key in user_prompt


def test_builder_integration_has_no_side_effect_from_reviewer_retry_changes():
    """session-51 の Builder 統合拘束が維持される。"""
    system_prompt, _user_prompt = build_prepared_spec_prompts(_ctx("session-51"))
    assert "One session must have exactly one objective." in system_prompt
    assert "Do not expand scope." in system_prompt
    assert "Keep the existing top-level key structure exactly." in system_prompt


def test_main_retry_stage_log_uses_reviewer_contract_prompt_without_side_effect(
    monkeypatch, tmp_path
):
    """retry stage のログ文言が Reviewer 契約反映済みで、既存フローを壊さない。"""
    session_id = "session-52-main-retry-log"
    ctx = _ctx(session_id)
    monkeypatch.setattr(rs, "ARTIFACTS_DIR", tmp_path / "artifacts")
    monkeypatch.setattr(rs, "load_session_context", lambda _sid: ctx)
    monkeypatch.setattr(rs, "enforce_git_sandbox_branch", lambda _sid: None)
    monkeypatch.setattr(rs, "call_chatgpt_for_prepared_spec", lambda _c: _prepared_spec(session_id))

    impl_calls = {"count": 0}

    def _impl_with_retry(*_a, **_k):
        impl_calls["count"] += 1
        return _impl()

    monkeypatch.setattr(rs, "call_claude_for_implementation", _impl_with_retry)

    checks_calls = {"count": 0}

    def _checks_with_retry(*_a, **_k):
        checks_calls["count"] += 1
        if checks_calls["count"] == 1:
            return _failed_checks()
        return _ok_checks()

    monkeypatch.setattr(rs, "run_local_checks", _checks_with_retry)
    monkeypatch.setattr(
        rs,
        "call_chatgpt_for_retry_instruction",
        lambda *_a, **_k: {
            "session_id": session_id,
            "failure_type": "test_failure",
            "priority": 4,
            "cause_summary": "AssertionError: x != y",
            "fix_instructions": ["pytest failure の最小修正のみ実施する"],
            "do_not_change": ["docs/sessions", "docs/acceptance"],
            "failed_tests": ["backend/tests/test_sample.py::test_ok"],
            "error_summary": "AssertionError: x != y",
            "changed_files": ["orchestration/run_session.py"],
        },
    )
    monkeypatch.setattr(
        rs,
        "retry_loop",
        lambda **_k: {
            "should_retry": True,
            "failure_type": "test_failure",
            "cause_summary": "AssertionError: x != y",
            "retry_count": 0,
            "stop_reason": "",
        },
    )

    stage_messages: list[str] = []
    monkeypatch.setattr(
        rs,
        "log_stage_progress",
        lambda _sid, _stage, message: stage_messages.append(str(message)),
    )
    monkeypatch.setattr(sys, "argv", ["run_session.py", "--session-id", session_id])

    assert main() == 0
    assert any("Reviewer契約反映済みのリトライ指示を生成" in m for m in stage_messages)
    assert impl_calls["count"] >= 2
    assert checks_calls["count"] >= 2
