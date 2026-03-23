# -*- coding: utf-8 -*-

import pytest

from orchestration.run_session import validate_patch_files


def test_patch_validation_within_limit():
    """AC-02-01: 5件以内で成功"""
    changed_files = ["a.py", "b.py", "c.py"]
    result = validate_patch_files(changed_files)
    assert result["status"] == "success"


def test_patch_validation_over_limit():
    """AC-02-02: 6件以上で失敗"""
    changed_files = ["a.py", "b.py", "c.py", "d.py", "e.py", "f.py"]
    result = validate_patch_files(changed_files)
    assert result["status"] == "error"
    assert result["error_type"] == "scope_violation"


def test_patch_validation_forbidden_paths():
    """AC-02-03: 禁止パスで失敗"""
    changed_files = ["docs/sessions/test.json"]
    result = validate_patch_files(changed_files)
    assert result["status"] == "error"
    assert result["error_type"] == "scope_violation"
