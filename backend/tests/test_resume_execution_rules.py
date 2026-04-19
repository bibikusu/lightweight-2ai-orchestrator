# -*- coding: utf-8 -*-
"""session-133 M03-D: resume artifact fail-fast と retry_history.json 永続化。"""

import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

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


def _ctx(session_id: str = "session-133-t") -> SessionContext:
    return SessionContext(
        session_id=session_id,
        session_data={
            "session_id": session_id,
            "phase_id": "M03",
            "title": "resume execution rules",
            "goal": "test",
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
            "limits": {"max_retries": 1, "max_changed_files": 5},
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


def _fail_checks(msg: str = "E") -> dict[str, Any]:
    return {
        "test": {"status": "failed", "command": "pytest", "returncode": 1, "stderr": msg, "stdout": ""},
        "lint": {"status": "skipped"},
        "typecheck": {"status": "skipped"},
        "build": {"status": "skipped"},
        "success": False,
    }


def _ok_checks() -> dict[str, Any]:
    return {
        "test": {"status": "passed", "command": "t", "returncode": 0, "stderr": "", "stdout": ""},
        "lint": {"status": "skipped"},
        "typecheck": {"status": "skipped"},
        "build": {"status": "skipped"},
        "success": True,
    }


def test_resume_fails_fast_when_required_artifact_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    sid = "session-133-artifact-missing"
    raw = _base_state(sid)
    art = tmp_path / "artifacts" / sid
    art.mkdir(parents=True)
    for sub in ("prompts", "responses", "patches", "test_results", "logs", "reports"):
        (art / sub).mkdir(parents=True, exist_ok=True)
    (art / "state.json").write_text(json.dumps(raw), encoding="utf-8")
    # prepared_spec を completed と記録しているが artifact を置かない

    monkeypatch.setattr(rs, "ARTIFACTS_DIR", tmp_path / "artifacts")
    monkeypatch.setattr(rs, "load_session_context", lambda _x: _ctx(sid))
    monkeypatch.setattr(sys, "argv", ["run_session.py", "--session-id", sid, "--resume"])

    assert main() == 1
    err = capsys.readouterr().err
    assert "prepared_spec.json" in err
    assert "required artifact missing" in err


def test_retry_history_json_written_to_session_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    sid = "session-133-retry-history"
    ctx = _ctx(sid)
    monkeypatch.setattr(rs, "ARTIFACTS_DIR", tmp_path / "artifacts")
    monkeypatch.setattr(rs, "load_session_context", lambda _sid: ctx)
    monkeypatch.setattr(rs, "enforce_git_sandbox_branch", lambda _sid: None)
    monkeypatch.setattr(
        rs,
        "call_chatgpt_for_prepared_spec",
        lambda _c: {"objective": "obj", "forbidden_changes": [], "allowed_changes": []},
    )
    seq = [_fail_checks("v1"), _ok_checks()]
    si = {"i": 0}

    def _checks(_c: Any, skip_build: bool = False) -> dict[str, Any]:
        r = seq[min(si["i"], len(seq) - 1)]
        si["i"] += 1
        return r

    monkeypatch.setattr(rs, "run_local_checks", _checks)
    monkeypatch.setattr(
        rs,
        "call_claude_for_implementation",
        lambda _ps, _c, _ri=None: {
            "changed_files": ["src/x.py"],
            "implementation_summary": [],
            "risks": [],
            "open_issues": [],
            "proposed_patch": "",
        },
    )
    monkeypatch.setattr(sys, "argv", ["run_session.py", "--session-id", sid])
    with patch("orchestration.providers.openai_client.OpenAIClientWrapper") as m:
        m.return_value.request_retry_instruction.return_value = {}
        assert main() == 0

    hist_path = tmp_path / "artifacts" / sid / "retry_history.json"
    assert hist_path.is_file()
    data = json.loads(hist_path.read_text(encoding="utf-8"))
    assert data["session_id"] == sid
    assert "retry_count" in data
    assert isinstance(data["retry_events"], list)
    assert len(data["retry_events"]) >= 1
    ev0 = data["retry_events"][0]
    assert set(ev0.keys()) >= {
        "attempt_index",
        "resumed_from_stage",
        "executed_stages",
        "patch_apply_executed",
        "started_at_utc",
        "finished_at_utc",
        "result",
    }


def test_state_schema_non_breaking_with_retry_history(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    sid = "session-133-state-schema"
    ctx = _ctx(sid)
    monkeypatch.setattr(rs, "ARTIFACTS_DIR", tmp_path / "artifacts")
    monkeypatch.setattr(rs, "load_session_context", lambda _sid: ctx)
    monkeypatch.setattr(rs, "enforce_git_sandbox_branch", lambda _sid: None)
    monkeypatch.setattr(
        rs,
        "call_chatgpt_for_prepared_spec",
        lambda _c: {"objective": "obj", "forbidden_changes": [], "allowed_changes": []},
    )
    seq = [_fail_checks("x"), _ok_checks()]
    si = {"i": 0}

    def _checks(_c: Any, skip_build: bool = False) -> dict[str, Any]:
        r = seq[min(si["i"], len(seq) - 1)]
        si["i"] += 1
        return r

    monkeypatch.setattr(rs, "run_local_checks", _checks)
    monkeypatch.setattr(
        rs,
        "call_claude_for_implementation",
        lambda _ps, _c, _ri=None: {
            "changed_files": ["a.py"],
            "implementation_summary": [],
            "risks": [],
            "open_issues": [],
            "proposed_patch": "",
        },
    )
    monkeypatch.setattr(sys, "argv", ["run_session.py", "--session-id", sid])
    with patch("orchestration.providers.openai_client.OpenAIClientWrapper") as m:
        m.return_value.request_retry_instruction.return_value = {}
        assert main() == 0

    state_path = tmp_path / "artifacts" / sid / "state.json"
    st = json.loads(state_path.read_text(encoding="utf-8"))
    required = {
        "session_id",
        "current_stage",
        "completed_stages",
        "status",
        "timestamp_utc",
        "failure_stage",
        "failure_type",
    }
    assert set(st.keys()) == required
    assert isinstance(st["completed_stages"], list)


def test_loading_and_validating_always_run_under_resume(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    sid = "session-133"
    raw = _base_state(
        sid,
        completed_stages=["loading", "validating", "git_guard", "prepared_spec"],
        current_stage="implementation",
    )
    art = tmp_path / "artifacts" / sid
    art.mkdir(parents=True)
    for sub in ("prompts", "responses", "patches", "test_results", "logs", "reports"):
        (art / sub).mkdir(parents=True, exist_ok=True)
    (art / "state.json").write_text(json.dumps(raw), encoding="utf-8")
    (art / "responses" / "prepared_spec.json").write_text(json.dumps(_prep(sid)), encoding="utf-8")

    ctx = _ctx(sid)
    loads: list[str] = []
    vals: list[bool] = []

    def _load(s: str) -> SessionContext:
        loads.append(s)
        return ctx

    _orig_val = rs.validate_session_context

    def _wrap_val(c: SessionContext) -> None:
        vals.append(True)
        return _orig_val(c)

    monkeypatch.setattr(rs, "ARTIFACTS_DIR", tmp_path / "artifacts")
    monkeypatch.setattr(rs, "load_session_context", _load)
    monkeypatch.setattr(rs, "validate_session_context", _wrap_val)
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
    monkeypatch.setattr(sys, "argv", ["run_session.py", "--session-id", sid, "--resume"])

    assert main() == 0
    assert loads == [sid]
    assert vals == [True]


def test_implementation_retry_artifact_and_memory_list_preserved() -> None:
    p = Path("/tmp/orch_session") / "responses" / "implementation_result.json"
    assert rs._resume_required_artifact_path(Path("/tmp/orch_session"), "implementation_retry") == p

    src = Path(rs.__file__).read_text(encoding="utf-8")
    idx = src.index("retry_history.append")
    snippet = src[idx : idx + 450]
    for key in ("attempt", "failure_type", "cause_summary", "cause_fingerprint"):
        assert f'"{key}"' in snippet


def test_session_133_scope_preserved() -> None:
    root = Path(__file__).resolve().parents[2]
    spec_path = root / "docs" / "sessions" / "session-133.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    allowed = spec["allowed_changes"]
    assert "orchestration/run_session.py" in allowed
    assert "backend/tests/test_resume_execution_rules.py" in allowed
    forbidden = "\n".join(spec["forbidden_changes"])
    assert "orchestration/providers" in forbidden
    assert "global_rules.md" in forbidden
