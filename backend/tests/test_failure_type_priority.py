# -*- coding: utf-8 -*-
"""block3-retry-02: resolve_canonical_failure_type の正本7値と優先順位の検証。"""

from orchestration.run_session import (
    normalize_check_results_for_retry,
    resolve_canonical_failure_type,
)


def test_canonical_priority_build_over_test():
    """build_error(1) が test_failure(4) より優先される。"""
    cr = {
        "build": {"status": "failed", "command": "make", "returncode": 2, "stderr": "b", "stdout": ""},
        "test": {"status": "failed", "command": "pytest", "returncode": 1, "stderr": "t", "stdout": ""},
        "lint": {"status": "skipped"},
        "typecheck": {"status": "skipped"},
        "success": False,
    }
    out = resolve_canonical_failure_type(cr)
    assert out["failure_type"] == "build_error"
    assert out["priority"] == 1


def test_canonical_import_error_over_plain_test():
    """import_error(2) が通常の test_failure(4) より優先される。"""
    cr = {
        "test": {
            "status": "failed",
            "command": "pytest",
            "returncode": 1,
            "stderr": "ModuleNotFoundError: no module named 'x'",
            "stdout": "",
        },
        "lint": {"status": "skipped"},
        "typecheck": {"status": "skipped"},
        "build": {"status": "skipped"},
        "success": False,
    }
    out = resolve_canonical_failure_type(cr)
    assert out["failure_type"] == "import_error"
    assert out["priority"] == 2


def test_canonical_type_mismatch_from_typecheck():
    """typecheck 失敗は type_mismatch(3)。"""
    cr = {
        "typecheck": {"status": "failed", "command": "mypy", "returncode": 1, "stderr": "err", "stdout": ""},
        "test": {"status": "skipped"},
        "lint": {"status": "skipped"},
        "build": {"status": "skipped"},
        "success": False,
    }
    out = resolve_canonical_failure_type(cr)
    assert out["failure_type"] == "type_mismatch"
    assert out["priority"] == 3


def test_canonical_scope_and_regression_flags():
    """複数フラグ時は優先番号最小（scope_violation=5）が選ばれる。"""
    cr = {
        "test": {"status": "passed", "command": "t", "returncode": 0, "stderr": "", "stdout": ""},
        "lint": {"status": "passed", "command": "l", "returncode": 0, "stderr": "", "stdout": ""},
        "typecheck": {"status": "passed", "command": "tc", "returncode": 0, "stderr": "", "stdout": ""},
        "build": {"status": "passed", "command": "b", "returncode": 0, "stderr": "", "stdout": ""},
        "success": True,
        "scope_violation": True,
        "regression_detected": True,
        "spec_missing_detected": True,
    }
    out = resolve_canonical_failure_type(cr)
    assert out["failure_type"] == "scope_violation"
    assert out["priority"] == 5


def test_canonical_spec_missing_when_only_lowest_flags():
    """spec_missing のみ True のとき spec_missing(7)。"""
    cr = {
        "test": {"status": "passed", "command": "t", "returncode": 0, "stderr": "", "stdout": ""},
        "lint": {"status": "passed", "command": "l", "returncode": 0, "stderr": "", "stdout": ""},
        "typecheck": {"status": "passed", "command": "tc", "returncode": 0, "stderr": "", "stdout": ""},
        "build": {"status": "passed", "command": "b", "returncode": 0, "stderr": "", "stdout": ""},
        "success": True,
        "scope_violation": False,
        "regression_detected": False,
        "spec_missing_detected": True,
    }
    out = resolve_canonical_failure_type(cr)
    assert out["failure_type"] == "spec_missing"
    assert out["priority"] == 7


def test_success_checks_imply_no_failure_canonical():
    """検証成功時は resolve が no_failure（main 側で retry 生成に入らない）。"""
    cr = {
        "test": {"status": "passed", "command": "t", "returncode": 0, "stderr": "", "stdout": ""},
        "lint": {"status": "skipped"},
        "typecheck": {"status": "skipped"},
        "build": {"status": "skipped"},
        "success": True,
    }
    out = resolve_canonical_failure_type(cr)
    assert out["failure_type"] == "no_failure"
    assert out["priority"] == 0


def test_resolve_canonical_failure_type_prefers_spec_missing_for_missing_json():
    """AC-118-01: JSON 欠損メッセージは test_failure に落とさず spec_missing。"""
    checks = {
        "test": {"status": "failed", "stderr": "Error: JSON file not found: /x/y.json", "stdout": ""},
        "lint": {"status": "skipped"},
        "typecheck": {"status": "skipped"},
        "build": {"status": "skipped"},
        "success": False,
    }
    out = resolve_canonical_failure_type(
        checks, error_message="JSON file not found: specs/foo.json", stop_stage="loading"
    )
    assert out["failure_type"] == "spec_missing"


def test_resolve_canonical_failure_type_prefers_scope_violation_for_forbidden_path():
    """AC-118-02: 禁止パス検出は test_failure ではなく scope_violation。"""
    checks = {
        "test": {"status": "failed", "stderr": "forbidden path detected: ../../etc/passwd", "stdout": ""},
        "lint": {"status": "skipped"},
        "typecheck": {"status": "skipped"},
        "build": {"status": "skipped"},
        "success": False,
    }
    out = resolve_canonical_failure_type(checks)
    assert out["failure_type"] == "scope_violation"


def test_resolve_canonical_failure_type_prefers_regression_for_init_preflight_duplicate():
    """AC-118-03: init 段の preflight 重複定義は regression。"""
    msg = (
        "[CODE_STATE_PREFLIGHT] duplicate top-level function definitions "
        "in run_session.py: foo. Fix duplicate definitions before continuing"
    )
    checks = {"success": False}
    out = resolve_canonical_failure_type(checks, error_message=msg, stop_stage="init")
    assert out["failure_type"] == "regression"


def test_resolve_canonical_failure_type_keeps_real_test_failures_as_test_failure():
    """AC-118-04: 実際の pytest / import 失敗は test_failure のまま。"""
    assert (
        resolve_canonical_failure_type(
            {
                "test": {
                    "status": "failed",
                    "stderr": "AssertionError: expected 1 got 2",
                    "stdout": "",
                },
                "lint": {"status": "skipped"},
                "typecheck": {"status": "skipped"},
                "build": {"status": "skipped"},
                "success": False,
            }
        )["failure_type"]
        == "test_failure"
    )
    assert (
        resolve_canonical_failure_type(
            {
                "test": {
                    "status": "failed",
                    "stderr": "ModuleNotFoundError: no module named 'missing_pkg'",
                    "stdout": "",
                },
                "lint": {"status": "skipped"},
                "typecheck": {"status": "skipped"},
                "build": {"status": "skipped"},
                "success": False,
            }
        )["failure_type"]
        == "import_error"
    )


def test_normalize_fills_missing_optional_fields():
    """未存在の checks フィールドは normalize でデフォルト化される。"""
    cr = {"test": {"status": "failed"}, "success": False}
    n = normalize_check_results_for_retry(cr)
    assert n.get("scope_violation") is False
    assert n.get("regression_detected") is False
    assert n.get("spec_missing_detected") is False
    assert n.get("error_messages") == []
