"""Tests for orchestration.handoff_validator (session-192)."""

from __future__ import annotations

import json
import pathlib
from typing import Optional

import pytest
import yaml

from orchestration.handoff_validator import validate_handoff


def _make_context_pack(session_id: str, extra: Optional[dict] = None) -> dict:
    pack = {
        "schema_version": "compact_context_pack.v1",
        "source_session_id": session_id,
        "session_summary": {"session_id": session_id},
        "acceptance_summary": {"acceptance_count": 1, "items": []},
        "completion_summary": {"completion_count": 1, "items": []},
        "reports_summary": {"found": False, "items": []},
        "inputs": {"session_json_path": f"docs/sessions/{session_id}.json"},
        "handoff_ready": True,
        "warnings": [],
    }
    if extra:
        pack.update(extra)
    return pack


def _make_session_json(session_id: str) -> dict:
    return {
        "session_id": session_id,
        "completion_criteria": [
            {"id": f"CC-{session_id}-01", "type": "artifact", "condition": "exists"}
        ],
    }


def _make_acceptance_yaml(session_id: str) -> dict:
    return {
        "session_id": session_id,
        "acceptance": [
            {
                "id": f"AC-{session_id}-01",
                "description": "check",
                "test_name": "test_check",
                "type": "manual",
                "manual_check": True,
                "completion_criteria_refs": [f"CC-{session_id}-01"],
                "verification": ["verify"],
            }
        ],
    }


def _write_fixtures(
    tmp_path: pathlib.Path,
    session_id: str,
    context_pack: Optional[dict] = None,
    session_json: Optional[dict] = None,
    acceptance_yaml: Optional[dict] = None,
) -> tuple:
    cp = context_pack if context_pack is not None else _make_context_pack(session_id)
    sj = session_json if session_json is not None else _make_session_json(session_id)
    ay = acceptance_yaml if acceptance_yaml is not None else _make_acceptance_yaml(session_id)

    cp_path = tmp_path / "compact_context_pack.json"
    sj_path = tmp_path / "session.json"
    ay_path = tmp_path / "acceptance.yaml"

    cp_path.write_text(json.dumps(cp, ensure_ascii=False, indent=2), encoding="utf-8")
    sj_path.write_text(json.dumps(sj, ensure_ascii=False, indent=2), encoding="utf-8")
    ay_path.write_text(yaml.safe_dump(ay, allow_unicode=True), encoding="utf-8")

    return cp_path, sj_path, ay_path


def test_validate_pass_case(tmp_path):
    session_id = "session-test-pass"
    cp_path, sj_path, ay_path = _write_fixtures(tmp_path, session_id)

    cp_before = cp_path.read_bytes()
    sj_before = sj_path.read_bytes()
    ay_before = ay_path.read_bytes()

    result = validate_handoff(cp_path, sj_path, ay_path)

    assert result.schema_version == "handoff_validator.v1"
    assert result.passed is True
    assert result.errors == []
    assert result.warnings == []

    # frozen=True: setattr must raise FrozenInstanceError (subclass of AttributeError)
    with pytest.raises((AttributeError,)):
        setattr(result, "passed", False)

    # read-only: input files unchanged after validation
    assert cp_path.read_bytes() == cp_before
    assert sj_path.read_bytes() == sj_before
    assert ay_path.read_bytes() == ay_before

    # warnings 透過確認
    cp_with_warn = _make_context_pack(session_id, extra={"warnings": ["warn from 191"]})
    cp_warn_path = tmp_path / "cp_warn.json"
    cp_warn_path.write_text(json.dumps(cp_with_warn, ensure_ascii=False), encoding="utf-8")
    result2 = validate_handoff(cp_warn_path, sj_path, ay_path)
    assert result2.warnings == ["warn from 191"]
    assert result2.passed is True


def test_validate_fails_on_missing_required_key(tmp_path):
    session_id = "session-test-missing"
    cp = _make_context_pack(session_id)
    del cp["source_session_id"]

    cp_path, sj_path, ay_path = _write_fixtures(tmp_path, session_id, context_pack=cp)
    result = validate_handoff(cp_path, sj_path, ay_path)

    assert result.passed is False
    assert any("source_session_id" in e for e in result.errors)


