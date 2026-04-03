# -*- coding: utf-8 -*-
"""session-114: run_session 実行前のトップレベル関数重複検出 preflight（AC-114-01〜05）。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

import orchestration.run_session as run_session


# ---------------------------------------------------------------------------
# AC-114-01
# ---------------------------------------------------------------------------
def test_detect_duplicate_top_level_function_names_returns_duplicate_name_list() -> None:
    """代表例 orchestrator_version を含む重複トップレベル def が検出される。"""
    src = """
def orchestrator_version() -> str:
    return "a"

def orchestrator_version() -> str:
    return "b"

def other_once():
    pass
"""
    dups = run_session.detect_duplicate_top_level_function_names(src)
    assert dups == ["orchestrator_version"]


# ---------------------------------------------------------------------------
# AC-114-02
# ---------------------------------------------------------------------------
def test_detect_duplicate_top_level_function_names_returns_empty_for_clean_source() -> None:
    """重複がなければ空リスト（現在の run_session.py をソースとしても通過）。"""
    path = Path(run_session.__file__).resolve()
    text = path.read_text(encoding="utf-8")
    assert run_session.detect_duplicate_top_level_function_names(text) == []


# ---------------------------------------------------------------------------
# AC-114-03
# ---------------------------------------------------------------------------
def test_main_stops_on_duplicate_definition_preflight_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """main は preflight 失敗時に通常の live-run（API 呼び出し以降）に進まず終了コード 1。"""
    monkeypatch.chdir(run_session.ROOT_DIR)
    monkeypatch.setattr(sys, "argv", ["run_session.py", "--session-id", "session-114-preflight"])
    monkeypatch.setattr(
        run_session,
        "detect_duplicate_top_level_function_names",
        lambda _source: ["orchestrator_version"],
    )
    rc = run_session.main()
    assert rc == 1


# ---------------------------------------------------------------------------
# AC-114-04
# ---------------------------------------------------------------------------
def test_duplicate_definition_preflight_error_message_is_code_state_specific(
    tmp_path: Path,
) -> None:
    """重複名が明示され、インフラ／接続系と誤認しない文言である。"""
    dup_file = tmp_path / "dup_mod.py"
    dup_file.write_text(
        "def orchestrator_version():\n    return 1\n\ndef orchestrator_version():\n    return 2\n",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError) as exc_info:
        run_session.enforce_run_session_duplicate_definition_preflight(dup_file)
    msg = str(exc_info.value)
    assert "orchestrator_version" in msg
    assert "[CODE_STATE_PREFLIGHT]" in msg
    assert "duplicate top-level function definitions" in msg
    assert "not an API, network, or infrastructure failure" in msg
    assert "APIConnectionError" not in msg
    assert "Connection" not in msg


# ---------------------------------------------------------------------------
# AC-114-05
# ---------------------------------------------------------------------------
def test_duplicate_definition_guard_does_not_require_builder_or_reviewer_contract_changes() -> None:
    """本変更は preflight 追加のみで Builder/Reviewer 契約コードパスを置換しない。"""
    assert callable(run_session.detect_duplicate_top_level_function_names)
    assert callable(run_session.enforce_run_session_duplicate_definition_preflight)
    assert callable(run_session.build_prepared_spec_prompts)
    assert callable(run_session.call_chatgpt_for_prepared_spec)
    assert callable(run_session.call_chatgpt_for_retry_instruction)
    assert callable(run_session.call_claude_for_implementation)
