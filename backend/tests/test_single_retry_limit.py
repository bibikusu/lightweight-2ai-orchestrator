# -*- coding: utf-8 -*-

import json
import sys
from unittest.mock import patch

import orchestration.run_session as rs
from orchestration.run_session import SessionContext, main


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


def _ctx(sid: str, *, max_retries: int = 5) -> SessionContext:
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


def test_v1_single_retry_is_enforced_even_if_config_allows_more(monkeypatch, tmp_path):
    """max_retries が大きくても v1 制約で 1 回に強制される（OpenAI は1回のみ）。"""
    sid = "session-single-retry-limit"
    ctx = _ctx(sid, max_retries=5)

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

    seq = [
        {
            "test": {"status": "failed", "command": "pytest", "returncode": 1, "stderr": "E1", "stdout": ""},
            "lint": {"status": "skipped"},
            "typecheck": {"status": "skipped"},
            "build": {"status": "skipped"},
            "success": False,
        },
        {
            "test": {"status": "failed", "command": "pytest", "returncode": 1, "stderr": "E2", "stdout": ""},
            "lint": {"status": "skipped"},
            "typecheck": {"status": "skipped"},
            "build": {"status": "skipped"},
            "success": False,
        },
    ]
    si = {"i": 0}

    def _checks(_c, skip_build=False):
        r = seq[min(si["i"], len(seq) - 1)]
        si["i"] += 1
        return r

    monkeypatch.setattr(rs, "run_local_checks", _checks)
    monkeypatch.setattr(sys, "argv", ["run_session.py", "--session-id", sid])

    with patch("orchestration.providers.openai_client.OpenAIClientWrapper") as m:
        m.return_value.request_retry_instruction.return_value = {}
        assert main() == 1
        assert m.return_value.request_retry_instruction.call_count == 1

    base = tmp_path / "artifacts" / sid
    rj = json.loads((base / "responses" / "retry_instruction.json").read_text(encoding="utf-8"))
    assert rj.get("max_retries") == 5
    assert rj.get("max_retries_effective") == 1
    assert rj.get("retry_count") == 1

    rep = json.loads((base / "reports" / "session_report.json").read_text(encoding="utf-8"))
    assert rep.get("max_retries") == 5
    assert rep.get("retry_stopped_max_retries") is True

