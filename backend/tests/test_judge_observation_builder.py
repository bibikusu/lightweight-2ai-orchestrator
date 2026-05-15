# -*- coding: utf-8 -*-
"""
judge_observation_builder のテスト。

docs/contracts/judge_observation_contract.md の acceptance criteria に対応。
session-201 / docs/acceptance/session-201.yaml との AST 照合は test_name で紐付ける。
"""

import json
import os
from typing import Any, Dict

import pytest

from orchestration.judge.observation_builder import build_judge_observation

# テスト用の最小合法 worker_report（worker_report_contract.md Section 3 準拠）
_VALID_REPORT: Dict[str, Any] = {
    "session_id": "session-test-001",
    "acceptance_ref": "docs/acceptance/session-test-001.yaml",
    "status_proposal": "pass_proposed",
    "changed_files": ["orchestration/judge/observation_builder.py"],
    "verification_summary": "All acceptance criteria satisfied.",
    "evidence_refs": ["docs/sessions/session-test-001.json"],
    "blocker_summary": None,
}

# pcc_display_contract.md Section 6 の宣言順
_PCC_FIELD_ORDER = [
    "current_session",
    "next_action",
    "blocker",
    "waiting_human",
    "queue_status",
    "recent_failures",
    "dependency_state",
    "judge_state",
]

# judge_observation_contract.md Section 3 が定める 5 フィールド
_OBS_REQUIRED_FIELDS = {
    "worker_report_ref",
    "judge_recommendation_ref",
    "observation_metadata",
    "pcc_display_fields",
    "final_decision_boundary",
}

# 戻り値・保存 JSON に含めてはならないフィールド名
_FORBIDDEN_FIELDS = {"decision", "verdict", "judgement", "go_hold_fail"}


# ---------------------------------------------------------------------------
# AC-201-01: observation artifact は 5 フィールドのみを持つ
# ---------------------------------------------------------------------------
def test_judge_observation_has_exactly_5_keys(tmp_path: Any) -> None:
    out = str(tmp_path / "obs.json")
    result = build_judge_observation(_VALID_REPORT, out)
    assert set(result.keys()) == _OBS_REQUIRED_FIELDS


# ---------------------------------------------------------------------------
# AC-201-02: final_decision_boundary は "commander_only" 固定
# ---------------------------------------------------------------------------
def test_judge_observation_final_decision_boundary_is_commander_only(tmp_path: Any) -> None:
    out = str(tmp_path / "obs.json")
    result = build_judge_observation(_VALID_REPORT, out)
    assert result["final_decision_boundary"] == "commander_only"


# ---------------------------------------------------------------------------
# AC-201-03: 禁止フィールドを含まない
# ---------------------------------------------------------------------------
def test_judge_observation_no_forbidden_fields(tmp_path: Any) -> None:
    out = str(tmp_path / "obs.json")
    result = build_judge_observation(_VALID_REPORT, out)
    assert not (_FORBIDDEN_FIELDS & set(result.keys()))


# ---------------------------------------------------------------------------
# AC-201-04: worker_report が dict でない場合 ValueError
# ---------------------------------------------------------------------------
def test_judge_observation_raises_on_non_dict_input(tmp_path: Any) -> None:
    out = str(tmp_path / "obs.json")
    with pytest.raises(ValueError):
        build_judge_observation("not_a_dict", out)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# AC-201-05: 必須キー欠落の場合 ValueError
# ---------------------------------------------------------------------------
def test_judge_observation_raises_on_missing_required_keys(tmp_path: Any) -> None:
    out = str(tmp_path / "obs.json")
    incomplete: Dict[str, Any] = {"session_id": "session-x"}
    with pytest.raises(ValueError):
        build_judge_observation(incomplete, out)


# ---------------------------------------------------------------------------
# AC-201-06: output_path に有効な JSON が保存される
# ---------------------------------------------------------------------------
def test_judge_observation_output_is_valid_json(tmp_path: Any) -> None:
    out = str(tmp_path / "obs.json")
    build_judge_observation(_VALID_REPORT, out)
    with open(out, encoding="utf-8") as fh:
        loaded = json.load(fh)
    assert isinstance(loaded, dict)
    assert set(loaded.keys()) == _OBS_REQUIRED_FIELDS


# ---------------------------------------------------------------------------
# AC-201-07: pcc_display_fields が Section 6 の宣言順 8 スロットを持つ
# ---------------------------------------------------------------------------
def test_judge_observation_pcc_display_fields_has_8_slots(tmp_path: Any) -> None:
    out = str(tmp_path / "obs.json")
    result = build_judge_observation(_VALID_REPORT, out)
    assert list(result["pcc_display_fields"].keys()) == _PCC_FIELD_ORDER


# ---------------------------------------------------------------------------
# AC-201-08: docs/sessions/session-201.json が存在し 14 キーを持つ
# ---------------------------------------------------------------------------
def test_session_201_json_has_all_14_keys() -> None:
    path = "docs/sessions/session-201.json"
    assert os.path.exists(path), f"{path} が存在しない"
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    required = {
        "session_id", "phase_id", "title", "goal", "scope", "out_of_scope",
        "constraints", "acceptance_ref", "allowed_changes_detail",
        "forbidden_changes", "completion_criteria", "acceptance_criteria",
        "review_points", "failure_type",
    }
    missing = required - d.keys()
    assert not missing, f"不足キー: {sorted(missing)}"


# ---------------------------------------------------------------------------
# AC-201-09: docs/acceptance/session-201.yaml の session_id が一致する
# ---------------------------------------------------------------------------
def test_session_201_yaml_session_id_matches() -> None:
    import yaml  # type: ignore[import]

    path = "docs/acceptance/session-201.yaml"
    assert os.path.exists(path), f"{path} が存在しない"
    with open(path, encoding="utf-8") as fh:
        d = yaml.safe_load(fh)
    assert d.get("session_id") == "session-201", (
        f"session_id 不一致: {d.get('session_id')!r}"
    )
