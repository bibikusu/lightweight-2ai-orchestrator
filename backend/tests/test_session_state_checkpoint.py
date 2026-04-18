# -*- coding: utf-8 -*-
"""session-131: state checkpoint (M03-B) 単体・結合検証（実ファイル・API 依存を避ける）。"""

import json
import sys
from pathlib import Path
from typing import Any

import pytest

import orchestration.run_session as rs
from orchestration.run_session import SessionContext, main


def _ctx(session_id: str = "session-131-t") -> SessionContext:
    return SessionContext(
        session_id=session_id,
        session_data={
            "session_id": session_id,
            "phase_id": "M03",
            "title": "checkpoint test",
            "goal": "state json",
            "scope": ["orchestration/run_session.py"],
            "out_of_scope": [],
            "constraints": ["minimal"],
            "acceptance_ref": "acceptance/session-53.yaml",
        },
        acceptance_data={
            "raw_yaml": (
                "session_id: session-53\nacceptance:\n"
                "  - id: AC-1\n"
                "    test_name: backend/tests/test_sample.py::test_ok\n"
            ),
            "parsed": {"session_id": "session-53"},
        },
        master_instruction="m",
        global_rules="r",
        roadmap_text="rm",
        runtime_config={
            "limits": {"max_retries": 0, "max_changed_files": 5},
            "providers": {"openai": {"model": "gpt-test", "timeout_sec": 1}},
        },
    )


def _ok_impl(session_id: str) -> dict[str, Any]:
    return {
        "session_id": session_id,
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


def _prep(session_id: str) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "objective": "t",
        "allowed_changes": ["orchestration/run_session.py"],
        "forbidden_changes": [],
        "completion_criteria": ["c"],
        "acceptance_criteria": [{"id": "a", "description": "d", "test_name": "t"}],
        "review_points": ["1", "2", "3", "検証十分性"],
        "implementation_notes": [],
    }


@pytest.fixture
def checkpoint_happy_mocks(monkeypatch, tmp_path):
    sid = "session-131-happy"
    ctx = _ctx(sid)
    monkeypatch.setattr(rs, "ARTIFACTS_DIR", tmp_path / "artifacts")
    monkeypatch.setattr(rs, "load_session_context", lambda _x: ctx)
    monkeypatch.setattr(rs, "enforce_git_sandbox_branch", lambda _sid: None)
    monkeypatch.setattr(rs, "call_chatgpt_for_prepared_spec", lambda _c: _prep(sid))
    monkeypatch.setattr(
        rs,
        "call_claude_for_implementation",
        lambda *_a, **_k: _ok_impl(sid),
    )
    monkeypatch.setattr(rs, "run_local_checks", lambda *_a, **_k: _ok_checks())
    monkeypatch.setattr(
        rs,
        "call_chatgpt_for_retry_instruction",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("no retry")),
    )
    monkeypatch.setattr(
        rs,
        "retry_loop",
        lambda **_k: (_ for _ in ()).throw(AssertionError("no retry")),
    )
    monkeypatch.setattr(sys, "argv", ["run_session.py", "--session-id", sid])
    return sid, tmp_path


def _load_state(tmp_path: Path, session_id: str) -> dict[str, Any]:
    p = tmp_path / "artifacts" / session_id / "state.json"
    return json.loads(p.read_text(encoding="utf-8"))


def test_state_checkpoint_written_after_stage(checkpoint_happy_mocks):
    """AC-01: stage 実行後に state JSON が生成または更新される。"""
    sid, tmp_path = checkpoint_happy_mocks
    assert main() == 0
    st_path = tmp_path / "artifacts" / sid / "state.json"
    assert st_path.is_file()
    data = json.loads(st_path.read_text(encoding="utf-8"))
    for k in (
        "session_id",
        "current_stage",
        "completed_stages",
        "status",
        "timestamp_utc",
        "failure_stage",
        "failure_type",
    ):
        assert k in data


