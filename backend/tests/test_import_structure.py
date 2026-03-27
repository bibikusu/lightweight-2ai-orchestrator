# -*- coding: utf-8 -*-
"""session-08 / 08a: import 正規化の受入テスト（AC-01〜05）。

AC-03 検査対象に自分自身が含まれるため、パス操作の典型パターン文字列はソースに直書きしない。
"""

import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[2]
TESTS_DIR = ROOT_DIR / "backend" / "tests"
_PATH_HACK = "sys.path" + ".insert"


def test_run_session_imports_with_single_entrypoint_bootstrap():
    """AC-01: import 時は sys.path を変えない。パス注入は main 先頭の互換レイヤー1箇所のみ。"""
    before = sys.path.copy()
    import orchestration.run_session as rs

    assert sys.path == before
    assert hasattr(rs, "main")
    assert hasattr(rs, "ROOT_DIR")
    assert hasattr(rs, "_ensure_repo_root_on_sys_path")
    assert callable(rs._ensure_repo_root_on_sys_path)


def test_provider_modules_import_without_manual_pythonpath():
    """AC-02: providers をパッケージパスから import できる"""
    from orchestration.providers.openai_client import (
        OpenAIClientConfig,
        OpenAIClientWrapper,
    )
    from orchestration.providers.claude_client import (
        ClaudeClientConfig,
        ClaudeClientWrapper,
    )

    assert OpenAIClientConfig is not None
    assert OpenAIClientWrapper is not None
    assert ClaudeClientConfig is not None
    assert ClaudeClientWrapper is not None


def test_orchestration_imports_work_in_ci_layout(monkeypatch):
    """AC-10-03: CI 想定の配置でも orchestration import が壊れない。"""
    monkeypatch.chdir(ROOT_DIR)
    import orchestration.run_session as rs
    from orchestration.providers.claude_client import ClaudeClientConfig
    from orchestration.providers.openai_client import OpenAIClientConfig

    assert hasattr(rs, "main")
    assert OpenAIClientConfig is not None
    assert ClaudeClientConfig is not None


def test_existing_tests_do_not_need_sys_path_insert():
    """AC-03: backend/tests/test_*.py にパス先頭注入（sys.path の insert）が無い"""
    offenders: list[str] = []
    for path in sorted(TESTS_DIR.glob("test_*.py")):
        text = path.read_text(encoding="utf-8")
        if _PATH_HACK in text:
            offenders.append(path.name)
    assert not offenders, f"残存: {offenders}"


def test_existing_ci_and_dry_run_flow_not_broken(monkeypatch, tmp_path):
    """AC-04: dry-run main がローカルで成立する（CI dry-run 契約）"""
    import orchestration.run_session as rs

    monkeypatch.setattr(rs, "ARTIFACTS_DIR", tmp_path / "artifacts")
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_session.py", "--dry-run", "--session-id", "session-01"],
    )
    assert rs.main() == 0


def test_existing_retry_and_report_contracts_not_broken():
    """AC-05: retry / report 関連の公開 API が import 可能で契約が壊れていない"""
    from orchestration.run_session import (
        SessionContext,
        _compute_retry_cause_fingerprint,
        _merge_retry_instruction,
        build_retry_prompts,
        build_session_report_record,
        classify_failure_type,
        generate_report,
        validate_acceptance_test_mapping,
    )

    assert callable(_merge_retry_instruction)
    assert callable(build_retry_prompts)
    assert callable(_compute_retry_cause_fingerprint)
    assert callable(classify_failure_type)
    assert callable(validate_acceptance_test_mapping)
    assert callable(generate_report)
    assert callable(build_session_report_record)

    ctx = SessionContext(
        session_id="s",
        session_data={"phase_id": "p", "title": "t", "goal": "g"},
        acceptance_data={"raw_yaml": "", "parsed": {}},
        master_instruction="",
        global_rules="",
        roadmap_text="",
        runtime_config={},
    )
    assert ctx.session_id == "s"
