# -*- coding: utf-8 -*-
"""block3-retry-02: retry_instruction マージ結果の必須キーと正本7値 failure_type の検証。"""

from orchestration.run_session import (
    SessionContext,
    _merge_retry_instruction,
)

RETRY_JSON_REQUIRED_KEYS = frozenset(
    {
        "session_id",
        "failure_type",
        "priority",
        "cause_summary",
        "fix_instructions",
        "do_not_change",
    }
)

# session-09 正本（no_failure はマージ結果では通常出ないが列挙に含めない）
CANONICAL_FAILURE_TYPES = frozenset(
    {
        "build_error",
        "import_error",
        "type_mismatch",
        "test_failure",
        "scope_violation",
        "breaking_change",
        "spec_missing",
    }
)


def _ctx() -> SessionContext:
    return SessionContext(
        session_id="block3-retry-02",
        session_data={"phase_id": "p", "title": "t", "goal": "g"},
        acceptance_data={"raw_yaml": "", "parsed": {}},
        master_instruction="",
        global_rules="",
        roadmap_text="",
        runtime_config={},
    )


def test_merged_retry_json_has_required_keys():
    """retry_instruction マージ結果に必須キーが欠落していない。"""
    ctx = _ctx()
    prepared_spec: dict = {"objective": "o", "forbidden_changes": []}
    impl_result: dict = {"changed_files": ["a.py"]}
    check_results: dict = {
        "test": {"status": "failed", "command": "pytest", "returncode": 1, "stderr": "e", "stdout": ""},
        "lint": {"status": "skipped"},
        "typecheck": {"status": "skipped"},
        "build": {"status": "skipped"},
        "success": False,
    }
    merged = _merge_retry_instruction({}, ctx, prepared_spec, impl_result, check_results)
    for k in RETRY_JSON_REQUIRED_KEYS:
        assert k in merged
    assert isinstance(merged["fix_instructions"], list)
    assert isinstance(merged["do_not_change"], list)
    assert merged["session_id"] == ctx.session_id
    assert merged["failure_type"] in CANONICAL_FAILURE_TYPES
