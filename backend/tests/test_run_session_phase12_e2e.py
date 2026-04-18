# -*- coding: utf-8 -*-
"""Phase12 E2E: session-51（Builder）と session-52（Reviewer/retry）統合後の main() 経路検証。"""

import json
import sys
from typing import Any

import pytest

import orchestration.run_session as rs
from orchestration.run_session import SessionContext, main

pytestmark = pytest.mark.usefixtures("isolate_phase12_e2e_docs_reads")


def _ctx(session_id: str = "session-53") -> SessionContext:
    return SessionContext(
        session_id=session_id,
        session_data={
            "session_id": session_id,
            "phase_id": "phase12",
            "title": "phase12 e2e",
            "goal": "e2e verification",
            "scope": ["orchestration/run_session.py"],
            "out_of_scope": ["docs/"],
            "constraints": ["minimal changes"],
            "acceptance_ref": "acceptance/session-53.yaml",
        },
        acceptance_data={
            "raw_yaml": (
                "acceptance:\n  - id: AC-1\n"
                "    test_name: backend/tests/test_sample.py::test_ok\n"
            ),
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


def _prepared_spec_builder_style(session_id: str) -> dict[str, Any]:
    """Builder 契約で想定される prepared_spec（allowed/forbidden の併記）。"""
    return {
        "session_id": session_id,
        "objective": "Phase12 E2E objective",
        "allowed_changes": ["orchestration/run_session.py"],
        "forbidden_changes": ["docs/sessions", "docs/acceptance"],
        "completion_criteria": ["cc1"],
        "acceptance_criteria": ["ac1"],
        "review_points": ["rp1"],
        "implementation_notes": ["note1"],
    }


def _ok_impl() -> dict[str, Any]:
    return {
        "changed_files": ["orchestration/run_session.py"],
        "implementation_summary": ["ok"],
        "patch_status": "applied",
        "risks": [],
        "open_issues": [],
        "proposed_patch": "",
    }


def _ok_checks() -> dict[str, Any]:
    return {
        "test": {"status": "passed", "command": "pytest", "returncode": 0, "stdout": "", "stderr": ""},
        "lint": {"status": "passed", "command": "ruff", "returncode": 0, "stdout": "", "stderr": ""},
        "typecheck": {"status": "passed", "command": "mypy", "returncode": 0, "stdout": "", "stderr": ""},
        "build": {"status": "passed", "command": "compileall", "returncode": 0, "stdout": "", "stderr": ""},
        "success": True,
    }


def _failed_checks() -> dict[str, Any]:
    return {
        "test": {
            "status": "failed",
            "command": "pytest",
            "returncode": 1,
            "stdout": "",
            "stderr": "AssertionError: x != y",
        },
        "lint": {"status": "passed", "command": "ruff", "returncode": 0, "stdout": "", "stderr": ""},
        "typecheck": {"status": "passed", "command": "mypy", "returncode": 0, "stdout": "", "stderr": ""},
        "build": {"status": "passed", "command": "compileall", "returncode": 0, "stdout": "", "stderr": ""},
        "success": False,
    }


def _retry_instruction_reviewer_style(session_id: str) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "failure_type": "test_failure",
        "priority": 4,
        "cause_summary": "AssertionError: x != y",
        "fix_instructions": ["pytest 失敗の最小修正のみ"],
        "do_not_change": ["docs/sessions", "docs/acceptance"],
        "failed_tests": ["backend/tests/test_sample.py::test_ok"],
        "error_summary": "AssertionError: x != y",
        "changed_files": ["orchestration/run_session.py"],
    }


RETRY_INSTRUCTION_TOP_LEVEL_KEYS = [
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


def test_phase12_e2e_success_path_without_retry(monkeypatch, tmp_path):
    """checks 成功のみ・retry なしで exit 0、呼び出し順は prepared_spec → implementation → checks → report。"""
    session_id = "session-53-e2e-success"
    ctx = _ctx(session_id)
    call_order: list[str] = []

    monkeypatch.setattr(rs, "ARTIFACTS_DIR", tmp_path / "artifacts")
    monkeypatch.setattr(rs, "load_session_context", lambda _sid: ctx)
    monkeypatch.setattr(rs, "enforce_git_sandbox_branch", lambda _sid: None)

    prep = _prepared_spec_builder_style(session_id)

    def _track_prepared(_c: SessionContext) -> dict[str, Any]:
        call_order.append("prepared_spec")
        return prep

    def _track_impl(*_a: Any, **_k: Any) -> dict[str, Any]:
        call_order.append("implementation")
        return _ok_impl()

    def _track_checks(*_a: Any, **_k: Any) -> dict[str, Any]:
        call_order.append("checks")
        return _ok_checks()

    orig_persist = rs.persist_session_reports

    def _track_persist(*a: Any, **kw: Any) -> None:
        call_order.append("report")
        return orig_persist(*a, **kw)

    monkeypatch.setattr(rs, "call_chatgpt_for_prepared_spec", _track_prepared)
    monkeypatch.setattr(rs, "call_claude_for_implementation", _track_impl)
    monkeypatch.setattr(rs, "run_local_checks", _track_checks)
    monkeypatch.setattr(rs, "persist_session_reports", _track_persist)
    monkeypatch.setattr(
        rs,
        "call_chatgpt_for_retry_instruction",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("retry は発火しない想定")),
    )
    monkeypatch.setattr(
        rs,
        "retry_loop",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("retry_loop は呼ばれない想定")),
    )

    monkeypatch.setattr(sys, "argv", ["run_session.py", "--session-id", session_id])

    assert main() == 0
    assert call_order == ["prepared_spec", "implementation", "checks", "report"]
    assert not (tmp_path / "artifacts" / session_id / "responses" / "retry_instruction.json").exists()


