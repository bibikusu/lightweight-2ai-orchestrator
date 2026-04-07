# -*- coding: utf-8 -*-

import json
import sys
from typing import Any

import orchestration.run_session as rs
from orchestration.run_session import SessionContext, main, persist_session_reports, run_gpt_review_stage


def _ctx(session_id: str) -> SessionContext:
    return SessionContext(
        session_id=session_id,
        session_data={
            "session_id": session_id,
            "phase_id": "phase15",
            "title": "gpt review stage",
            "goal": "session-15 verification",
            "scope": ["orchestration/run_session.py"],
            "out_of_scope": ["docs/"],
            "constraints": ["minimal changes"],
            "acceptance_ref": "acceptance/session-15.yaml",
        },
        acceptance_data={
            "raw_yaml": "",
            "parsed": {
                "acceptance": [
                    {"id": "AC-15-01", "description": "after report"},
                    {"id": "AC-15-02", "description": "save verdict"},
                ]
            },
        },
        master_instruction="master",
        global_rules="rules",
        roadmap_text="roadmap",
        runtime_config={
            "limits": {"max_retries": 1, "max_changed_files": 5},
            "providers": {"openai": {"model": "gpt-test", "timeout_sec": 1}},
        },
    )


def _prepared_spec(session_id: str) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "objective": "obj",
        "allowed_changes": ["orchestration/run_session.py"],
        "forbidden_changes": ["docs/sessions", "docs/acceptance"],
        "completion_criteria": [],
        "acceptance_criteria": [],
        "review_points": [],
        "implementation_notes": [],
    }


def _impl_result() -> dict[str, Any]:
    return {
        "changed_files": ["orchestration/run_session.py"],
        "implementation_summary": ["ok"],
        "patch_status": "applied",
        "risks": [],
        "open_issues": [],
        "proposed_patch": "",
    }


def _checks_all_passed() -> dict[str, Any]:
    return {
        "test": {"status": "passed"},
        "lint": {"status": "passed"},
        "typecheck": {"status": "passed"},
        "build": {"status": "passed"},
        "success": True,
    }


def _patch_main_success(monkeypatch, tmp_path, session_id: str) -> None:
    ctx = _ctx(session_id)
    monkeypatch.setattr(rs, "ARTIFACTS_DIR", tmp_path / "artifacts")
    monkeypatch.setattr(rs, "load_session_context", lambda _sid: ctx)
    monkeypatch.setattr(rs, "enforce_git_sandbox_branch", lambda _sid: None)
    monkeypatch.setattr(rs, "call_chatgpt_for_prepared_spec", lambda _c: _prepared_spec(session_id))
    monkeypatch.setattr(rs, "call_claude_for_implementation", lambda *_a, **_k: _impl_result())
    monkeypatch.setattr(
        rs,
        "_apply_patch_validate_and_run_local_checks",
        lambda **_k: _checks_all_passed(),
    )
    monkeypatch.setattr(sys, "argv", ["run_session.py", "--session-id", session_id])


def test_gpt_review_runs_after_report(monkeypatch, tmp_path):
    """AC-15-01: run_gpt_review_stage が report 保存後に呼ばれる。"""
    sid = "session-15-01"
    _patch_main_success(monkeypatch, tmp_path, sid)
    called = {"n": 0}

    def _wrapped(session_dir, report_payload):
        called["n"] += 1
        assert (session_dir / "report.json").is_file()
        assert report_payload["session_id"] == sid
        return {"session_id": sid, "verdict_status": "conditional_pass", "human_review_needed": True}

    monkeypatch.setattr(rs, "run_gpt_review_stage", _wrapped)

    assert main() == 0
    assert called["n"] == 1


def test_gpt_verdict_json_is_saved(tmp_path):
    """AC-15-02: gpt_verdict.json が保存される。"""
    session_dir = tmp_path / "artifacts" / "session-15-02"
    session_dir.mkdir(parents=True)
    report_payload = {
        "session_id": "session-15-02",
        "completion_status": "review_required",
        "checks": _checks_all_passed(),
        "acceptance_results": [{"id": "AC-15-02", "result": "passed"}],
    }
    out = run_gpt_review_stage(session_dir, report_payload)
    saved = json.loads((session_dir / "gpt_verdict.json").read_text(encoding="utf-8"))
    assert out == saved
    assert saved["session_id"] == "session-15-02"
    assert saved["human_review_needed"] is True


def test_gpt_verdict_status_enum_is_restricted(tmp_path):
    """AC-15-03: verdict_status は pass/conditional_pass/fail のみ。"""
    session_dir = tmp_path / "artifacts" / "session-15-03"
    session_dir.mkdir(parents=True)

    fail_case = run_gpt_review_stage(
        session_dir,
        {
            "session_id": "session-15-03",
            "completion_status": "failed",
            "checks": {"success": False},
            "acceptance_results": [],
        },
    )
    pass_case = run_gpt_review_stage(
        session_dir,
        {
            "session_id": "session-15-03",
            "completion_status": "passed",
            "checks": _checks_all_passed(),
            "acceptance_results": [{"id": "AC-15-03", "result": "passed"}],
        },
    )
    conditional_case = run_gpt_review_stage(
        session_dir,
        {
            "session_id": "session-15-03",
            "completion_status": "review_required",
            "checks": _checks_all_passed(),
            "acceptance_results": [{"id": "AC-15-03", "result": "not_applicable"}],
        },
    )
    allowed = {"pass", "conditional_pass", "fail"}
    assert fail_case["verdict_status"] in allowed
    assert pass_case["verdict_status"] in allowed
    assert conditional_case["verdict_status"] in allowed
    assert fail_case["verdict_status"] == "fail"
    assert pass_case["verdict_status"] == "pass"
    assert conditional_case["verdict_status"] == "conditional_pass"


def test_gpt_verdict_preserves_human_review_needed(tmp_path):
    """AC-15-04: human_review_needed は常に True。"""
    session_dir = tmp_path / "artifacts" / "session-15-04"
    session_dir.mkdir(parents=True)
    samples = [
        {"session_id": "s1", "completion_status": "failed", "checks": {"success": False}, "acceptance_results": []},
        {"session_id": "s2", "completion_status": "passed", "checks": _checks_all_passed(), "acceptance_results": [{"id": "x", "result": "passed"}]},
        {"session_id": "s3", "completion_status": "review_required", "checks": _checks_all_passed(), "acceptance_results": [{"id": "x", "result": "not_applicable"}]},
    ]
    for payload in samples:
        verdict = run_gpt_review_stage(session_dir, payload)
        assert verdict["human_review_needed"] is True


def test_existing_report_generation_is_unchanged(tmp_path):
    """AC-15-05: report.json に verdict_status が混入しない。"""
    session_dir = tmp_path / "artifacts" / "session-15-05"
    persist_session_reports(
        session_dir=session_dir,
        ctx=None,
        prepared_spec={},
        impl_result={"changed_files": [], "risks": [], "open_issues": []},
        checks={"success": True},
        status="success",
        dry_run=False,
        started_at="2026-01-01T00:00:00+00:00",
        finished_at="2026-01-01T00:00:01+00:00",
    )
    report = json.loads((session_dir / "report.json").read_text(encoding="utf-8"))
    assert "verdict_status" not in report
