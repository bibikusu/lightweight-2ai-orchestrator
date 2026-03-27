# -*- coding: utf-8 -*-

import json

import pytest

from orchestration.run_session import (
    SessionContext,
    build_acceptance_results_for_report_json,
    build_session_report_record,
    decide_completion_status,
    generate_report,
    persist_session_reports,
)


def _assert_required_report_keys(obj: dict) -> None:
    for k in (
        "session_id",
        "status",
        "dry_run",
        "started_at",
        "finished_at",
        "changed_files",
        "checks",
        "failure_type",
        "error_message",
    ):
        assert k in obj


def test_report_json_is_generated_on_dry_run(monkeypatch, tmp_path):
    """AC-B4R1-03/04: dry-run でも artifacts/<sid>/report.json が生成され required_keys を満たす"""
    import orchestration.run_session as rs
    import sys

    sid = "session-01"
    monkeypatch.setattr(rs, "ARTIFACTS_DIR", tmp_path / "artifacts")
    monkeypatch.setattr(sys, "argv", ["run_session.py", "--dry-run", "--session-id", sid])
    assert rs.main() == 0

    p = tmp_path / "artifacts" / sid / "report.json"
    assert p.is_file()
    obj = json.loads(p.read_text(encoding="utf-8"))
    _assert_required_report_keys(obj)
    assert obj["status"] == "dry_run"
    assert obj["dry_run"] is True


def test_report_json_is_generated_on_success(monkeypatch, tmp_path):
    """AC-B4R1-01/04: 成功時に report.json が生成され required_keys を満たす"""
    import orchestration.run_session as rs
    import sys

    sid = "session-report-success"
    ctx = rs.SessionContext(
        session_id=sid,
        session_data={
            "session_id": sid,
            "phase_id": "p",
            "title": "t",
            "goal": "g",
            "scope": [],
            "out_of_scope": [],
            "constraints": [],
            "acceptance_ref": "acceptance/session-01.yaml",
        },
        acceptance_data={"raw_yaml": "", "parsed": {"acceptance": []}},
        master_instruction="",
        global_rules="",
        roadmap_text="",
        runtime_config={
            "limits": {"max_retries": 1, "max_changed_files": 5},
            "providers": {"openai": {"model": "gpt-test", "timeout_sec": 1}},
        },
    )

    monkeypatch.setattr(rs, "ARTIFACTS_DIR", tmp_path / "artifacts")
    monkeypatch.setattr(rs, "load_session_context", lambda _sid: ctx)
    monkeypatch.setattr(rs, "enforce_git_sandbox_branch", lambda _sid: None)
    monkeypatch.setattr(
        rs, "call_chatgpt_for_prepared_spec", lambda _c: {"objective": "obj", "forbidden_changes": []}
    )
    monkeypatch.setattr(
        rs,
        "call_claude_for_implementation",
        lambda _ps, _c, _ri=None: {
            "changed_files": ["orchestration/run_session.py"],
            "implementation_summary": [],
            "risks": [],
            "open_issues": [],
            "proposed_patch": "",
        },
    )
    monkeypatch.setattr(
        rs,
        "run_local_checks",
        lambda _c, **_: {
            "test": {"status": "passed"},
            "lint": {"status": "skipped"},
            "typecheck": {"status": "skipped"},
            "build": {"status": "skipped"},
            "success": True,
        },
    )

    monkeypatch.setattr(sys, "argv", ["run_session.py", "--session-id", sid])
    assert rs.main() == 0

    p = tmp_path / "artifacts" / sid / "report.json"
    assert p.is_file()
    obj = json.loads(p.read_text(encoding="utf-8"))
    _assert_required_report_keys(obj)
    assert obj["status"] == "success"
    assert obj["dry_run"] is False
    assert isinstance(obj["changed_files"], list)


