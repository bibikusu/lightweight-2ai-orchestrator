# -*- coding: utf-8 -*-
"""session-23: session spec 品質固定の fail-fast テスト。"""

from __future__ import annotations

import pytest

from orchestration.run_session import validate_session_spec_quality


def _base_session() -> dict:
    return {
        "session_id": "session-23",
        "phase_id": "phase7",
        "project_id": "lightweight_2ai_orchestrator",
        "title": "spec 品質固定",
        "goal": "実行前 fail-fast",
        "type": "code",
        "scope": ["validation"],
        "out_of_scope": ["none"],
        "constraints": ["fail-fast"],
        "acceptance_ref": "docs/acceptance/session-23.yaml",
        "review_points": [
            "仕様一致（AC達成）",
            "変更範囲遵守",
            "副作用なし（既存破壊なし）",
            "検証十分性",
        ],
        "acceptance_criteria": [
            {
                "id": "AC-23-01",
                "description": "review_points の第4軸が検証十分性であること",
                "test_name": "test_review_points_fourth_axis_must_be_verification_sufficiency",
            }
        ],
        "completion_criteria": [
            {
                "id": "CC-23-01",
                "type": "state_transition_consistent",
                "condition": "spec 品質を実行前検証",
            },
            {
                "id": "CC-23-02",
                "type": "artifact",
                "condition": "差戻し可能なエラーを返す",
            },
        ],
    }


def test_review_points_fourth_axis_must_be_verification_sufficiency() -> None:
    data = _base_session()
    data["review_points"] = ["a", "b", "c", "d"]
    with pytest.raises(ValueError, match="第4軸"):
        validate_session_spec_quality(data)


def test_completion_criteria_requires_id_type_condition() -> None:
    data = _base_session()
    data["completion_criteria"] = [{"id": "CC-23-X", "type": "artifact"}]
    with pytest.raises(ValueError, match="condition"):
        validate_session_spec_quality(data)


def test_completion_criteria_type_must_be_allowed_enum() -> None:
    data = _base_session()
    data["completion_criteria"] = [
        {"id": "CC-23-X", "type": "unsupported_type", "condition": "x"},
        {"id": "CC-23-Y", "type": "artifact", "condition": "y"},
    ]
    with pytest.raises(ValueError, match="許可値外"):
        validate_session_spec_quality(data)


def test_code_session_acceptance_requires_test_name() -> None:
    data = _base_session()
    data["acceptance_criteria"] = [{"id": "AC-23-X", "description": "x"}]
    with pytest.raises(ValueError, match="test_name"):
        validate_session_spec_quality(data)


def test_docs_only_session_uses_docs_only_completion_rule() -> None:
    data = _base_session()
    data["type"] = "docs-only"
    data["acceptance_criteria"] = [{"id": "AC-23-X", "description": "x"}]
    data["completion_criteria"] = [
        {
            "id": "CC-23-X",
            "type": "state_transition_consistent",
            "condition": "x",
        }
    ]
    with pytest.raises(ValueError, match="document_rule"):
        validate_session_spec_quality(data)

    data["completion_criteria"] = [
        {
            "id": "CC-23-X",
            "type": "document_rule",
            "condition": "docs-only の整合性",
        }
    ]
    validate_session_spec_quality(data)


def test_session_spec_requires_non_empty_acceptance_and_completion() -> None:
    data = _base_session()
    data["acceptance_criteria"] = []
    with pytest.raises(ValueError, match="acceptance_criteria"):
        validate_session_spec_quality(data)

    data = _base_session()
    data["completion_criteria"] = []
    with pytest.raises(ValueError, match="completion_criteria"):
        validate_session_spec_quality(data)
