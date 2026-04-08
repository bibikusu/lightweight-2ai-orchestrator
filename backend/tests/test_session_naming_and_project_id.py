# -*- coding: utf-8 -*-
"""session-22: session_id 命名規則と project_id 必須化の検証。"""

from __future__ import annotations

import pytest

from orchestration.run_session import (
    resolve_project_config_for_session,
    validate_batch_session_project_consistency,
    validate_session_required_keys,
)


def _registry_stub() -> dict:
    return {
        "version": 1,
        "projects": {
            "lightweight_2ai_orchestrator": {
                "project_id": "lightweight_2ai_orchestrator",
                "target_repo": ".",
                "project_root": ".",
                "docs_root": ".",
                "artifact_namespace": "lightweight_2ai_orchestrator",
            },
            "a01_card_task": {
                "project_id": "a01_card_task",
                "target_repo": ".",
                "project_root": ".",
                "docs_root": ".",
                "artifact_namespace": "a01_card_task",
            },
        },
    }


def _new_session_minimal(session_id: str) -> dict:
    return {
        "session_id": session_id,
        "phase_id": "phase7",
        "title": "session-22 test",
        "goal": "validate naming",
        "scope": ["validation"],
        "out_of_scope": ["none"],
        "constraints": ["fail-fast"],
        "acceptance_ref": "docs/acceptance/session-22.yaml",
    }


def test_new_session_requires_project_id() -> None:
    data = _new_session_minimal("lightweight_2ai_orchestrator-session-22")
    with pytest.raises(ValueError, match="project_id"):
        validate_session_required_keys(data, legacy_map={"session_to_project": {}})


def test_session_id_requires_project_prefix() -> None:
    data = _new_session_minimal("session-22")
    data["project_id"] = "lightweight_2ai_orchestrator"
    with pytest.raises(ValueError, match="session_id 命名規則違反"):
        resolve_project_config_for_session(
            session_id=data["session_id"],
            session_data=data,
            registry=_registry_stub(),
            legacy_map={"session_to_project": {}},
        )


def test_session_prefix_must_match_project_id() -> None:
    data = _new_session_minimal("a01_card_task-session-22")
    data["project_id"] = "lightweight_2ai_orchestrator"
    with pytest.raises(ValueError, match="prefix と project_id が不一致"):
        resolve_project_config_for_session(
            session_id=data["session_id"],
            session_data=data,
            registry=_registry_stub(),
            legacy_map={"session_to_project": {}},
        )


def test_batch_rejects_mixed_prefix_or_project_id() -> None:
    session_items = [
        (
            "lightweight_2ai_orchestrator-session-22",
            {"project_id": "lightweight_2ai_orchestrator"},
        ),
        (
            "a01_card_task-session-22",
            {"project_id": "a01_card_task"},
        ),
    ]
    with pytest.raises(ValueError, match="project_id が混在"):
        validate_batch_session_project_consistency(
            session_items,
            legacy_map={"session_to_project": {}},
        )


def test_legacy_mapping_only_applies_to_legacy_sessions() -> None:
    registry = _registry_stub()
    legacy_map = {
        "session_to_project": {
            "session-20a": "lightweight_2ai_orchestrator",
        }
    }

    legacy_data = _new_session_minimal("session-20a")
    resolved = resolve_project_config_for_session(
        session_id="session-20a",
        session_data=legacy_data,
        registry=registry,
        legacy_map=legacy_map,
    )
    assert resolved["project_id"] == "lightweight_2ai_orchestrator"

    new_data = _new_session_minimal("lightweight_2ai_orchestrator-session-22")
    with pytest.raises(ValueError, match="new session では project_id が必須"):
        resolve_project_config_for_session(
            session_id=new_data["session_id"],
            session_data=new_data,
            registry=registry,
            legacy_map=legacy_map,
        )
