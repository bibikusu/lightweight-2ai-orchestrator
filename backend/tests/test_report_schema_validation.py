# -*- coding: utf-8 -*-
"""docs/reports/phase5_completion_report.json の構造・必須キー検証（session-27）。"""

from backend.tests.report_json_test_helpers import (
    assert_required_keys,
    load_json_object,
    repo_root,
)

# 実在する phase5_completion_report.json のトップレベルキー集合（仕様の正本）
REQUIRED_TOP_LEVEL_KEYS = frozenset(
    (
        "capabilities",
        "completed_sessions",
        "consistency_check",
        "final_judgement",
        "open_issues",
        "phase",
        "risks",
        "status",
        "test_results",
    )
)

# Phase5 完了レポートの status 許容値（session 指示どおり）
PHASE5_STATUS_ENUM = frozenset(
    {"completed", "conditional_completed", "not_completed"}
)

TEST_RESULTS_REQUIRED_KEYS = frozenset({"pytest", "ruff", "mypy", "build"})

FINAL_JUDGEMENT_REQUIRED_KEYS = frozenset({"result", "reason", "next_phase"})


def _load_phase5_completion_report() -> dict:
    """レポート JSON を読み込む（パスはリポジトリルート基準）。"""
    path = repo_root() / "docs" / "reports" / "phase5_completion_report.json"
    return load_json_object(
        path,
        missing_file_message=f"phase5 レポートが見つかりません: {path}",
        root_not_dict_message="phase5 レポートのルートは JSON でなければなりません",
    )


def test_report_has_required_top_level_keys() -> None:
    """AC-27-01: 必須トップレベルキーがすべて存在する。"""
    data = _load_phase5_completion_report()
    assert_required_keys(data, REQUIRED_TOP_LEVEL_KEYS)


def test_report_capabilities_all_boolean() -> None:
    """AC-27-02: capabilities は object かつ値がすべて bool。"""
    data = _load_phase5_completion_report()
    caps = data.get("capabilities")
    assert isinstance(caps, dict), "capabilities は object である必要があります"
    for key, val in caps.items():
        assert isinstance(
            val, bool
        ), f"capabilities[{key!r}] は bool である必要があります（実際は {type(val).__name__}）"


def test_report_status_enum_valid() -> None:
    """AC-27-03: status が enum 定義内である。"""
    data = _load_phase5_completion_report()
    status = data.get("status")
    assert isinstance(status, str), "status は文字列である必要があります"
    assert status in PHASE5_STATUS_ENUM, (
        f"status={status!r} は許容されません（許容: {sorted(PHASE5_STATUS_ENUM)}）"
    )


def test_report_test_results_keys_exist() -> None:
    """AC-27-04: test_results に pytest / ruff / mypy / build が存在する。"""
    data = _load_phase5_completion_report()
    tr = data.get("test_results")
    assert isinstance(tr, dict), "test_results は object である必要があります"
    assert_required_keys(tr, TEST_RESULTS_REQUIRED_KEYS, label="test_results")


def test_report_final_judgement_structure() -> None:
    """AC-27-05: final_judgement が result / reason / next_phase を持つ。"""
    data = _load_phase5_completion_report()
    fj = data.get("final_judgement")
    assert isinstance(fj, dict), "final_judgement は object である必要があります"
    assert_required_keys(fj, FINAL_JUDGEMENT_REQUIRED_KEYS, label="final_judgement")
