# -*- coding: utf-8 -*-
"""session-21: project registry 解決と legacy 制約の単体テスト。"""

from __future__ import annotations

from pathlib import Path

import pytest

from orchestration.run_session import (
    ensure_artifact_dirs,
    resolve_project_config_for_session,
)


def _registry_with_existing_paths(tmp_path: Path) -> dict:
    target_repo = tmp_path / "repo"
    project_root = tmp_path / "project"
    docs_root = project_root / "docs"
    target_repo.mkdir(parents=True, exist_ok=True)
    docs_root.mkdir(parents=True, exist_ok=True)
    return {
        "version": 1,
        "projects": {
            "lightweight_2ai_orchestrator": {
                "project_id": "lightweight_2ai_orchestrator",
                "target_repo": str(target_repo),
                "project_root": str(project_root),
                "docs_root": str(docs_root),
                "artifact_namespace": "lightweight_2ai_orchestrator",
            }
        },
    }


def test_registry_rejects_unknown_project_id(tmp_path: Path) -> None:
    registry = _registry_with_existing_paths(tmp_path)
    legacy_map = {"version": 1, "session_to_project": {}}
    with pytest.raises(ValueError, match="未登録"):
        resolve_project_config_for_session(
            session_id="session-21",
            session_data={"project_id": "unknown_project"},
            registry=registry,
            legacy_map=legacy_map,
        )


def test_registry_resolves_target_repo_from_project_id(tmp_path: Path) -> None:
    registry = _registry_with_existing_paths(tmp_path)
    legacy_map = {"version": 1, "session_to_project": {}}
    resolved = resolve_project_config_for_session(
        session_id="session-21",
        session_data={"project_id": "lightweight_2ai_orchestrator"},
        registry=registry,
        legacy_map=legacy_map,
    )
    assert resolved["target_repo"] == (tmp_path / "repo").resolve()


def test_registry_resolves_existing_project_root_from_project_id(tmp_path: Path) -> None:
    registry = _registry_with_existing_paths(tmp_path)
    legacy_map = {"version": 1, "session_to_project": {}}
    resolved = resolve_project_config_for_session(
        session_id="session-21",
        session_data={"project_id": "lightweight_2ai_orchestrator"},
        registry=registry,
        legacy_map=legacy_map,
    )
    assert resolved["project_root"] == (tmp_path / "project").resolve()
    assert resolved["project_root"].exists()


def test_registry_resolves_existing_docs_root_from_project_id(tmp_path: Path) -> None:
    registry = _registry_with_existing_paths(tmp_path)
    legacy_map = {"version": 1, "session_to_project": {}}
    resolved = resolve_project_config_for_session(
        session_id="session-21",
        session_data={"project_id": "lightweight_2ai_orchestrator"},
        registry=registry,
        legacy_map=legacy_map,
    )
    assert resolved["docs_root"] == (tmp_path / "project" / "docs").resolve()
    assert resolved["docs_root"].exists()


def test_registry_namespaces_artifacts_by_project_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("orchestration.run_session.ARTIFACTS_DIR", tmp_path / "artifacts")
    session_dir = ensure_artifact_dirs("session-21", "lightweight_2ai_orchestrator")
    assert session_dir == tmp_path / "artifacts" / "lightweight_2ai_orchestrator" / "session-21"
    assert (session_dir / "reports").is_dir()


def test_legacy_session_requires_explicit_project_mapping(tmp_path: Path) -> None:
    registry = _registry_with_existing_paths(tmp_path)
    legacy_map = {
        "version": 1,
        "session_to_project": {"session-12": "lightweight_2ai_orchestrator"},
    }
    resolved = resolve_project_config_for_session(
        session_id="session-12",
        session_data={},
        registry=registry,
        legacy_map=legacy_map,
    )
    assert resolved["project_id"] == "lightweight_2ai_orchestrator"

    with pytest.raises(ValueError, match="明示マッピング"):
        resolve_project_config_for_session(
            session_id="session-999",
            session_data={},
            registry=registry,
            legacy_map=legacy_map,
        )
