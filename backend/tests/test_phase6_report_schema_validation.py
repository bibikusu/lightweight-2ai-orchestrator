# -*- coding: utf-8 -*-
"""docs/reports の Phase6 レポート JSON の構造・型検証（session-32）。

Phase5 向けの test_report_schema_validation.py / test_report_schema_extension.py と
対象・必須キーが異なるため重複しない。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# Phase6 failure pattern summary のトップレベル必須キー（現行 JSON に合わせる）
PHASE6_FAILURE_PATTERN_SUMMARY_REQUIRED_KEYS = frozenset(
    (
        "phase",
        "sessions_reviewed",
        "failure_patterns",
        "root_causes",
        "preventive_actions",
        "open_issues",
        "final_judgement",
    )
)

# Phase6 progress dashboard のトップレベル必須キー（現行 JSON に合わせる）
PHASE6_PROGRESS_DASHBOARD_REQUIRED_KEYS = frozenset(
    (
        "phase",
        "reviewed_sessions",
        "status_counts",
        "failure_type_counts",
        "open_issues_summary",
        "current_position",
        "next_actions",
        "final_judgement",
    )
)

# Phase6 completion report のトップレベル必須キー（現行 JSON に合わせる）
PHASE6_COMPLETION_REPORT_REQUIRED_KEYS = frozenset(
    (
        "phase",
        "status",
        "reviewed_sessions",
        "completion_checks",
        "evidence_summary",
        "risks",
        "open_issues",
        "final_judgement",
    )
)

FINAL_JUDGEMENT_REQUIRED_KEYS = frozenset({"result", "reason", "next_phase"})

# Phase6 完了レポートの final_judgement.result 許容値（session-32 指示）
PHASE6_COMPLETION_FINAL_JUDGEMENT_RESULT_ENUM = frozenset(
    {"completed", "conditional_completed", "not_completed"}
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_json_object(path: Path) -> dict:
    if not path.is_file():
        pytest.fail(f"レポートが見つかりません: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        pytest.fail(f"{path.name} のルートは JSON object である必要があります")
    return raw


def _load_phase6_failure_pattern_summary() -> dict:
    path = _repo_root() / "docs" / "reports" / "phase6_failure_pattern_summary.json"
    return _load_json_object(path)


def _load_phase6_progress_dashboard() -> dict:
    path = _repo_root() / "docs" / "reports" / "phase6_progress_dashboard.json"
    return _load_json_object(path)


def _load_phase6_completion_report() -> dict:
    path = _repo_root() / "docs" / "reports" / "phase6_completion_report.json"
    return _load_json_object(path)


def test_phase6_failure_pattern_summary_structure() -> None:
    """AC-32-01: phase6_failure_pattern_summary.json の必須トップレベル構造と型。"""
    data = _load_phase6_failure_pattern_summary()
    missing = PHASE6_FAILURE_PATTERN_SUMMARY_REQUIRED_KEYS - data.keys()
    assert not missing, f"不足キー: {sorted(missing)}"

    assert isinstance(data["phase"], str), "phase は str である必要があります"
    assert isinstance(data["sessions_reviewed"], list), (
        "sessions_reviewed は list である必要があります"
    )
    assert isinstance(data["failure_patterns"], list), (
        "failure_patterns は list である必要があります"
    )
    assert isinstance(data["root_causes"], list), "root_causes は list である必要があります"
    assert isinstance(data["preventive_actions"], list), (
        "preventive_actions は list である必要があります"
    )
    assert isinstance(data["open_issues"], list), "open_issues は list である必要があります"
    assert isinstance(data["final_judgement"], dict), (
        "final_judgement は object である必要があります"
    )


def test_phase6_progress_dashboard_structure() -> None:
    """AC-32-02: phase6_progress_dashboard.json の必須トップレベル構造と型。"""
    data = _load_phase6_progress_dashboard()
    missing = PHASE6_PROGRESS_DASHBOARD_REQUIRED_KEYS - data.keys()
    assert not missing, f"不足キー: {sorted(missing)}"

    assert isinstance(data["phase"], str), "phase は str である必要があります"
    assert isinstance(data["reviewed_sessions"], list), (
        "reviewed_sessions は list である必要があります"
    )
    assert isinstance(data["status_counts"], dict), (
        "status_counts は object である必要があります"
    )
    assert isinstance(data["failure_type_counts"], dict), (
        "failure_type_counts は object である必要があります"
    )
    assert isinstance(data["open_issues_summary"], dict), (
        "open_issues_summary は object である必要があります"
    )
    assert isinstance(data["current_position"], dict), (
        "current_position は object である必要があります"
    )
    assert isinstance(data["next_actions"], list), "next_actions は list である必要があります"
    assert isinstance(data["final_judgement"], dict), (
        "final_judgement は object である必要があります"
    )


def test_phase6_completion_report_structure() -> None:
    """AC-32-03: phase6_completion_report.json の必須トップレベル構造と型。"""
    data = _load_phase6_completion_report()
    missing = PHASE6_COMPLETION_REPORT_REQUIRED_KEYS - data.keys()
    assert not missing, f"不足キー: {sorted(missing)}"

    assert isinstance(data["phase"], str), "phase は str である必要があります"
    assert isinstance(data["status"], str), "status は str である必要があります"
    assert isinstance(data["reviewed_sessions"], list), (
        "reviewed_sessions は list である必要があります"
    )
    assert isinstance(data["completion_checks"], list), (
        "completion_checks は list である必要があります"
    )
    assert isinstance(data["evidence_summary"], dict), (
        "evidence_summary は object である必要があります"
    )
    assert isinstance(data["risks"], list), "risks は list である必要があります"
    assert isinstance(data["open_issues"], list), "open_issues は list である必要があります"
    assert isinstance(data["final_judgement"], dict), (
        "final_judgement は object である必要があります"
    )


def test_phase6_completion_report_final_judgement_enum() -> None:
    """AC-32-04: completion report の final_judgement に必須キーと result enum がある。"""
    data = _load_phase6_completion_report()
    fj = data["final_judgement"]
    assert isinstance(fj, dict), "final_judgement は object である必要があります"
    missing = FINAL_JUDGEMENT_REQUIRED_KEYS - fj.keys()
    assert not missing, f"final_judgement の不足キー: {sorted(missing)}"

    result = fj["result"]
    assert isinstance(result, str), "final_judgement.result は str である必要があります"
    assert result in PHASE6_COMPLETION_FINAL_JUDGEMENT_RESULT_ENUM, (
        f"final_judgement.result={result!r} は許容されません"
        f"（許容: {sorted(PHASE6_COMPLETION_FINAL_JUDGEMENT_RESULT_ENUM)}）"
    )
    assert isinstance(fj["reason"], str), "final_judgement.reason は str である必要があります"
    assert isinstance(fj["next_phase"], str), (
        "final_judgement.next_phase は str である必要があります"
    )


def test_phase6_progress_dashboard_next_actions_is_list() -> None:
    """AC-32-05: progress dashboard の next_actions が list である。"""
    data = _load_phase6_progress_dashboard()
    na = data["next_actions"]
    assert isinstance(na, list), "next_actions は list である必要があります"
