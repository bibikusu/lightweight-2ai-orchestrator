# -*- coding: utf-8 -*-

import pytest

from orchestration.run_session import classify_failure_type


def test_failure_type_is_single():
    """AC-02: failure_type は 1 つだけ確定する（文字列で返す）"""
    check_results = {
        "build": {"status": "passed"},
        "typecheck": {"status": "passed"},
        "lint": {"status": "passed"},
        "test": {"status": "failed"},
    }
    result = classify_failure_type(check_results)
    assert isinstance(result.get("failure_type"), str)
    assert result["failure_type"] == "test_failure"


def test_failure_type_priority_order():
    """AC-03: 固定優先順位（build > typecheck > lint > test）に従う"""
    check_results = {
        "build": {"status": "failed"},
        "typecheck": {"status": "failed"},
        "lint": {"status": "failed"},
        "test": {"status": "failed"},
    }
    result = classify_failure_type(check_results)
    assert result["failure_type"] == "build_failure"
    assert result["priority"] == 4

    check_results2 = {
        "build": {"status": "passed"},
        "typecheck": {"status": "failed"},
        "lint": {"status": "failed"},
        "test": {"status": "failed"},
    }
    result2 = classify_failure_type(check_results2)
    assert result2["failure_type"] == "typecheck_failure"
    assert result2["priority"] == 3

