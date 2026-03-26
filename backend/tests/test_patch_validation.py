# -*- coding: utf-8 -*-

import pytest

from orchestration.run_session import (
    validate_changed_files_before_patch,
    validate_patch_files,
)


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


def test_patch_validation_allows_explicitly_allowed_artifacts_path():
    """allowed_changes で明示許可された artifacts パスは通過"""
    impl_result = {"changed_files": ["artifacts/.gitkeep"]}
    prepared_spec = {"allowed_changes": ["artifacts/.gitkeep"], "forbidden_changes": []}
    session_data = {"out_of_scope": []}

    validate_changed_files_before_patch(
        impl_result=impl_result,
        prepared_spec=prepared_spec,
        session_data=session_data,
        max_changed_files=5,
    )


def test_patch_validation_blocks_artifacts_path_without_explicit_allow():
    """allowed_changes に無い artifacts パスは拒否"""
    impl_result = {"changed_files": ["artifacts/not-allowed.txt"]}
    prepared_spec = {"allowed_changes": [], "forbidden_changes": []}
    session_data = {"out_of_scope": []}

    with pytest.raises(ValueError, match="forbidden path detected"):
        validate_changed_files_before_patch(
            impl_result=impl_result,
            prepared_spec=prepared_spec,
            session_data=session_data,
            max_changed_files=5,
        )
