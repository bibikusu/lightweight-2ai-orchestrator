from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from backend.tests.report_json_test_helpers import load_report_json


REPORT_PATHS: dict[str, str] = {
    "phase5_completion_report": "docs/reports/phase5_completion_report.json",
    "phase6_failure_pattern_summary": "docs/reports/phase6_failure_pattern_summary.json",
    "phase6_progress_dashboard": "docs/reports/phase6_progress_dashboard.json",
    "phase6_completion_report": "docs/reports/phase6_completion_report.json",
}


def _load_all_reports() -> dict[str, dict[str, Any]]:
    """docs/reports 配下の対象レポートをすべて読み込む。"""
    return {name: load_report_json(path) for name, path in REPORT_PATHS.items()}


def test_all_reports_are_json_objects() -> None:
    """AC-36-01: すべての対象レポートが JSON object として読み込める。"""
    reports = _load_all_reports()

    assert reports, "対象レポートが 1 件も見つかりません"

    for name, data in reports.items():
        assert isinstance(
            data, Mapping
        ), f"{name} は JSON object（dict）として読み込まれる必要があります"


def test_all_reports_have_final_judgement_structure() -> None:
    """AC-36-02: final_judgement が共通の構造（result/reason/next_phase）を持つ。"""
    reports = _load_all_reports()
    required_keys = {"result", "reason", "next_phase"}

    key_sets: dict[str, set[str]] = {}

    for name, data in reports.items():
        assert "final_judgement" in data, (
            f"{name} に final_judgement が存在しません（横断仕様と不整合）"
        )
        final_judgement = data["final_judgement"]
        assert isinstance(
            final_judgement, Mapping
        ), f"{name}.final_judgement は object である必要があります"

        keys = set(final_judgement.keys())
        key_sets[name] = keys

        missing = required_keys - keys
        assert not missing, (
            f"{name}.final_judgement に必須キー {sorted(required_keys)} が不足しています: "
            f"{sorted(missing)}"
        )

    # final_judgement のキー構造がすべてのレポートで揃っていることを確認する
    all_key_sets = list(key_sets.values())
    assert all_key_sets, "final_judgement を持つレポートが 1 件も見つかりません"

    first = all_key_sets[0]
    for name, keys in key_sets.items():
        assert (
            keys == first
        ), f"{name}.final_judgement のキー集合 {sorted(keys)} が他のレポートと不一致です"


def test_all_reports_have_required_top_level_keys() -> None:
    """AC-36-03（構造観点）: 共通のトップレベルキー構造が維持されている。"""
    reports = _load_all_reports()

    # 4 レポートに共通して存在すべき最小集合のみを見る（既存単体テストと重複しないようにする）
    minimally_required = {"phase", "final_judgement"}

    for name, data in reports.items():
        keys = set(data.keys())
        missing = minimally_required - keys
        assert not missing, (
            f"{name} に共通必須トップレベルキー {sorted(minimally_required)} が不足しています: "
            f"{sorted(missing)}"
        )

    # すべてのレポートで共通しているキー集合が不自然に乖離していないことも確認する
    key_sets = [set(data.keys()) for data in reports.values()]
    common_keys = set.intersection(*key_sets)
    assert minimally_required <= common_keys, (
        "対象レポート間の共通トップレベルキー集合が最小要件を満たしていません"
    )


def test_reports_status_enum_valid() -> None:
    """AC-36-03: status を持つレポートの enum 一貫性を検証する。"""
    reports = _load_all_reports()
    allowed_status = {"completed", "conditional_completed", "not_completed"}

    seen_status_values: set[str] = set()

    for name, data in reports.items():
        if "status" not in data:
            continue
        status = data["status"]
        assert isinstance(status, str), f"{name}.status は str である必要があります"
        assert status in allowed_status, (
            f"{name}.status={status!r} は許容されません "
            f"(許容値: {sorted(allowed_status)})"
        )
        seen_status_values.add(status)

    assert seen_status_values, "status フィールドを持つレポートが少なくとも 1 件必要です"


def test_reports_next_phase_consistency() -> None:
    """AC-36-04: final_judgement.next_phase の naming consistency を緩やかに検証する。"""
    reports = _load_all_reports()

    next_phases: dict[str, str] = {}
    for name, data in reports.items():
        if "final_judgement" not in data:
            continue
        fj = data["final_judgement"]
        if not isinstance(fj, Mapping) or "next_phase" not in fj:
            continue
        next_phase = fj["next_phase"]
        assert isinstance(
            next_phase, str
        ), f"{name}.final_judgement.next_phase は str である必要があります"

        value = next_phase.strip()
        assert value, (
            f"{name}.final_judgement.next_phase は空文字列ではいけません"
        )
        # 長さや前後の空白など、極端に不自然な値になっていないことだけを確認する
        assert (
            len(value) <= 64
        ), f"{name}.final_judgement.next_phase が不自然に長すぎます (len={len(value)})"
        assert value == next_phase, (
            f"{name}.final_judgement.next_phase に前後の不要な空白があります: {next_phase!r}"
        )

        next_phases[name] = value

    assert (
        next_phases
    ), "final_judgement.next_phase を持つレポートが少なくとも 1 件必要です"