def test_report_json_is_generated_on_failure(monkeypatch, tmp_path):
    """AC-B4R1-02/04: 失敗時にも report.json が生成され status=failed になる"""
    import orchestration.run_session as rs
    import sys

    sid = "session-report-fail"
    ctx = rs.SessionContext(
        session_id=sid,
        session_data={
            "session_id": sid,
            "phase_id": "p",
            "title": "t",
            "goal": "g",
            "scope": [],
            "out_of_scope": [],
            "constraints": [],
            "acceptance_ref": "acceptance/session-01.yaml",
        },
        acceptance_data={"raw_yaml": "", "parsed": {"acceptance": []}},
        master_instruction="",
        global_rules="",
        roadmap_text="",
        runtime_config={
            "limits": {"max_retries": 1, "max_changed_files": 5},
            "providers": {"openai": {"model": "gpt-test", "timeout_sec": 1}},
        },
    )

    monkeypatch.setattr(rs, "ARTIFACTS_DIR", tmp_path / "artifacts")
    monkeypatch.setattr(rs, "load_session_context", lambda _sid: ctx)
    monkeypatch.setattr(rs, "enforce_git_sandbox_branch", lambda _sid: None)
    monkeypatch.setattr(
        rs, "call_chatgpt_for_prepared_spec", lambda _c: {"objective": "obj", "forbidden_changes": []}
    )
    monkeypatch.setattr(
        rs,
        "call_claude_for_implementation",
        lambda _ps, _c, _ri=None: {
            "changed_files": ["orchestration/run_session.py"],
            "implementation_summary": [],
            "risks": [],
            "open_issues": [],
            "proposed_patch": "",
        },
    )
    monkeypatch.setattr(
        rs,
        "run_local_checks",
        lambda _c, **_: {
            "test": {"status": "failed", "command": "pytest", "returncode": 1, "stderr": "E", "stdout": ""},
            "lint": {"status": "skipped"},
            "typecheck": {"status": "skipped"},
            "build": {"status": "skipped"},
            "success": False,
        },
    )

    monkeypatch.setattr(sys, "argv", ["run_session.py", "--session-id", sid])
    assert rs.main() == 1

    p = tmp_path / "artifacts" / sid / "report.json"
    assert p.is_file()
    obj = json.loads(p.read_text(encoding="utf-8"))
    _assert_required_report_keys(obj)
    assert obj["status"] == "failed"
    assert obj["dry_run"] is False

def test_acceptance_results_auto_judged():
    """AC-13-01: acceptance_results が test_name と実行結果で passed/failed 判定される"""
    ctx = SessionContext(
        session_id="session-04",
        session_data={"phase_id": "phase-04", "title": "t", "goal": "g"},
        acceptance_data={
            "raw_yaml": "",
            "parsed": {
                "acceptance": [
                    {"id": "AC-04-01", "description": "a", "test_name": "test_a"},
                    {"id": "AC-04-02", "description": "b", "test_name": "test_b"},
                ]
            },
        },
        master_instruction="",
        global_rules="",
        roadmap_text="",
        runtime_config={},
    )

    prepared_spec = {"objective": "obj"}
    impl_result = {
        "changed_files": ["orchestration/run_session.py"],
        "implementation_summary": ["ok"],
        "risks": ["r1"],
        "open_issues": ["i1"],
        "diff_summary": "changed_files: 1 files",
    }
    checks = {
        "test": {"status": "passed"},
        "lint": {"status": "passed"},
        "typecheck": {"status": "passed"},
        "build": {"status": "passed"},
        "success": True,
        "test_function_results": {"test_a": True, "test_b": False},
    }

    report_obj = build_session_report_record(
        ctx,
        prepared_spec,
        impl_result,
        checks,
        status="success",
        completion="review_required",
    )

    acceptance_results = report_obj["acceptance_results"]
    assert len(acceptance_results) == 2
    assert {x["test"] for x in acceptance_results} == {"test_a", "test_b"}
    assert next(x for x in acceptance_results if x["test"] == "test_a")["result"] == "passed"
    assert next(x for x in acceptance_results if x["test"] == "test_b")["result"] == "failed"
    assert next(x for x in acceptance_results if x["test"] == "test_a")["description"] == "a"
    assert next(x for x in acceptance_results if x["test"] == "test_b")["description"] == "b"

    normalized = build_acceptance_results_for_report_json(ctx, checks)
    assert normalized == [
        {"id": "AC-04-01", "result": "passed"},
        {"id": "AC-04-02", "result": "failed"},
    ]


