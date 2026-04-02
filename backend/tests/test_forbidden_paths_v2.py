import pytest

from orchestration.run_session import (
    check_forbidden_paths,
    normalize_changed_file_path,
    validate_changed_files_before_patch,
    validate_patch_files,
)


def test_forbidden_detect():
    """FORBIDDEN_PATHS に該当するパスが検出されること。"""
    paths = ["docs/sessions/test.json", "a.py"]
    normalized = [normalize_changed_file_path(p) for p in paths]

    # check_forbidden_paths で禁止パスが検出される
    assert check_forbidden_paths(normalized) is False

    # validate_patch_files でも scope_violation になる
    result = validate_patch_files(paths)
    assert result["status"] == "error"
    assert result["error_type"] == "scope_violation"
    assert "forbidden path detected" in result["message"]


def test_no_override():
    """allowed_changes が FORBIDDEN_PATHS ルールをバイパスしないこと。"""
    impl_result = {"changed_files": ["docs/sessions/test.json"]}
    prepared_spec = {
        "allowed_changes": ["docs/sessions/test.json"],
        "forbidden_changes": [],
    }
    session_data = {"out_of_scope": []}

    with pytest.raises(ValueError, match="forbidden path detected"):
        validate_changed_files_before_patch(
            impl_result=impl_result,
            prepared_spec=prepared_spec,
            session_data=session_data,
            max_changed_files=5,
        )


def test_consistency():
    """check_forbidden_paths と validate_changed_files_before_patch の結果が一致すること。"""

    def _validate_ok(changed_files, allowed_changes):
        impl_result = {"changed_files": changed_files}
        prepared_spec = {
            "allowed_changes": allowed_changes,
            "forbidden_changes": [],
        }
        session_data = {"out_of_scope": []}
        validate_changed_files_before_patch(
            impl_result=impl_result,
            prepared_spec=prepared_spec,
            session_data=session_data,
            max_changed_files=5,
        )

    # 許可されるパス
    safe_paths = ["backend/tests/sample.py"]
    normalized_safe = [normalize_changed_file_path(p) for p in safe_paths]
    assert check_forbidden_paths(normalized_safe) is True
    _validate_ok(safe_paths, allowed_changes=[])

    # 禁止されるパス
    forbidden_paths = ["docs/acceptance/spec.md"]
    normalized_forbidden = [normalize_changed_file_path(p) for p in forbidden_paths]
    assert check_forbidden_paths(normalized_forbidden) is False
    impl_result = {"changed_files": forbidden_paths}
    prepared_spec = {
        "allowed_changes": [],
        "forbidden_changes": [],
    }
    session_data = {"out_of_scope": []}
    with pytest.raises(ValueError, match="forbidden path detected"):
        validate_changed_files_before_patch(
            impl_result=impl_result,
            prepared_spec=prepared_spec,
            session_data=session_data,
            max_changed_files=5,
        )


def test_no_regression():
    """既存の禁止パス・許可パス挙動にリグレッションがないこと。"""
    # validate_patch_files の既存挙動
    assert validate_patch_files(["a.py"])["status"] == "success"
    assert validate_patch_files(["docs/sessions/test.json"])["status"] == "error"

    # validate_changed_files_before_patch の既存の artifacts/.gitkeep 許可挙動
    impl_result = {"changed_files": ["artifacts/.gitkeep"]}
    prepared_spec = {
        "allowed_changes": ["artifacts/.gitkeep"],
        "forbidden_changes": [],
    }
    session_data = {"out_of_scope": []}

    # 例外が発生しないことを確認（互換性維持）
    validate_changed_files_before_patch(
        impl_result=impl_result,
        prepared_spec=prepared_spec,
        session_data=session_data,
        max_changed_files=5,
    )

