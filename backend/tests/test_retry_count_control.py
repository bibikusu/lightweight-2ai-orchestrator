# -*- coding: utf-8 -*-

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

import orchestration.run_session as rs
from orchestration.run_session import (
    SessionContext,
    _compute_retry_cause_fingerprint,
    build_session_report_record,
    compute_next_retry_count,
    main,
)


def _session_data(sid: str) -> dict:
    return {
        "session_id": sid,
        "phase_id": "p",
        "title": "t",
        "goal": "g",
        "scope": [],
        "out_of_scope": [],
        "constraints": [],
        "acceptance_ref": "acceptance/session-01.yaml",
    }


def _failing_checks() -> dict:
    return {
        "test": {"status": "failed", "command": "pytest", "returncode": 1, "stderr": "E1", "stdout": ""},
        "lint": {"status": "skipped"},
        "typecheck": {"status": "skipped"},
        "build": {"status": "skipped"},
        "success": False,
    }


def _ctx(sid: str, *, max_retries: int = 3) -> SessionContext:
    return SessionContext(
        session_id=sid,
        session_data=_session_data(sid),
        acceptance_data={"raw_yaml": "", "parsed": {"acceptance": []}},
        master_instruction="",
        global_rules="",
        roadmap_text="",
        runtime_config={
            "limits": {"max_retries": max_retries, "max_changed_files": 5},
            "providers": {"openai": {"model": "gpt-test", "timeout_sec": 1}},
        },
    )


def _patch_main_fail(monkeypatch, tmp_path, sid: str, *, max_retries: int = 3):
    ctx = _ctx(sid, max_retries=max_retries)
    monkeypatch.setattr(rs, "ARTIFACTS_DIR", tmp_path / "artifacts")
    monkeypatch.setattr(rs, "load_session_context", lambda _sid: ctx)
    monkeypatch.setattr(rs, "enforce_git_sandbox_branch", lambda _sid: None)
    monkeypatch.setattr(
        rs,
        "call_chatgpt_for_prepared_spec",
        lambda _c: {"objective": "obj", "forbidden_changes": []},
    )
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
    monkeypatch.setattr(rs, "run_local_checks", lambda _c, skip_build=False: _failing_checks())
    return ctx


def _read_state_count(session_dir: Path) -> int:
    p = session_dir / "responses" / "retry_state.json"
    if not p.is_file():
        return 0
    return int(json.loads(p.read_text(encoding="utf-8")).get("retry_count", 0))


def test_compute_next_retry_count_helper():
    assert compute_next_retry_count(1, False) == 1
    assert compute_next_retry_count(1, True) == 2


def test_retry_count_increments_and_persists(monkeypatch, tmp_path):
    """AC-01: 新規リトライ指示後に retry_count が永続化される"""
    sid = "session-05c-inc"
    _patch_main_fail(monkeypatch, tmp_path, sid, max_retries=3)
    monkeypatch.setattr(sys, "argv", ["run_session.py", "--session-id", sid])
    with patch("orchestration.providers.openai_client.OpenAIClientWrapper") as m:
        m.return_value.request_retry_instruction.return_value = {}
        assert main() == 1
    base = tmp_path / "artifacts" / sid
    assert _read_state_count(base) == 1
    rj = json.loads((base / "responses" / "retry_instruction.json").read_text(encoding="utf-8"))
    assert rj.get("retry_count") == 1


def test_retry_stops_when_max_retries_reached(monkeypatch, tmp_path):
    """AC-02: retry_count >= max_retries で API を呼ばず打ち切る"""
    sid = "session-05c-max"
    _patch_main_fail(monkeypatch, tmp_path, sid, max_retries=2)
    rdir = tmp_path / "artifacts" / sid / "responses"
    rdir.mkdir(parents=True, exist_ok=True)
    (rdir / "retry_state.json").write_text(
        json.dumps({"retry_count": 2}, ensure_ascii=False),
        encoding="utf-8",
    )

    def _boom(*_a, **_k):
        raise AssertionError("上限到達後は OpenAI 不要")

    monkeypatch.setattr(sys, "argv", ["run_session.py", "--session-id", sid])
    with patch("orchestration.providers.openai_client.OpenAIClientWrapper", side_effect=_boom):
        assert main() == 1

    base = tmp_path / "artifacts" / sid
    rj = json.loads((base / "responses" / "retry_instruction.json").read_text(encoding="utf-8"))
    assert rj.get("retry_exhausted") is True
    rep = json.loads((base / "reports" / "session_report.json").read_text(encoding="utf-8"))
    assert rep.get("retry_stopped_max_retries") is True
    assert rep.get("retry_stopped_same_cause") is False


