# -*- coding: utf-8 -*-

import json
import sys
from unittest.mock import patch

import orchestration.run_session as rs
from orchestration.run_session import (
    SessionContext,
    build_implementation_prompts,
    main,
    retry_loop,
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


def _fail_checks(msg: str = "E") -> dict:
    return {
        "test": {"status": "failed", "command": "pytest", "returncode": 1, "stderr": msg, "stdout": ""},
        "lint": {"status": "skipped"},
        "typecheck": {"status": "skipped"},
        "build": {"status": "skipped"},
        "success": False,
    }


def _ok_checks() -> dict:
    return {
        "test": {"status": "passed", "command": "t", "returncode": 0, "stderr": "", "stdout": ""},
        "lint": {"status": "skipped"},
        "typecheck": {"status": "skipped"},
        "build": {"status": "skipped"},
        "success": True,
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


def _patch_loop_base(monkeypatch, tmp_path, sid: str, *, max_retries: int = 5):
    ctx = _ctx(sid, max_retries=max_retries)
    monkeypatch.setattr(rs, "ARTIFACTS_DIR", tmp_path / "artifacts")
    monkeypatch.setattr(rs, "load_session_context", lambda _sid: ctx)
    monkeypatch.setattr(rs, "enforce_git_sandbox_branch", lambda _sid: None)
    monkeypatch.setattr(
        rs,
        "call_chatgpt_for_prepared_spec",
        lambda _c: {"objective": "obj", "forbidden_changes": []},
    )
    return ctx


def test_retry_loop_runs_single_iteration_under_v1_limit(monkeypatch, tmp_path):
    """AC-01: v1 制約（最大1回）で Claude retry が単発で走る"""
    sid = "session-06a-multi"
    _patch_loop_base(monkeypatch, tmp_path, sid, max_retries=5)
    # v1 制約で retry は 1 回までなので、1 回目の retry で成功するシーケンスにする
    seq = [_fail_checks("a"), _ok_checks()]
    si = {"i": 0}

    def _checks(_c, skip_build=False):
        r = seq[min(si["i"], len(seq) - 1)]
        si["i"] += 1
        return r

    claude_retry = {"n": 0}

    def _claude(_ps, _ctx, ri=None):
        if ri is not None:
            claude_retry["n"] += 1
        return {
            "changed_files": ["src/x.py"],
            "implementation_summary": [],
            "risks": [],
            "open_issues": [],
            "proposed_patch": "",
        }

    monkeypatch.setattr(rs, "run_local_checks", _checks)
    monkeypatch.setattr(rs, "call_claude_for_implementation", _claude)
    monkeypatch.setattr(sys, "argv", ["run_session.py", "--session-id", sid])
    with patch("orchestration.providers.openai_client.OpenAIClientWrapper") as m:
        m.return_value.request_retry_instruction.return_value = {}
        assert main() == 0
    assert claude_retry["n"] == 1


def test_retry_loop_updates_check_results_each_iteration(monkeypatch, tmp_path):
    """AC-02: ループ毎に checks.json が保存され内容が更新される"""
    sid = "session-06a-checks"
    _patch_loop_base(monkeypatch, tmp_path, sid, max_retries=5)
    seq = [_fail_checks("v1"), _ok_checks()]
    si = {"i": 0}

    def _checks(_c, skip_build=False):
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
    saved = []
    orig_save = rs.save_json

    def _wrap_save(path, data):
        if path.name == "checks.json":
            saved.append(dict(data))
        return orig_save(path, data)

    monkeypatch.setattr(rs, "save_json", _wrap_save)
    with patch("orchestration.providers.openai_client.OpenAIClientWrapper") as m:
        m.return_value.request_retry_instruction.return_value = {}
        assert main() == 0
    assert len(saved) >= 2
    assert saved[0]["success"] is False
    assert any(s.get("success") for s in saved)


def test_retry_loop_passes_retry_instruction_explicitly(monkeypatch, tmp_path):
    """AC-03: Claude 呼び出しに retry_instruction が dict で渡る"""
    sid = "session-06a-explicit"
    _patch_loop_base(monkeypatch, tmp_path, sid, max_retries=5)
    seq = [_fail_checks(), _ok_checks()]
    si = {"i": 0}

    def _checks(_c, skip_build=False):
        r = seq[min(si["i"], len(seq) - 1)]
        si["i"] += 1
        return r

    seen: list[object] = []

    def _claude(_ps, _ctx, ri=None):
        seen.append(ri)
        return {
            "changed_files": ["src/x.py"],
            "implementation_summary": [],
            "risks": [],
            "open_issues": [],
            "proposed_patch": "",
        }

    monkeypatch.setattr(rs, "run_local_checks", _checks)
    monkeypatch.setattr(rs, "call_claude_for_implementation", _claude)
    monkeypatch.setattr(sys, "argv", ["run_session.py", "--session-id", sid])
    with patch("orchestration.providers.openai_client.OpenAIClientWrapper") as m:
        m.return_value.request_retry_instruction.return_value = {}
        assert main() == 0
    assert any(isinstance(x, dict) and x.get("failure_type") for x in seen if x)

    _, user = build_implementation_prompts(
        {"objective": "o"},
        _ctx("x", max_retries=1),
        {"failure_type": "test_failure", "fix_instructions": ["do"]},
    )
    assert "[retry_instruction]" in user


def test_retry_loop_stops_on_same_cause(monkeypatch, tmp_path):
    """AC-04: ループ内で同一原因なら打ち切り（Claude retry 継続なし）"""
    sid = "session-06a-same"
    _patch_loop_base(monkeypatch, tmp_path, sid, max_retries=5)
    monkeypatch.setattr(rs, "run_local_checks", lambda _c, **_: _fail_checks("same"))
    claude_n = {"r": 0}

    def _claude(_ps, _c, ri=None):
        if ri is not None:
            claude_n["r"] += 1
        return {
            "changed_files": ["src/x.py"],
            "implementation_summary": [],
            "risks": [],
            "open_issues": [],
            "proposed_patch": "",
        }

    monkeypatch.setattr(rs, "call_claude_for_implementation", _claude)
    monkeypatch.setattr(sys, "argv", ["run_session.py", "--session-id", sid])

    def _boom(*_a, **_k):
        raise AssertionError("同一原因後は OpenAI を追加で呼ばない想定")

    with patch("orchestration.providers.openai_client.OpenAIClientWrapper") as m:
        m.return_value.request_retry_instruction.return_value = {}
        assert main() == 1
    assert claude_n["r"] == 1
    rep = json.loads(
        (tmp_path / "artifacts" / sid / "reports" / "session_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert rep.get("retry_stopped_same_cause") is True
    assert rep.get("retry_stopped_max_retries") is False


def test_retry_loop_stops_on_max_retries(monkeypatch, tmp_path):
    """AC-05: retry_count 上限でループ・API が打ち切り"""
    sid = "session-06a-maxloop"
    _patch_loop_base(monkeypatch, tmp_path, sid, max_retries=1)
    rdir = tmp_path / "artifacts" / sid / "responses"
    rdir.mkdir(parents=True, exist_ok=True)
    (rdir / "retry_state.json").write_text(
        json.dumps({"retry_count": 1}, ensure_ascii=False),
        encoding="utf-8",
    )
    monkeypatch.setattr(rs, "run_local_checks", lambda _c, **_: _fail_checks())
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

    def _boom(*_a, **_k):
        raise AssertionError("上限時は再取得しない")

    with patch("orchestration.providers.openai_client.OpenAIClientWrapper", side_effect=_boom):
        assert main() == 1
    rep = json.loads(
        (tmp_path / "artifacts" / sid / "reports" / "session_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert rep.get("retry_stopped_max_retries") is True


def test_existing_retry_and_report_flow_not_broken(monkeypatch, tmp_path):
    """AC-06: 単発失敗フローとレポート必須キーが維持される"""
    sid = "session-06a-regress"
    _patch_loop_base(monkeypatch, tmp_path, sid, max_retries=1)
    monkeypatch.setattr(rs, "run_local_checks", lambda _c, **_: _fail_checks())
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
        assert main() == 1
    base = tmp_path / "artifacts" / sid
    rep = json.loads((base / "reports" / "session_report.json").read_text(encoding="utf-8"))
    for key in (
        "session_id",
        "acceptance_results",
        "retry_count",
        "max_retries",
        "retry_stopped_same_cause",
        "retry_stopped_max_retries",
    ):
        assert key in rep


def test_same_failure_not_retried():
    """同一 failure_type + cause_summary は再試行しない。"""
    decision = retry_loop(
        retry_history=[{"attempt": 1, "failure_type": "test_failure", "cause_summary": "A"}],
        failure={"failure_type": "test_failure", "cause_summary": "A"},
        retry_count=1,
        max_retries=3,
    )
    assert decision["should_retry"] is False
    assert decision["stop_reason"] == "same_failure_and_cause"


def test_retry_stops_when_failure_type_repeats():
    """同一 failure_type が連続したら停止する。"""
    decision = retry_loop(
        retry_history=[{"attempt": 1, "failure_type": "type_mismatch", "cause_summary": "old"}],
        failure={"failure_type": "type_mismatch", "cause_summary": "new"},
        retry_count=1,
        max_retries=3,
    )
    assert decision["should_retry"] is False
    assert decision["stop_reason"] == "failure_type_repeated"


def test_retry_stops_at_limit():
    """上限回数到達時は停止する。"""
    decision = retry_loop(
        retry_history=[],
        failure={"failure_type": "build_error", "cause_summary": "B"},
        retry_count=2,
        max_retries=2,
    )
    assert decision["should_retry"] is False
    assert decision["stop_reason"] == "max_retries_reached"
