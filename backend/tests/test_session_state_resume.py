# -*- coding: utf-8 -*-
"""session-132: resume state 読込・検証・stage skip（M03-C）。"""

import inspect
import json
import sys
from typing import Any

import pytest

import orchestration.run_session as rs
from orchestration.run_session import SessionContext, main


def _base_state(session_id: str, **overrides: Any) -> dict[str, Any]:
    st: dict[str, Any] = {
        "session_id": session_id,
        "current_stage": "implementation",
        "completed_stages": ["loading", "validating", "git_guard", "prepared_spec"],
        "status": "running",
        "timestamp_utc": "2026-04-18T12:00:00Z",
        "failure_stage": None,
        "failure_type": None,
    }
    st.update(overrides)
    return st


def _ctx(session_id: str = "session-132-t") -> SessionContext:
    return SessionContext(
        session_id=session_id,
        session_data={
            "session_id": session_id,
            "phase_id": "M03",
            "title": "resume test",
            "goal": "resume",
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


def test_resume_loads_state_and_selects_start_stage(monkeypatch, tmp_path):
    """AC-01: 正常 state を読み、start_stage が current_stage と一致する。"""
    sid = "session-132-ac01"
    raw = _base_state(
        sid,
        completed_stages=["loading", "validating", "git_guard"],
        current_stage="prepared_spec",
    )
    art = tmp_path / "artifacts" / sid
    art.mkdir(parents=True)
    (art / "state.json").write_text(json.dumps(raw), encoding="utf-8")

    monkeypatch.setattr(rs, "ARTIFACTS_DIR", tmp_path / "artifacts")
    loaded = rs._resume_load_state(sid)
    rs._resume_validate_state(loaded, sid)
    assert rs._resume_determine_start_stage(loaded) == loaded["current_stage"]

    ctx = _ctx(sid)
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
        ["run_session.py", "--session-id", sid, "--resume"],
    )
    assert main() == 0


def test_resume_skips_completed_stages(monkeypatch, tmp_path):
    """AC-02: git_guard / prepared_spec がスキップされ本体が呼ばれない。"""
    sid = "session-132-ac02"
    raw = _base_state(sid)
    art = tmp_path / "artifacts" / sid
    art.mkdir(parents=True)
    for sub in ("prompts", "responses", "patches", "test_results", "logs", "reports"):
        (art / sub).mkdir(parents=True, exist_ok=True)
    (art / "state.json").write_text(json.dumps(raw), encoding="utf-8")
    (art / "responses" / "prepared_spec.json").write_text(
        json.dumps(_prep(sid)),
        encoding="utf-8",
    )

    git_calls: list[Any] = []
    prep_calls: list[Any] = []

    def _track_git(_sid: str) -> None:
        git_calls.append(True)

    def _track_prep(_c: Any) -> dict[str, Any]:
        prep_calls.append(True)
        return _prep(sid)

    monkeypatch.setattr(rs, "ARTIFACTS_DIR", tmp_path / "artifacts")
    ctx = _ctx(sid)
    monkeypatch.setattr(rs, "load_session_context", lambda _x: ctx)
    monkeypatch.setattr(rs, "enforce_git_sandbox_branch", _track_git)
    monkeypatch.setattr(rs, "call_chatgpt_for_prepared_spec", _track_prep)
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
        ["run_session.py", "--session-id", sid, "--resume"],
    )
    assert main() == 0
    assert git_calls == []
    assert prep_calls == []


