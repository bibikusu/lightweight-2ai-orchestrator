# -*- coding: utf-8 -*-
"""AC-73: Claude 実装応答ガードの回帰テスト。"""

import logging
import inspect
import pytest

from orchestration.run_session import validate_impl_result


# 必須キーを含む最小の有効な impl_result
_VALID_BASE = {
    "session_id": "session-test",
    "changed_files": ["a.py"],
    "implementation_summary": "summary",
    "patch_status": "applied",
    "proposed_patch": "diff --git ...",
}


def test_impl_result_missing_required_key_stops_before_patch():
    """blocking 必須キー（changed_files / implementation_summary / proposed_patch）欠落 → ValueError。
    session_id / patch_status 欠落は warning のみで ValueError にならない。"""
    blocking_keys = [
        "changed_files",
        "implementation_summary",
        "proposed_patch",
    ]
    for missing_key in blocking_keys:
        incomplete = {k: v for k, v in _VALID_BASE.items() if k != missing_key}
        with pytest.raises(ValueError, match=missing_key):
            validate_impl_result(incomplete)

    # session_id / patch_status 欠落は ValueError にならない
    for warning_only_key in ("session_id", "patch_status"):
        without_key = {k: v for k, v in _VALID_BASE.items() if k != warning_only_key}
        validate_impl_result(without_key)  # raise されないこと


def test_validate_impl_result_called_only_from_main_flow():
    """validate_impl_result が main() 内でのみ呼ばれることを確認する。"""
    import orchestration.run_session as m

    source = inspect.getsource(m)

    # validate_impl_result の呼び出し箇所が main() 内に存在すること
    # main() の定義以降に2回呼ばれていることを確認
    main_start = source.find("\ndef main(")
    assert main_start != -1, "main() が見つからない"

    main_body = source[main_start:]
    call_count = main_body.count("validate_impl_result(")
    assert call_count >= 2, (
        f"validate_impl_result が main() 内で {call_count} 回しか呼ばれていない（2回以上必要）"
    )

    # main() の外では呼ばれていないこと
    # "def validate_impl_result(" は定義行なので除外し、
    # 実際の呼び出し "validate_impl_result(" のみをカウントする
    before_main = source[:main_start]
    calls_before_main = before_main.count("validate_impl_result(") - before_main.count(
        "def validate_impl_result("
    )
    assert calls_before_main == 0, (
        f"validate_impl_result が main() 外で {calls_before_main} 回呼ばれている"
    )


def test_impl_result_with_required_keys_does_not_hard_fail_on_noncritical_type_mismatch():
    """必須キーがすべて存在し patch_status が有効値なら、
    changed_files が list[int] でも ValueError にならない。"""
    result = {
        "session_id": "session-test",
        "changed_files": [1, 2, 3],  # int のリスト（型不整合だが warning のみ）
        "implementation_summary": "summary",
        "patch_status": "applied",
        "proposed_patch": "diff --git ...",
    }
    # ValueError が raise されないことを確認
    validate_impl_result(result)


def test_impl_result_noncritical_type_issue_is_warning_only(caplog):
    """型不整合時に warning ログが出力されることを確認する。"""
    result_bad_changed_files = {
        "session_id": "session-test",
        "changed_files": "not_a_list",  # list でない
        "implementation_summary": "summary",
        "patch_status": "applied",
        "proposed_patch": "diff --git ...",
    }
    with caplog.at_level(logging.WARNING, logger="orchestration.run_session"):
        validate_impl_result(result_bad_changed_files)

    assert any(
        "changed_files" in record.message and record.levelname == "WARNING"
        for record in caplog.records
    ), "changed_files 型不整合で WARNING ログが出ていない"

    caplog.clear()

    result_bad_summary = {
        "session_id": "session-test",
        "changed_files": ["a.py"],
        "implementation_summary": 42,  # list でも str でもない
        "patch_status": "applied",
        "proposed_patch": "diff --git ...",
    }
    with caplog.at_level(logging.WARNING, logger="orchestration.run_session"):
        validate_impl_result(result_bad_summary)

    assert any(
        "implementation_summary" in record.message and record.levelname == "WARNING"
        for record in caplog.records
    ), "implementation_summary 型不整合で WARNING ログが出ていない"
