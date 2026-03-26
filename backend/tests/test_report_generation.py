# -*- coding: utf-8 -*-

import json

import pytest

from orchestration.run_session import (
    SessionContext,
    build_session_report_record,
    generate_report,
)


def test_report_contains_acceptance_status():
    """acceptanceごとの PASS/FAIL が機械向けレコードに含まれる"""
    ctx = SessionContext(
        session_id="session-04",
        session_data={"phase_id": "phase-04", "title": "t", "goal": "g"},
        acceptance_data={
            "raw_yaml": "",
            "parsed": {
                "acceptance": [
                    {"id": "AC-04-01", "test_name": "test_a"},
                    {"id": "AC-04-02", "test_name": "test_b"},
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

    report_obj = build_session_report_record(ctx, prepared_spec, impl_result, checks)

    acceptance_results = report_obj["acceptance_results"]
    assert len(acceptance_results) == 2
    assert {x["test"] for x in acceptance_results} == {"test_a", "test_b"}
    assert next(x for x in acceptance_results if x["test"] == "test_a")["result"] == "pass"
    assert next(x for x in acceptance_results if x["test"] == "test_b")["result"] == "fail"


def test_report_contains_required_fields():
    """AC-01: 機械向けレコードに必須フィールドが含まれる"""
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

    report_obj = build_session_report_record(ctx, prepared_spec, impl_result, checks)

    for key in [
        "changed_files",
        "test_result",
        "lint_result",
        "typecheck_result",
        "build_result",
        "risks",
        "open_issues",
        "diff_summary",
        "acceptance_results",
        "retry_count",
        "max_retries",
        "retry_stopped_same_cause",
        "retry_stopped_max_retries",
    ]:
        assert key in report_obj
    assert report_obj["retry_count"] == 0
    assert report_obj["retry_stopped_same_cause"] is False
    assert report_obj["retry_stopped_max_retries"] is False


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
