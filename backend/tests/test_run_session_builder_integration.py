# -*- coding: utf-8 -*-

import sys

import orchestration.run_session as rs
from orchestration.run_session import SessionContext, build_prepared_spec_prompts, main

EXPECTED_PREPARED_SPEC_KEYS = [
    "session_id",
    "objective",
    "allowed_changes",
    "forbidden_changes",
    "completion_criteria",
    "acceptance_criteria",
    "review_points",
    "implementation_notes",
]


def _ctx(session_id: str = "session-51") -> SessionContext:
    return SessionContext(
        session_id=session_id,
        session_data={
            "session_id": session_id,
            "phase_id": "phase12",
            "title": "builder integration",
            "goal": "prepared_spec quality hardening",
            "scope": ["orchestration/run_session.py"],
            "out_of_scope": ["retry", "reviewer"],
            "constraints": ["minimal changes"],
            "acceptance_ref": "acceptance/session-51.yaml",
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


def _ok_impl() -> dict:
    return {
        "changed_files": ["orchestration/run_session.py"],
        "implementation_summary": ["ok"],
        "patch_status": "applied",
        "risks": [],
        "open_issues": [],
        "proposed_patch": "",
    }


def _ok_checks() -> dict:
    return {
        "test": {"status": "passed", "command": "pytest", "returncode": 0, "stdout": "", "stderr": ""},
        "lint": {"status": "passed", "command": "ruff", "returncode": 0, "stdout": "", "stderr": ""},
        "typecheck": {"status": "passed", "command": "mypy", "returncode": 0, "stdout": "", "stderr": ""},
        "build": {"status": "passed", "command": "compileall", "returncode": 0, "stdout": "", "stderr": ""},
        "success": True,
    }


def test_build_prepared_spec_prompts_contains_builder_contract_constraints():
    """Builder 契約の主要拘束が system/user prompt に含まれる。"""
    system_prompt, user_prompt = build_prepared_spec_prompts(_ctx())

    assert "One session must have exactly one objective." in system_prompt
    assert "Return only valid JSON." in system_prompt
    assert "Do not add markdown fences." in system_prompt
    assert "Do not expand scope." in system_prompt
    assert "Respect allowed_changes / forbidden_changes." in system_prompt
    assert "completion_criteria / acceptance_criteria / review_points are required." in system_prompt
    assert "Acceptance must be test-mappable." in system_prompt
    assert "Do not guess missing facts." in system_prompt
    assert "Keep the existing top-level key structure exactly." in system_prompt

    assert "allowed_changes must be concrete and actionable." in user_prompt
    assert "forbidden_changes must not conflict with out_of_scope." in user_prompt
    assert "completion_criteria must include normal-path, error-path, and no-side-effect checks." in user_prompt
    assert "acceptance_criteria must remain test-mappable." in user_prompt
    assert "review_points must include exactly these 4 axes:" in user_prompt
    assert "1) spec match (AC achieved)" in user_prompt
    assert "2) scope adherence" in user_prompt
    assert "3) no side effects (no regression)" in user_prompt
    assert "4) no over/under implementation" in user_prompt


def test_prepared_spec_output_key_structure_is_preserved():
    """prepared_spec のトップレベルキー列挙が既存構造のまま維持される。"""
    _, user_prompt = build_prepared_spec_prompts(_ctx())

    assert "Return JSON with keys:" in user_prompt
    for key in EXPECTED_PREPARED_SPEC_KEYS:
        assert f"\n{key}\n" in f"\n{user_prompt}\n"


def test_main_prepared_spec_stage_log_is_builder_contract_aware(monkeypatch, tmp_path):
    """prepared_spec stage のログ文言が Builder 契約反映済みで、成功経路に副作用がない。"""
    session_id = "session-51-main-log"
    ctx = _ctx(session_id)
    monkeypatch.setattr(rs, "ARTIFACTS_DIR", tmp_path / "artifacts")
    monkeypatch.setattr(rs, "load_session_context", lambda _sid: ctx)
    monkeypatch.setattr(rs, "enforce_git_sandbox_branch", lambda _sid: None)
    monkeypatch.setattr(
        rs,
        "call_chatgpt_for_prepared_spec",
        lambda _c: {
            "session_id": session_id,
            "objective": "o",
            "allowed_changes": [],
            "forbidden_changes": [],
            "completion_criteria": [],
            "acceptance_criteria": [],
            "review_points": [],
            "implementation_notes": [],
        },
    )
    monkeypatch.setattr(rs, "call_claude_for_implementation", lambda *_a, **_k: _ok_impl())
    monkeypatch.setattr(rs, "run_local_checks", lambda *_a, **_k: _ok_checks())

    stage_messages: list[str] = []
    monkeypatch.setattr(
        rs,
        "log_stage_progress",
        lambda _sid, _stage, message: stage_messages.append(str(message)),
    )
    monkeypatch.setattr(sys, "argv", ["run_session.py", "--session-id", session_id])

    assert main() == 0
    assert any("Builder契約反映の仕様整形" in m for m in stage_messages)
    assert not (tmp_path / "artifacts" / session_id / "responses" / "retry_instruction.json").exists()


def test_builder_integration_does_not_invoke_retry_or_reviewer_paths(monkeypatch, tmp_path):
    """Builder 統合の最小実装で retry / reviewer 系に依存しない。"""
    session_id = "session-51-no-retry"
    ctx = _ctx(session_id)
    monkeypatch.setattr(rs, "ARTIFACTS_DIR", tmp_path / "artifacts")
    monkeypatch.setattr(rs, "load_session_context", lambda _sid: ctx)
    monkeypatch.setattr(rs, "enforce_git_sandbox_branch", lambda _sid: None)
    monkeypatch.setattr(
        rs,
        "call_chatgpt_for_prepared_spec",
        lambda _c: {
            "session_id": session_id,
            "objective": "o",
            "allowed_changes": [],
            "forbidden_changes": [],
            "completion_criteria": [],
            "acceptance_criteria": [],
            "review_points": [],
            "implementation_notes": [],
        },
    )
    monkeypatch.setattr(rs, "call_claude_for_implementation", lambda *_a, **_k: _ok_impl())
    monkeypatch.setattr(rs, "run_local_checks", lambda *_a, **_k: _ok_checks())
    monkeypatch.setattr(
        rs,
        "call_chatgpt_for_retry_instruction",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("retry 系は呼ばれない想定")),
    )
    monkeypatch.setattr(
        rs,
        "retry_loop",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("retry_loop は呼ばれない想定")),
    )
    monkeypatch.setattr(
        rs,
        "classify_failure",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("失敗分類は呼ばれない想定")),
    )
    monkeypatch.setattr(sys, "argv", ["run_session.py", "--session-id", session_id])

    assert main() == 0
