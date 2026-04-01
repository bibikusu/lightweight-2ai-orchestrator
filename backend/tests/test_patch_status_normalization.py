"""patch_status 正規化のテスト。

_PATCH_STATUS_ALIASES に定義された非正規値が validate_impl_result 呼び出し後に
正規値へ書き換わることを確認する。
"""

from orchestration.run_session import validate_impl_result


def _make_impl_result(patch_status: str) -> dict:
    """テスト用の最小有効 impl_result を生成する。"""
    return {
        "session_id": "test-session-001",
        "changed_files": [],
        "implementation_summary": "テスト用サマリー",
        "proposed_patch": "",
        "patch_status": patch_status,
    }


def test_patch_status_normalized():
    """no_patch_required は validate_impl_result 後に not_applicable へ変換される。"""
    result = _make_impl_result("no_patch_required")
    validate_impl_result(result)
    assert result["patch_status"] == "not_applicable"


def test_invalid_patch_status_safe():
    """未知の patch_status でも ValueError にならない（warning のみ）。"""
    result = _make_impl_result("unknown_value")
    # 例外が発生しないことを確認
    validate_impl_result(result)
    # 未知の値はそのまま残る（not_applicable への変換はされない）
    assert result["patch_status"] == "unknown_value"


def test_existing_patch_status_unchanged():
    """正規値（applied/partial/not_applicable/dry_run）はそのまま維持される。"""
    for status in ("applied", "partial", "not_applicable", "dry_run"):
        result = _make_impl_result(status)
        validate_impl_result(result)
        assert result["patch_status"] == status, f"{status} が変換されてしまった"