def test_same_cause_stop_has_priority_over_retry_count(monkeypatch, tmp_path):
    """AC-03: 同一原因は retry_count 上限より優先（上限でも同一原因なら exhausted にしない）"""
    sid = "session-05c-priority"
    _patch_main_fail(monkeypatch, tmp_path, sid, max_retries=2)
    fp = _compute_retry_cause_fingerprint(_failing_checks())
    rdir = tmp_path / "artifacts" / sid / "responses"
    rdir.mkdir(parents=True, exist_ok=True)
    (rdir / "retry_instruction.json").write_text(
        json.dumps({"cause_fingerprint": fp}, ensure_ascii=False),
        encoding="utf-8",
    )
    (rdir / "retry_state.json").write_text(
        json.dumps({"retry_count": 2}, ensure_ascii=False),
        encoding="utf-8",
    )

    def _boom(*_a, **_k):
        raise AssertionError("同一原因では OpenAI 不要")

    monkeypatch.setattr(sys, "argv", ["run_session.py", "--session-id", sid])
    with patch("orchestration.providers.openai_client.OpenAIClientWrapper", side_effect=_boom):
        assert main() == 1

    base = tmp_path / "artifacts" / sid
    rj = json.loads((base / "responses" / "retry_instruction.json").read_text(encoding="utf-8"))
    assert rj.get("retry_skipped_same_cause") is True
    assert rj.get("retry_exhausted") is not True
    rep = json.loads((base / "reports" / "session_report.json").read_text(encoding="utf-8"))
    assert rep.get("retry_stopped_same_cause") is True
    assert rep.get("retry_stopped_max_retries") is False


def test_report_contains_retry_count_fields():
    """AC-04: 機械向けレポートに retry 制御フィールドが含まれる"""
    ctx = SessionContext(
        session_id="session-05c-rep",
        session_data={"phase_id": "p", "title": "t", "goal": "g"},
        acceptance_data={"raw_yaml": "", "parsed": {"acceptance": []}},
        master_instruction="",
        global_rules="",
        roadmap_text="",
        runtime_config={"limits": {"max_retries": 3}},
    )
    prepared = {"objective": "o"}
    impl = {
        "changed_files": [],
        "implementation_summary": [],
        "risks": [],
        "open_issues": [],
        "diff_summary": "none",
    }
    checks = {
        "test": {"status": "failed"},
        "lint": {"status": "skipped"},
        "typecheck": {"status": "skipped"},
        "build": {"status": "skipped"},
        "success": False,
    }
    rec = build_session_report_record(
        ctx,
        prepared,
        impl,
        checks,
        retry_control={
            "retry_count": 2,
            "max_retries": 3,
            "retry_stopped_same_cause": False,
            "retry_stopped_max_retries": True,
        },
    )
    assert rec["retry_count"] == 2
    assert rec["max_retries"] == 3
    assert rec["retry_stopped_same_cause"] is False
    assert rec["retry_stopped_max_retries"] is True


def test_existing_retry_and_report_flow_not_broken(monkeypatch, tmp_path):
    """AC-05: 既存の main 失敗フローとレポート既定フィールドを壊さない"""
    sid = "session-05c-existing"
    _patch_main_fail(monkeypatch, tmp_path, sid, max_retries=1)
    monkeypatch.setattr(sys, "argv", ["run_session.py", "--session-id", sid])
    with patch("orchestration.providers.openai_client.OpenAIClientWrapper") as m:
        m.return_value.request_retry_instruction.return_value = {}
        assert main() == 1
    base = tmp_path / "artifacts" / sid
    rep = json.loads((base / "reports" / "session_report.json").read_text(encoding="utf-8"))
    for key in (
        "session_id",
        "changed_files",
        "acceptance_results",
        "retry_count",
        "max_retries",
        "retry_stopped_same_cause",
        "retry_stopped_max_retries",
    ):
        assert key in rep
    assert rep["retry_stopped_same_cause"] is True
    assert rep["retry_stopped_max_retries"] is False