def test_completed_stages_updated_correctly(checkpoint_happy_mocks):
    """AC-02: stage 完了時に completed_stages が正しく更新される。"""
    sid, tmp_path = checkpoint_happy_mocks
    assert main() == 0
    data = _load_state(tmp_path, sid)
    assert data["status"] == "completed"
    exp_prefix = ["loading", "validating", "git_guard", "prepared_spec", "implementation", "patch_apply"]
    assert data["completed_stages"] == exp_prefix


def test_failure_state_persisted(monkeypatch, tmp_path):
    """AC-03: failure 時に failure_stage と failure_type が保存される。"""
    sid = "session-131-fail"
    ctx = _ctx(sid)
    monkeypatch.setattr(rs, "ARTIFACTS_DIR", tmp_path / "artifacts")
    monkeypatch.setattr(rs, "load_session_context", lambda _x: ctx)
    monkeypatch.setattr(rs, "enforce_git_sandbox_branch", lambda _sid: None)
    monkeypatch.setattr(rs, "call_chatgpt_for_prepared_spec", lambda _c: _prep(sid))

    def _boom(*_a, **_k):
        raise RuntimeError("planned impl failure")

    monkeypatch.setattr(rs, "call_claude_for_implementation", _boom)
    monkeypatch.setattr(sys, "argv", ["run_session.py", "--session-id", sid])
    assert main() == 1
    data = _load_state(tmp_path, sid)
    assert data["status"] == "failed"
    assert data["failure_stage"] == "implementation"
    assert data["failure_type"] == "RuntimeError"


def test_checkpoint_does_not_break_existing_flow(monkeypatch, tmp_path):
    """AC-04: dry-run と通常 mock 成功フローが壊れていない。"""
    sid = "session-131-dry"
    ctx = _ctx(sid)
    monkeypatch.setattr(rs, "ARTIFACTS_DIR", tmp_path / "artifacts")
    monkeypatch.setattr(rs, "load_session_context", lambda _x: ctx)
    monkeypatch.setattr(rs, "enforce_git_sandbox_branch", lambda _sid: None)
    monkeypatch.setattr(rs, "call_chatgpt_for_prepared_spec", lambda _c: _prep(sid))
    monkeypatch.setattr(
        rs,
        "call_claude_for_implementation",
        lambda *_a, **_k: _ok_impl(sid),
    )
    monkeypatch.setattr(rs, "run_local_checks", lambda *_a, **_k: _ok_checks())
    monkeypatch.setattr(
        rs,
        "call_chatgpt_for_retry_instruction",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("no retry")),
    )
    monkeypatch.setattr(
        rs,
        "retry_loop",
        lambda **_k: (_ for _ in ()).throw(AssertionError("no retry")),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_session.py", "--session-id", sid, "--dry-run"],
    )
    assert main() == 0
    assert not (tmp_path / "artifacts" / sid / "state.json").exists()

    sid2 = "session-131-norm"
    ctx2 = _ctx(sid2)
    monkeypatch.setattr(rs, "load_session_context", lambda _x: ctx2)
    monkeypatch.setattr(rs, "call_chatgpt_for_prepared_spec", lambda _c: _prep(sid2))
    monkeypatch.setattr(
        rs,
        "call_claude_for_implementation",
        lambda *_a, **_k: _ok_impl(sid2),
    )
    monkeypatch.setattr(sys, "argv", ["run_session.py", "--session-id", sid2])
    assert main() == 0
    assert (tmp_path / "artifacts" / sid2 / "state.json").is_file()


def test_checkpoint_scope_is_preserved(checkpoint_happy_mocks):
    """AC-05: checkpoint が M03-A 最小スキーマに収まり、余計なキーを増やしていない。"""
    sid, tmp_path = checkpoint_happy_mocks
    assert main() == 0
    data = _load_state(tmp_path, sid)
    allowed = {
        "session_id",
        "current_stage",
        "completed_stages",
        "status",
        "timestamp_utc",
        "failure_stage",
        "failure_type",
    }
    assert set(data.keys()) == allowed