def test_resume_stops_on_missing_state_stderr(monkeypatch, tmp_path, capsys):
    sid = "session-132-missing"
    monkeypatch.setattr(rs, "ARTIFACTS_DIR", tmp_path / "artifacts")
    monkeypatch.setattr(sys, "argv", ["run_session.py", "--session-id", sid, "--resume"])
    assert main() == 1
    assert "state.json not found" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("cli_sid", "broken_state", "reason_substring"),
    [
        (
            "cli-x",
            {**_base_state("cli-x"), "session_id": "different-id"},
            "session_id",
        ),
        (
            "session-132-br",
            _base_state("session-132-br", timestamp_utc="not-a-timestamp"),
            "timestamp",
        ),
        (
            "session-132-br",
            _base_state(
                "session-132-br",
                completed_stages=["loading", "unknown_stage"],
            ),
            "completed_stages",
        ),
        (
            "session-132-br",
            _base_state(
                "session-132-br",
                completed_stages=["loading", "completed"],
            ),
            "completed_stages",
        ),
        (
            "session-132-br",
            _base_state(
                "session-132-br",
                status="completed",
                current_stage="completed",
                failure_stage="implementation",
                failure_type=None,
                completed_stages=[
                    "loading",
                    "validating",
                    "git_guard",
                    "prepared_spec",
                    "implementation",
                    "patch_apply",
                ],
            ),
            "failure",
        ),
        (
            "session-132-br",
            _base_state(
                "session-132-br",
                status="running",
                current_stage="unknown_stage",
            ),
            "current_stage",
        ),
        (
            "session-132-br",
            _base_state(
                "session-132-br",
                status="failed",
                failure_stage=None,
                failure_type="RuntimeError",
                current_stage="implementation",
            ),
            "failure_stage",
        ),
        (
            "session-132-br",
            _base_state(
                "session-132-br",
                current_stage="git_guard",
                completed_stages=["patch_apply"],
                status="running",
            ),
            "order",
        ),
    ],
)
def test_resume_stops_on_inconsistent_state(
    monkeypatch,
    tmp_path,
    capsys,
    cli_sid: str,
    broken_state: dict[str, Any],
    reason_substring: str,
):
    """AC-03 / DP-06 7 項目 + 追加の完了ステージ整合。"""
    art = tmp_path / "artifacts" / cli_sid
    art.mkdir(parents=True)
    (art / "state.json").write_text(json.dumps(broken_state), encoding="utf-8")

    monkeypatch.setattr(rs, "ARTIFACTS_DIR", tmp_path / "artifacts")
    monkeypatch.setattr(rs, "load_session_context", lambda _x: _ctx(cli_sid))
    monkeypatch.setattr(sys, "argv", ["run_session.py", "--session-id", cli_sid, "--resume"])
    assert main() == 1
    err = capsys.readouterr().err.lower()
    assert reason_substring.lower() in err


def test_resume_does_not_break_existing_flows(monkeypatch, tmp_path):
    """AC-04: --resume なしの mock 経路が従来通り。"""
    sid = "session-132-norm"
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
    assert main() == 0
    st = json.loads((tmp_path / "artifacts" / sid / "state.json").read_text(encoding="utf-8"))
    assert st["status"] == "completed"

    sid2 = "session-132-dry"
    ctx2 = _ctx(sid2)
    monkeypatch.setattr(rs, "load_session_context", lambda _x: ctx2)
    monkeypatch.setattr(sys, "argv", ["run_session.py", "--session-id", sid2, "--dry-run"])
    assert main() == 0
    assert not (tmp_path / "artifacts" / sid2 / "state.json").exists()


def test_resume_scope_is_preserved():
    """AC-05: checkpoint 系はシグネチャが維持されている。"""
    assert rs.PIPELINE_STAGES
    for name in (
        "_write_session_state_checkpoint",
        "_checkpoint_stage_begin",
        "_checkpoint_stage_complete",
        "_checkpoint_should_record",
        "_checkpoint_timestamp_utc",
    ):
        assert hasattr(rs, name)
        sig = str(inspect.signature(getattr(rs, name)))
        if name == "_checkpoint_timestamp_utc":
            assert "->" in sig
        elif name == "_checkpoint_should_record":
            assert "args" in sig
        else:
            assert "session_dir" in sig