def test_acceptance_not_applicable_only_when_unmapped():
    """AC-13-02: not_applicable は未実行または未対応 test_name のみ"""
    ctx = SessionContext(
        session_id="session-04",
        session_data={"phase_id": "phase-04", "title": "t", "goal": "g"},
        acceptance_data={
            "raw_yaml": "",
            "parsed": {
                "acceptance": [
                    {"id": "AC-04-01", "test_name": "test_mapped_pass"},
                    {"id": "AC-04-02", "test_name": "test_mapped_fail"},
                    {"id": "AC-04-03", "test_name": "test_unmapped"},
                    {"id": "AC-04-04"},
                ]
            },
        },
        master_instruction="",
        global_rules="",
        roadmap_text="",
        runtime_config={},
    )
    checks = {
        "test_function_results": {
            "test_mapped_pass": True,
            "test_mapped_fail": False,
        }
    }

    normalized = build_acceptance_results_for_report_json(ctx, checks)
    assert normalized == [
        {"id": "AC-04-01", "result": "passed"},
        {"id": "AC-04-02", "result": "failed"},
        {"id": "AC-04-03", "result": "not_applicable"},
        {"id": "AC-04-04", "result": "not_applicable"},
    ]


def test_session_report_contains_required_fields():
    """AC-09-01: session_report.json に必須キーがすべて存在する"""
    ctx = SessionContext(
        session_id="session-04",
        session_data={"phase_id": "phase-04", "title": "t", "goal": "g"},
        acceptance_data={"raw_yaml": "", "parsed": {"acceptance": []}},
        master_instruction="",
        global_rules="",
        roadmap_text="",
        runtime_config={},
    )
    prepared_spec = {"objective": "obj"}
    impl_result = {
        "changed_files": [],
        "implementation_summary": ["ok"],
        "risks": [],
        "open_issues": [],
        "diff_summary": "changed_files: none",
    }
    checks = {
        "test": {"status": "passed"},
        "lint": {"status": "passed"},
        "typecheck": {"status": "skipped"},
        "build": {"status": "passed"},
        "success": True,
    }

    report_obj = build_session_report_record(
        ctx,
        prepared_spec,
        impl_result,
        checks,
        status="success",
        completion="review_required",
    )

    for key in [
        "session_id",
        "status",
        "completion",
        "changed_files",
        "test_result",
        "lint_result",
        "typecheck_result",
        "build_result",
        "acceptance_results",
        "risks",
        "open_issues",
        "diff_summary",
    ]:
        assert key in report_obj
    assert report_obj["status"] == "success"
    assert report_obj["completion"] == "review_required"
    assert report_obj["diff_summary"] != ""


def test_session_report_contains_check_results_as_strings():
    """AC-09-02: check 結果が文字列へ正規化される"""
    ctx = SessionContext(
        session_id="session-04",
        session_data={"phase_id": "phase-04", "title": "t", "goal": "g"},
        acceptance_data={"raw_yaml": "", "parsed": {"acceptance": []}},
        master_instruction="",
        global_rules="",
        roadmap_text="",
        runtime_config={},
    )
    report_obj = build_session_report_record(
        ctx,
        {"objective": "obj"},
        {"changed_files": [], "risks": [], "open_issues": []},
        {
            "test": {"status": "passed"},
            "lint": {"status": "failed"},
            "typecheck": {"status": "skipped"},
            "build": {"status": None},
            "success": False,
        },
        status="failed",
        completion="retry_required",
    )
    assert isinstance(report_obj["test_result"], str)
    assert isinstance(report_obj["lint_result"], str)
    assert isinstance(report_obj["typecheck_result"], str)
    assert isinstance(report_obj["build_result"], str)
    assert report_obj["test_result"] == "pass"
    assert report_obj["lint_result"] == "fail"


