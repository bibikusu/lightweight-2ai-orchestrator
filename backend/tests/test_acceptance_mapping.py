# -*- coding: utf-8 -*-

import pytest

from orchestration.run_session import validate_acceptance_test_mapping


def test_acceptance_mapping_exists():
    """AC-01: acceptance 項目の test_name が利用可能なテスト関数名に存在する"""
    acceptance_items = [
        {"id": "AC-04-01", "test_name": "test_report_contains_required_fields"},
        {"id": "AC-04-02", "test_name": "test_failure_type_priority_order"},
    ]
    available = [
        "test_report_contains_required_fields",
        "test_failure_type_priority_order",
    ]

    result = validate_acceptance_test_mapping(acceptance_items, available)
    assert result["status"] == "success"
    assert result["missing_test_names"] == []


def test_acceptance_mapping_detects_missing_test_names():
    """存在しない test_name は missing として返す"""
    acceptance_items = [
        {"id": "AC-04-01", "test_name": "test_report_contains_required_fields"},
        {"id": "AC-04-02", "test_name": "test_non_existent"},
    ]
    available = ["test_report_contains_required_fields"]

    result = validate_acceptance_test_mapping(acceptance_items, available)
    assert result["status"] == "error"
    assert "test_non_existent" in result["missing_test_names"]