def test_phase12_e2e_retry_path_uses_builder_and_reviewer_contract_outputs(monkeypatch, tmp_path):
    """初回 checks 失敗後に retry 指示→再実装→成功。Builder の prepared_spec と Reviewer の retry が併存。"""
    session_id = "session-53-e2e-retry"
    ctx = _ctx(session_id)
    prep = _prepared_spec_builder_style(session_id)

    monkeypatch.setattr(rs, "ARTIFACTS_DIR", tmp_path / "artifacts")
    monkeypatch.setattr(rs, "load_session_context", lambda _sid: ctx)
    monkeypatch.setattr(rs, "enforce_git_sandbox_branch", lambda _sid: None)
    monkeypatch.setattr(rs, "call_chatgpt_for_prepared_spec", lambda _c: prep)

    impl_calls = {"n": 0}

    def _impl_track(*_a: Any, **_k: Any) -> dict[str, Any]:
        impl_calls["n"] += 1
        return _ok_impl()

    monkeypatch.setattr(rs, "call_claude_for_implementation", _impl_track)

    checks_calls = {"n": 0}

    def _checks_track(*_a: Any, **_k: Any) -> dict[str, Any]:
        checks_calls["n"] += 1
        if checks_calls["n"] == 1:
            return _failed_checks()
        return _ok_checks()

    monkeypatch.setattr(rs, "run_local_checks", _checks_track)
    monkeypatch.setattr(
        rs,
        "call_chatgpt_for_retry_instruction",
        lambda *_a, **_k: _retry_instruction_reviewer_style(session_id),
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

    monkeypatch.setattr(sys, "argv", ["run_session.py", "--session-id", session_id])

    assert main() == 0
    assert impl_calls["n"] >= 2
    assert checks_calls["n"] >= 2

    spec_path = tmp_path / "artifacts" / session_id / "responses" / "prepared_spec.json"
    saved_spec = json.loads(spec_path.read_text(encoding="utf-8"))
    assert saved_spec.get("allowed_changes") == prep["allowed_changes"]
    assert saved_spec.get("forbidden_changes") == prep["forbidden_changes"]
    assert saved_spec.get("completion_criteria") == prep["completion_criteria"]

    ri_path = tmp_path / "artifacts" / session_id / "responses" / "retry_instruction.json"
    assert ri_path.is_file()
    saved_ri = json.loads(ri_path.read_text(encoding="utf-8"))
    assert saved_ri.get("fix_instructions") == _retry_instruction_reviewer_style(session_id)["fix_instructions"]


def test_phase12_e2e_preserves_retry_instruction_top_level_keys(monkeypatch, tmp_path):
    """retry 経路で保存される retry_instruction に契約どおりのトップレベルキーが残る。"""
    session_id = "session-53-e2e-retry-keys"
    ctx = _ctx(session_id)
    monkeypatch.setattr(rs, "ARTIFACTS_DIR", tmp_path / "artifacts")
    monkeypatch.setattr(rs, "load_session_context", lambda _sid: ctx)
    monkeypatch.setattr(rs, "enforce_git_sandbox_branch", lambda _sid: None)
    monkeypatch.setattr(
        rs,
        "call_chatgpt_for_prepared_spec",
        lambda _c: _prepared_spec_builder_style(session_id),
    )

    checks_n = {"n": 0}

    def _checks_twice(*_a: Any, **_k: Any) -> dict[str, Any]:
        checks_n["n"] += 1
        if checks_n["n"] == 1:
            return _failed_checks()
        return _ok_checks()

    monkeypatch.setattr(rs, "run_local_checks", _checks_twice)
    monkeypatch.setattr(rs, "call_claude_for_implementation", lambda *_a, **_k: _ok_impl())
    monkeypatch.setattr(
        rs,
        "call_chatgpt_for_retry_instruction",
        lambda *_a, **_k: _retry_instruction_reviewer_style(session_id),
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
    monkeypatch.setattr(sys, "argv", ["run_session.py", "--session-id", session_id])

    assert main() == 0

    ri_path = tmp_path / "artifacts" / session_id / "responses" / "retry_instruction.json"
    data = json.loads(ri_path.read_text(encoding="utf-8"))
    missing = [k for k in RETRY_INSTRUCTION_TOP_LEVEL_KEYS if k not in data]
    assert not missing, f"欠損キー: {missing}"


def test_phase12_e2e_persists_session_report_after_success(monkeypatch, tmp_path):
    """成功完了後に report.json が存在し session_id / status / completion_status を含む。"""
    session_id = "session-53-e2e-report"
    ctx = _ctx(session_id)
    monkeypatch.setattr(rs, "ARTIFACTS_DIR", tmp_path / "artifacts")
    monkeypatch.setattr(rs, "load_session_context", lambda _sid: ctx)
    monkeypatch.setattr(rs, "enforce_git_sandbox_branch", lambda _sid: None)
    monkeypatch.setattr(
        rs,
        "call_chatgpt_for_prepared_spec",
        lambda _c: _prepared_spec_builder_style(session_id),
    )
    monkeypatch.setattr(rs, "call_claude_for_implementation", lambda *_a, **_k: _ok_impl())
    monkeypatch.setattr(rs, "run_local_checks", lambda *_a, **_k: _ok_checks())
    monkeypatch.setattr(
        rs,
        "call_chatgpt_for_retry_instruction",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("retry は不要")),
    )
    monkeypatch.setattr(sys, "argv", ["run_session.py", "--session-id", session_id])

    assert main() == 0

    report_path = tmp_path / "artifacts" / session_id / "report.json"
    assert report_path.is_file()
    rep = json.loads(report_path.read_text(encoding="utf-8"))
    assert rep.get("session_id") == session_id
    assert rep.get("status") == "success"
    assert "completion_status" in rep
    assert rep.get("completion_status") is not None
