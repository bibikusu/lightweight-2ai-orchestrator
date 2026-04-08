"""session-20a: 通常実行前 fail-fast 検証テスト。"""

from __future__ import annotations

from pathlib import Path

import pytest

import orchestration.run_session as rs


def _valid_session(tmp_path: Path, acceptance_path: Path) -> dict:
    return {
        "session_id": "session-20a",
        "phase_id": "phase7",
        "title": "fail-fast 実行前検証の強化",
        "goal": "通常実行前に一括検証する",
        "scope": ["run_session.py の実行前検証ロジック強化"],
        "out_of_scope": ["providers 配下の変更"],
        "constraints": ["dry-run の基本挙動を壊さない"],
        "acceptance_ref": str(acceptance_path),
        "target_repo": "LIGHTWEIGHT_2AI_ORCHESTRATOR",
        "project_root": str(tmp_path),
    }


def test_fail_fast_requires_target_repo_for_normal_run(tmp_path: Path) -> None:
    acceptance = tmp_path / "session-20a.yaml"
    acceptance.write_text("session_id: session-20a\n", encoding="utf-8")
    session = _valid_session(tmp_path, acceptance)
    session.pop("target_repo")

    with pytest.raises(ValueError, match="target_repo"):
        rs.validate_normal_run_session_inputs(session)


@pytest.mark.parametrize("project_root", [None, "", "not-found-dir"])
def test_fail_fast_requires_existing_project_root(tmp_path: Path, project_root: str | None) -> None:
    acceptance = tmp_path / "session-20a.yaml"
    acceptance.write_text("session_id: session-20a\n", encoding="utf-8")
    session = _valid_session(tmp_path, acceptance)
    session["project_root"] = project_root

    with pytest.raises(ValueError, match="project_root"):
        rs.validate_normal_run_session_inputs(session)


def test_fail_fast_requires_existing_acceptance_ref(tmp_path: Path) -> None:
    session = _valid_session(tmp_path, tmp_path / "missing.yaml")
    session["acceptance_ref"] = "   "
    with pytest.raises(ValueError, match="acceptance_ref"):
        rs.validate_normal_run_session_inputs(session)

    session["acceptance_ref"] = str(tmp_path / "missing.yaml")
    with pytest.raises(FileNotFoundError, match="acceptance file not found"):
        rs.validate_normal_run_session_inputs(session)


def test_fail_fast_reports_all_missing_required_keys_sorted() -> None:
    broken = {
        "session_id": "session-20a",
        "phase_id": "phase7",
        "title": "x",
        "goal": "x",
        "scope": [],
    }
    with pytest.raises(ValueError, match="missing required keys: acceptance_ref, constraints, out_of_scope"):
        rs.validate_session_required_keys(broken)


def test_fail_fast_rejects_mixed_projects_in_batch(tmp_path: Path) -> None:
    payload = {
        "session-a": {
            "target_repo": "LIGHTWEIGHT_2AI_ORCHESTRATOR",
            "project_root": str(tmp_path / "project-a"),
        },
        "session-b": {
            "target_repo": "A02_fina",
            "project_root": str(tmp_path / "project-b"),
        },
    }

    with pytest.raises(ValueError, match="single project"):
        rs.validate_batch_same_project(payload)


def test_fail_fast_allows_valid_session_inputs(tmp_path: Path) -> None:
    acceptance = tmp_path / "session-20a.yaml"
    acceptance.write_text("session_id: session-20a\n", encoding="utf-8")
    session = _valid_session(tmp_path, acceptance)
    rs.validate_normal_run_session_inputs(session)
