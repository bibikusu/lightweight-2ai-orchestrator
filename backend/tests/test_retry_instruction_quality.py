# -*- coding: utf-8 -*-

import pytest

from orchestration.run_session import (
    SessionContext,
    _merge_retry_instruction,
    build_retry_prompts,
    resolve_canonical_failure_type,
)


def _ctx() -> SessionContext:
    return SessionContext(
        session_id="session-05a",
        session_data={"phase_id": "p", "title": "t", "goal": "g"},
        acceptance_data={"raw_yaml": "", "parsed": {}},
        master_instruction="",
        global_rules="",
        roadmap_text="",
        runtime_config={},
    )


def test_retry_instruction_contains_required_fields():
    """AC-01: プロンプトが必須 JSON キーを列挙している"""
    ctx = _ctx()
    prepared_spec: dict = {"objective": "o", "forbidden_changes": ["x/"]}
    impl_result: dict = {"changed_files": ["a.py"]}
    check_results: dict = {
        "test": {"status": "failed", "command": "pytest", "returncode": 1, "stderr": "e", "stdout": ""},
        "lint": {"status": "skipped"},
        "typecheck": {"status": "skipped"},
        "build": {"status": "skipped"},
        "success": False,
    }
    _, user = build_retry_prompts(ctx, prepared_spec, impl_result, check_results)
    for key in (
        "failed_tests",
        "error_summary",
        "changed_files",
        "fix_instructions",
        "do_not_change",
        "failure_type",
        "cause_summary",
        "priority",
        "session_id",
    ):
        assert key in user, f"missing: {key}"


def test_retry_instruction_has_single_failure_type():
    """AC-02: 分類は1種類のみ（マージ後は正本 resolve_canonical_failure_type と一致）"""
    ctx = _ctx()
    prepared_spec: dict = {"objective": "o"}
    impl_result: dict = {"changed_files": []}
    check_results: dict = {
        "lint": {"status": "failed", "command": "lint", "returncode": 1, "stderr": "e", "stdout": ""},
        "test": {"status": "skipped"},
        "typecheck": {"status": "skipped"},
        "build": {"status": "skipped"},
        "success": False,
    }
    _, user = build_retry_prompts(ctx, prepared_spec, impl_result, check_results)
    assert "1つのみ" in user or "exactly one" in user.lower() or "failure_type は出力に1つ" in user

    expected = resolve_canonical_failure_type(check_results)
    merged = _merge_retry_instruction(
        {"failure_type": "wrong_type_should_be_overwritten"},
        ctx,
        prepared_spec,
        impl_result,
        check_results,
    )
    assert merged["failure_type"] == expected["failure_type"]
    assert merged["priority"] == expected["priority"]


def test_retry_instruction_includes_do_not_change():
    """AC-03: マージ後に do_not_change が非空リストである"""
    ctx = _ctx()
    prepared_spec: dict = {"objective": "o", "forbidden_changes": ["secrets/"]}
    impl_result: dict = {"changed_files": []}
    check_results: dict = {
        "test": {"status": "failed", "command": "t", "returncode": 1, "stderr": "e", "stdout": ""},
        "lint": {"status": "skipped"},
        "typecheck": {"status": "skipped"},
        "build": {"status": "skipped"},
        "success": False,
    }
    merged = _merge_retry_instruction({}, ctx, prepared_spec, impl_result, check_results)
    assert isinstance(merged.get("do_not_change"), list)
    assert len(merged["do_not_change"]) >= 1


def test_retry_does_not_expand_scope():
    """AC-05: スコープ拡張禁止が system / user に含まれる"""
    ctx = _ctx()
    prepared_spec: dict = {"objective": "o"}
    impl_result: dict = {"changed_files": []}
    check_results: dict = {
        "test": {"status": "failed", "command": "t", "returncode": 1, "stderr": "e", "stdout": ""},
        "lint": {"status": "skipped"},
        "typecheck": {"status": "skipped"},
        "build": {"status": "skipped"},
        "success": False,
    }
    system, user = build_retry_prompts(ctx, prepared_spec, impl_result, check_results)
    assert "Do not expand scope" in system
    assert "prepared_spec" in user