def test_report_file_extension_matches_content():
    """AC-02: .md は Markdown、.json は JSON として解釈できる（拡張子と内容が一致）"""
    ctx = SessionContext(
        session_id="session-04",
        session_data={"phase_id": "phase-04", "title": "t", "goal": "g"},
        acceptance_data={"raw_yaml": "", "parsed": {"acceptance": []}},
        master_instruction="",
        global_rules="",
        roadmap_text="",
        runtime_config={},
    )
    prepared_spec = {"objective": "obj"}
    impl_result = {
        "changed_files": ["x.py"],
        "implementation_summary": ["ok"],
        "risks": [],
        "open_issues": [],
        "diff_summary": "changed_files: 1 files",
    }
    checks = {
        "test": {"status": "passed"},
        "lint": {"status": "passed"},
        "typecheck": {"status": "passed"},
        "build": {"status": "passed"},
        "success": True,
    }

    md = generate_report(ctx, prepared_spec, impl_result, checks)
    assert md.startswith("# Session Report:")
    with pytest.raises(json.JSONDecodeError):
        json.loads(md)

    rec = build_session_report_record(ctx, prepared_spec, impl_result, checks)
    dumped = json.dumps(rec, ensure_ascii=False)
    roundtrip = json.loads(dumped)
    assert roundtrip["session_id"] == "session-04"


def test_existing_report_consumption_not_broken():
    """AC-04: generate_report は従来どおり Markdown を返し、主要フィールドが読める"""
    ctx = SessionContext(
        session_id="session-04",
        session_data={"phase_id": "phase-04", "title": "t", "goal": "g"},
        acceptance_data={"raw_yaml": "", "parsed": {"acceptance": []}},
        master_instruction="",
        global_rules="",
        roadmap_text="",
        runtime_config={},
    )
    prepared_spec = {"objective": "obj"}
    impl_result = {
        "changed_files": ["a"],
        "implementation_summary": ["ok"],
        "risks": [],
        "open_issues": [],
        "diff_summary": "changed_files: 1 files",
    }
    checks = {
        "test": {"status": "failed"},
        "lint": {"status": "passed"},
        "typecheck": {"status": "passed"},
        "build": {"status": "passed"},
        "success": False,
    }

    report_md = generate_report(ctx, prepared_spec, impl_result, checks)
    assert report_md.startswith("# Session Report:")
    assert "Changed Files" in report_md
    assert "- a" in report_md
    assert "Test: failed" in report_md

    record = build_session_report_record(ctx, prepared_spec, impl_result, checks)
    assert record["changed_files"] == ["a"]
    assert record["test_result"] == "fail"


def test_decide_completion_status_failed_status_is_prioritized():
    """status=failed の場合は acceptance/risk 状態より優先して failed にする"""
    out = decide_completion_status(
        "failed",
        acceptance_results=[],
        risks=[],
        open_issues=[],
    )
    assert out["completion_status"] == "failed"
    assert out["human_review_needed"] is False


def test_report_json_contains_risks_and_open_issues(tmp_path):
    """report.json に risks/open_issues が常に含まれる"""
    session_dir = tmp_path / "artifacts" / "session-keys"
    checks = {"success": True}
    impl_result = {
        "changed_files": [],
        "risks": ["r1"],
        "open_issues": ["i1"],
    }
    persist_session_reports(
        session_dir=session_dir,
        ctx=None,
        prepared_spec={},
        impl_result=impl_result,
        checks=checks,
        status="success",
        dry_run=False,
        started_at="2026-01-01T00:00:00+00:00",
        finished_at="2026-01-01T00:00:01+00:00",
    )
    report = json.loads((session_dir / "report.json").read_text(encoding="utf-8"))
    assert report["risks"] == ["r1"]
    assert report["open_issues"] == ["i1"]
