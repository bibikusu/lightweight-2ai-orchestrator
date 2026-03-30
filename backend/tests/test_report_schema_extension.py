# -*- coding: utf-8 -*-
"""docs/reports/phase5_completion_report.json の未カバー構造検証（session-31）。

session-27（test_report_schema_validation.py）で既に検証している項目は含めない。
"""

from backend.tests.report_json_test_helpers import (
    assert_required_keys,
    load_json_object,
    repo_root,
)

# phase5 レポートの consistency_check に期待するキー（現行 JSON に合わせる）
CONSISTENCY_CHECK_REQUIRED_KEYS = frozenset(
    (
        "config_alignment",
        "docs_alignment",
        "report_schema_integrity",
        "ci_alignment",
    )
)


def _load_phase5_completion_report() -> dict:
    """レポート JSON を読み込む（リポジトリルート基準）。"""
    path = repo_root() / "docs" / "reports" / "phase5_completion_report.json"
    return load_json_object(
        path,
        missing_file_message=f"phase5 レポートが見つかりません: {path}",
        root_not_dict_message="phase5 レポートのルートは JSON object である必要があります",
    )


def test_completed_sessions_is_list_of_strings() -> None:
    """AC-31-01: completed_sessions は str のリストである。"""
    data = _load_phase5_completion_report()
    cs = data.get("completed_sessions")
    assert isinstance(cs, list), "completed_sessions は list である必要があります"
    for i, item in enumerate(cs):
        assert isinstance(item, str), (
            f"completed_sessions[{i}] は str である必要があります（実際は {type(item).__name__}）"
        )


def test_risks_is_list() -> None:
    """AC-31-02: risks は list である。"""
    data = _load_phase5_completion_report()
    risks = data.get("risks")
    assert isinstance(risks, list), "risks は list である必要があります"


def test_open_issues_is_list() -> None:
    """AC-31-03: open_issues は list である。"""
    data = _load_phase5_completion_report()
    oi = data.get("open_issues")
    assert isinstance(oi, list), "open_issues は list である必要があります"


def test_consistency_check_has_required_keys() -> None:
    """AC-31-04: consistency_check は dict で必須キーを持つ。"""
    data = _load_phase5_completion_report()
    cc = data.get("consistency_check")
    assert isinstance(cc, dict), "consistency_check は object である必要があります"
    assert_required_keys(cc, CONSISTENCY_CHECK_REQUIRED_KEYS, label="consistency_check")