def test_validate_fails_on_ac_cc_bidirectional_mismatch(tmp_path):
    session_id = "session-test-accc"

    # sub-case (a): AC references non-existent CC
    ay_bad = {
        "session_id": session_id,
        "acceptance": [
            {
                "id": f"AC-{session_id}-01",
                "description": "check",
                "test_name": "test_check",
                "type": "manual",
                "manual_check": True,
                "completion_criteria_refs": ["CC-999-99"],  # 存在しない CC
                "verification": ["verify"],
            }
        ],
    }
    cp_path, sj_path, ay_path = _write_fixtures(tmp_path, session_id, acceptance_yaml=ay_bad)
    result = validate_handoff(cp_path, sj_path, ay_path)
    assert result.passed is False
    assert any("CC-999-99" in e for e in result.errors)

    # sub-case (b): CC is orphan (referenced by no AC)
    sj_orphan = {
        "session_id": session_id,
        "completion_criteria": [
            {"id": f"CC-{session_id}-01", "type": "artifact", "condition": "exists"},
            {"id": f"CC-{session_id}-99", "type": "artifact", "condition": "orphan"},  # orphan
        ],
    }
    ay_normal = _make_acceptance_yaml(session_id)
    cp_path2 = tmp_path / "cp2.json"
    sj_path2 = tmp_path / "sj2.json"
    ay_path2 = tmp_path / "ay2.yaml"
    cp_path2.write_text(json.dumps(_make_context_pack(session_id), ensure_ascii=False), encoding="utf-8")
    sj_path2.write_text(json.dumps(sj_orphan, ensure_ascii=False), encoding="utf-8")
    ay_path2.write_text(yaml.safe_dump(ay_normal, allow_unicode=True), encoding="utf-8")
    result2 = validate_handoff(cp_path2, sj_path2, ay_path2)
    assert result2.passed is False
    assert any(f"CC-{session_id}-99" in e for e in result2.errors)


def test_validate_fails_on_scope_invasion(tmp_path):
    session_id = "session-test-scope"

    for forbidden_key in ("dependency_graph", "judge_result", "dependencies"):
        cp = _make_context_pack(session_id, extra={forbidden_key: {}})
        cp_path = tmp_path / f"cp_{forbidden_key}.json"
        sj_path = tmp_path / f"sj_{forbidden_key}.json"
        ay_path = tmp_path / f"ay_{forbidden_key}.yaml"
        cp_path.write_text(json.dumps(cp, ensure_ascii=False), encoding="utf-8")
        sj_path.write_text(json.dumps(_make_session_json(session_id), ensure_ascii=False), encoding="utf-8")
        ay_path.write_text(yaml.safe_dump(_make_acceptance_yaml(session_id), allow_unicode=True), encoding="utf-8")
        result = validate_handoff(cp_path, sj_path, ay_path)
        assert result.passed is False, f"expected fail for {forbidden_key}"
        assert any(forbidden_key in e for e in result.errors), f"expected {forbidden_key} in errors"

    # 'ready' は禁止集合に含まれないため、トップレベルに追加しても error にならない
    cp_ready = _make_context_pack(session_id, extra={"ready": True})
    cp_ready_path = tmp_path / "cp_ready.json"
    cp_ready_path.write_text(json.dumps(cp_ready, ensure_ascii=False), encoding="utf-8")
    sj_ready = tmp_path / "sj_ready.json"
    ay_ready = tmp_path / "ay_ready.yaml"
    sj_ready.write_text(json.dumps(_make_session_json(session_id), ensure_ascii=False), encoding="utf-8")
    ay_ready.write_text(yaml.safe_dump(_make_acceptance_yaml(session_id), allow_unicode=True), encoding="utf-8")
    result_ready = validate_handoff(cp_ready_path, sj_ready, ay_ready)
    assert result_ready.passed is True, "'ready' should not trigger scope invasion error"
    assert not any("ready" in e for e in result_ready.errors)
