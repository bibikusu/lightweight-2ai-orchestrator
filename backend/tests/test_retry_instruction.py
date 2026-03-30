# -*- coding: utf-8 -*-

from orchestration.run_session import (
    SessionContext,
    _merge_retry_instruction,
    build_retry_prompts,
)


def _minimal_ctx() -> SessionContext:
    return SessionContext(
        session_id="session-05",
        session_data={"phase_id": "p", "title": "t", "goal": "g"},
        acceptance_data={"raw_yaml": "", "parsed": {}},
        master_instruction="",
        global_rules="",
        roadmap_text="",
        runtime_config={},
    )


def test_retry_instruction_contains_required_fields():
    """AC-01: プロンプトが必須 JSON キーを列挙している"""
    ctx = _minimal_ctx()
    prepared_spec: dict = {"objective": "o", "forbidden_changes": ["prod/"]}
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
    ):
        assert key in user, f"missing prompt mention: {key}"


def test_retry_instruction_contains_failure_type():
    """AC-02: 分類された failure_type がプロンプトに含まれる"""
    ctx = _minimal_ctx()
    prepared_spec: dict = {"objective": "o"}
    impl_result: dict = {"changed_files": []}
    check_results: dict = {
        "build": {"status": "failed", "command": "make", "returncode": 2, "stderr": "boom", "stdout": ""},
        "test": {"status": "failed", "command": "pytest", "returncode": 1, "stderr": "x", "stdout": ""},
        "lint": {"status": "skipped"},
        "typecheck": {"status": "skipped"},
        "success": False,
    }
    _, user = build_retry_prompts(ctx, prepared_spec, impl_result, check_results)
    assert "build_error" in user


def test_retry_instruction_has_fix_instructions():
    """AC-03: マージ後の retry 指示に非空の fix_instructions がある"""
    ctx = _minimal_ctx()
    prepared_spec: dict = {"objective": "o"}
    impl_result: dict = {"changed_files": ["x.py"]}
    check_results: dict = {
        "lint": {"status": "failed", "command": "lint", "returncode": 1, "stderr": "err", "stdout": ""},
        "test": {"status": "skipped"},
        "typecheck": {"status": "skipped"},
        "build": {"status": "skipped"},
        "success": False,
    }
    merged = _merge_retry_instruction({}, ctx, prepared_spec, impl_result, check_results)
    assert isinstance(merged.get("fix_instructions"), list)
    assert len(merged["fix_instructions"]) >= 1
    assert all(isinstance(x, str) and x.strip() for x in merged["fix_instructions"])


def test_retry_instruction_has_do_not_change():
    """AC-04: マージ後の retry 指示に do_not_change がある"""
    ctx = _minimal_ctx()
    prepared_spec: dict = {
        "objective": "o",
        "forbidden_changes": ["secrets/", "vendor/"],
    }
    impl_result: dict = {"changed_files": []}
    check_results: dict = {
        "typecheck": {
            "status": "failed",
            "command": "mypy",
            "returncode": 1,
            "stderr": "type err",
            "stdout": "",
        },
        "test": {"status": "skipped"},
        "lint": {"status": "skipped"},
        "build": {"status": "skipped"},
        "success": False,
    }
    merged = _merge_retry_instruction({}, ctx, prepared_spec, impl_result, check_results)
    assert isinstance(merged.get("do_not_change"), list)
    assert len(merged["do_not_change"]) >= 1


def test_retry_does_not_expand_scope():
    """AC-05: プロンプトがスコープ拡張禁止を明示している"""
    ctx = _minimal_ctx()
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
    assert "Do not expand scope" in system or "prepared_spec" in system.lower()
    assert "allowed_changes" in user or "scope" in user.lower()
