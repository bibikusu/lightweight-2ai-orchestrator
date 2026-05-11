"""Tests for orchestration.context_pack (session-191)."""

import json
import pathlib

import yaml

from orchestration.context_pack import build_compact_context_pack, write_compact_context_pack


def _write_session_fixtures(tmp_path: pathlib.Path, session_id: str) -> pathlib.Path:
    """Write minimal session JSON and acceptance YAML under tmp_path docs/."""
    docs_sessions = tmp_path / "docs" / "sessions"
    docs_acceptance = tmp_path / "docs" / "acceptance"
    docs_sessions.mkdir(parents=True, exist_ok=True)
    docs_acceptance.mkdir(parents=True, exist_ok=True)

    session_data = {
        "session_id": session_id,
        "phase_id": "phase-test",
        "title": "Test session",
        "goal": "Verify context pack builder",
        "scope": ["scope item 1"],
        "out_of_scope": ["out of scope item 1"],
        "constraints": ["constraint 1"],
        "allowed_changes_detail": ["docs/sessions/test.json: test"],
        "forbidden_changes": ["do not touch X"],
        "review_points": ["仕様一致（AC達成）", "変更範囲遵守", "副作用なし", "検証十分性"],
        "failure_type": "test_failure",
        "acceptance_ref": f"docs/acceptance/{session_id}.yaml",
        "completion_criteria": [
            {"id": f"CC-{session_id}-01", "type": "artifact", "condition": "artifact exists"}
        ],
        "acceptance_criteria": [
            {"id": f"AC-{session_id}-01", "description": "artifact check", "test_name": "test_artifact"}
        ],
    }
    (docs_sessions / f"{session_id}.json").write_text(
        json.dumps(session_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    acceptance_data = {
        "session_id": session_id,
        "phase_id": "phase-test",
        "title": "Test session",
        "acceptance": [
            {
                "id": f"AC-{session_id}-01",
                "description": "artifact check",
                "test_name": "test_artifact",
                "type": "manual",
                "manual_check": True,
                "completion_criteria_refs": [f"CC-{session_id}-01"],
                "verification": ["check artifact exists"],
            }
        ],
    }
    (docs_acceptance / f"{session_id}.yaml").write_text(
        yaml.safe_dump(acceptance_data, allow_unicode=True), encoding="utf-8"
    )
    return tmp_path


def test_build_normal_case(tmp_path):
    session_id = "session-test-01"
    repo_root = _write_session_fixtures(tmp_path, session_id)

    pack = build_compact_context_pack(session_id, repo_root)

    assert pack["schema_version"] == "compact_context_pack.v1"

    # session_summary 11 キー欠落なし
    expected_keys = [
        "session_id", "phase_id", "title", "goal", "scope", "out_of_scope",
        "constraints", "allowed_changes_detail", "forbidden_changes",
        "review_points", "failure_type",
    ]
    for key in expected_keys:
        assert key in pack["session_summary"], f"session_summary missing key: {key}"

    assert "acceptance_count" in pack["acceptance_summary"]
    assert "items" in pack["acceptance_summary"]
    assert "completion_count" in pack["completion_summary"]
    assert "items" in pack["completion_summary"]

    output_dir = repo_root / "artifacts" / session_id / "context"
    out_path = write_compact_context_pack(pack, output_dir)
    expected_path = repo_root / "artifacts" / session_id / "context" / "compact_context_pack.json"
    assert out_path == expected_path
    assert out_path.exists()


def test_build_with_missing_reports(tmp_path):
    session_id = "session-test-02"
    repo_root = _write_session_fixtures(tmp_path, session_id)
    # reports ディレクトリは作成しない

    pack = build_compact_context_pack(session_id, repo_root)

    assert pack["reports_summary"]["found"] is False
    assert any(f"reports missing for {session_id}" in w for w in pack["warnings"])


def test_build_rejects_out_of_scope_fields(tmp_path):
    session_id = "session-test-03"
    repo_root = _write_session_fixtures(tmp_path, session_id)

    pack = build_compact_context_pack(session_id, repo_root)

    forbidden = {"dependency_graph", "judge_result", "dependencies", "ready"}
    for key in forbidden:
        assert key not in pack, f"out-of-scope field found in pack: {key}"


def test_build_is_deterministic(tmp_path):
    session_id = "session-test-04"
    repo_root = _write_session_fixtures(tmp_path, session_id)

    pack1 = build_compact_context_pack(session_id, repo_root)
    pack2 = build_compact_context_pack(session_id, repo_root)

    serialized1 = json.dumps(pack1, ensure_ascii=False, sort_keys=False, indent=2)
    serialized2 = json.dumps(pack2, ensure_ascii=False, sort_keys=False, indent=2)
    assert serialized1 == serialized2
