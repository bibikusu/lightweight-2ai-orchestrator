# -*- coding: utf-8 -*-

from orchestration.run_session import (
    build_failure_record_for_report,
    resolve_canonical_failure_type,
)


def test_indentation_error_is_classified_as_generated_artifact_invalid() -> None:
    """AC-66-01: IndentationError は generated_artifact_invalid になる。"""
    checks = {
        "test": {
            "status": "failed",
            "stderr": "E   IndentationError: unexpected indent",
            "stdout": "",
        },
        "lint": {"status": "skipped"},
        "typecheck": {"status": "skipped"},
        "build": {"status": "skipped"},
        "success": False,
    }
    out = resolve_canonical_failure_type(checks)
    assert out["failure_type"] == "generated_artifact_invalid"


def test_syntax_error_family_is_not_misclassified_as_test_failure() -> None:
    """AC-66-02: SyntaxError 系は test_failure へ誤分類されない。"""
    checks = {
        "test": {
            "status": "failed",
            "stderr": "E   TabError: inconsistent use of tabs and spaces in indentation",
            "stdout": "",
        },
        "lint": {"status": "passed"},
        "typecheck": {"status": "passed"},
        "build": {"status": "passed"},
        "success": False,
    }
    out = resolve_canonical_failure_type(checks)
    assert out["failure_type"] == "generated_artifact_invalid"


def test_report_payload_keeps_failure_type_and_failure_metadata_for_generated_artifact_invalid() -> None:
    """AC-66-03: report 用 failure_type と failure metadata が同時に残る。"""
    checks = {
        "test": {
            "status": "failed",
            "stderr": "E   IndentationError: unindent does not match any outer indentation level",
            "stdout": "",
        },
        "lint": {"status": "passed"},
        "typecheck": {"status": "passed"},
        "build": {"status": "passed"},
        "success": False,
    }
    canonical = resolve_canonical_failure_type(checks)
    failure = build_failure_record_for_report(
        checks,
        "failed",
        error_message=None,
        aborted_stage=None,
    )
    assert canonical["failure_type"] == "generated_artifact_invalid"
    assert failure["failure_type"] == "generated_artifact_invalid"
    assert failure["failure_layer"] == "generated_artifact"
    assert failure["stop_stage"] == "checks"
    assert isinstance(failure["cause_summary"], str)
    assert failure["cause_summary"] != ""


def test_existing_failure_classification_behavior_remains_unchanged() -> None:
    """AC-66-04: SyntaxError 系以外の分類挙動を壊さない。"""
    checks = {
        "test": {
            "status": "failed",
            "stderr": "E   ModuleNotFoundError: No module named 'example_missing_module'",
            "stdout": "",
        },
        "lint": {"status": "passed"},
        "typecheck": {"status": "passed"},
        "build": {"status": "passed"},
        "success": False,
    }
    out = resolve_canonical_failure_type(checks)
    assert out["failure_type"] == "import_error"
