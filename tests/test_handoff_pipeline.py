"""Tests for orchestration.integration.handoff_pipeline (session-193)."""

from __future__ import annotations

import json
import pathlib

import pytest
import yaml

import orchestration.integration.handoff_pipeline as pipeline_mod
from orchestration.handoff_validator import ValidationResult
from orchestration.integration import HandoffPipelineResult, build_then_validate


def _write_pipeline_fixtures(tmp_path: pathlib.Path, session_id: str) -> pathlib.Path:
    """session JSON と acceptance YAML を tmp_path 配下に作成する。"""
    docs_sessions = tmp_path / "docs" / "sessions"
    docs_acceptance = tmp_path / "docs" / "acceptance"
    docs_sessions.mkdir(parents=True, exist_ok=True)
    docs_acceptance.mkdir(parents=True, exist_ok=True)

    session_data = {
        "session_id": session_id,
        "phase_id": "phase-test",
        "title": "Test pipeline session",
        "goal": "Verify handoff pipeline",
        "scope": ["scope item"],
        "out_of_scope": ["out of scope item"],
        "constraints": ["constraint"],
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
        "title": "Test pipeline session",
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


def test_build_then_validate_pass_case(tmp_path):
    session_id = "session-pipe-01"
    _write_pipeline_fixtures(tmp_path, session_id)

    result = build_then_validate(session_id, tmp_path)

    # AC-193-01: schema_version と frozen 確認
    assert result.schema_version == "handoff_pipeline.v1"
    with pytest.raises(AttributeError):
        setattr(result, "schema_version", "other")

    # AC-193-02: 戻り値の型確認
    assert isinstance(result, HandoffPipelineResult)

    # AC-193-03: context_pack_path と validation_result を返す
    assert isinstance(result.context_pack_path, pathlib.Path)
    assert result.context_pack_path.name == "compact_context_pack.json"
    assert result.context_pack_path.exists()
    assert isinstance(result.validation_result, ValidationResult)
    assert result.validation_result.passed is True

    # AC-193-07: 統合関数は integration パッケージ内に実装
    assert hasattr(pipeline_mod, "build_then_validate")
    assert hasattr(pipeline_mod, "HandoffPipelineResult")


def test_build_then_validate_reraises_context_pack_failure(tmp_path, monkeypatch):
    # AC-193-04: context_pack 生成失敗時は validate_handoff を呼ばず例外を re-raise する
    def _fail_build(*args, **kwargs):
        raise RuntimeError("context pack failure")

    validate_called: list = []

    def _spy_validate(*args, **kwargs):
        validate_called.append(True)
        return ValidationResult(schema_version="handoff_validator.v1", passed=True)

    monkeypatch.setattr(pipeline_mod, "build_compact_context_pack", _fail_build)
    monkeypatch.setattr(pipeline_mod, "validate_handoff", _spy_validate)

    with pytest.raises(RuntimeError, match="context pack failure"):
        build_then_validate("session-pipe-fail", tmp_path)

    assert validate_called == [], "validate_handoff は呼ばれてはならない"


def test_build_then_validate_returns_validator_failure(tmp_path, monkeypatch):
    # AC-193-05: validator fail 時も context_pack_path と ValidationResult(passed=False) を返す
    session_id = "session-pipe-02"
    _write_pipeline_fixtures(tmp_path, session_id)

    fail_result = ValidationResult(
        schema_version="handoff_validator.v1",
        passed=False,
        errors=["validation error detail"],
    )
    monkeypatch.setattr(pipeline_mod, "validate_handoff", lambda *a, **kw: fail_result)

    result = build_then_validate(session_id, tmp_path)

    assert result.validation_result.passed is False
    assert result.validation_result.errors == ["validation error detail"]
    assert result.context_pack_path.exists()


def test_build_then_validate_side_effects_limited_to_context_pack(tmp_path):
    # AC-193-06 / AC-193-08: 副作用は compact_context_pack.json の出力のみ
    session_id = "session-pipe-03"
    _write_pipeline_fixtures(tmp_path, session_id)

    session_json_path = tmp_path / "docs" / "sessions" / f"{session_id}.json"
    acceptance_yaml_path = tmp_path / "docs" / "acceptance" / f"{session_id}.yaml"

    sj_before = session_json_path.read_bytes()
    ay_before = acceptance_yaml_path.read_bytes()

    result = build_then_validate(session_id, tmp_path)

    # compact_context_pack.json のみ生成される
    assert result.context_pack_path.exists()
    assert result.context_pack_path.name == "compact_context_pack.json"

    # session JSON / acceptance YAML は変更されない
    assert session_json_path.read_bytes() == sj_before
    assert acceptance_yaml_path.read_bytes() == ay_before
