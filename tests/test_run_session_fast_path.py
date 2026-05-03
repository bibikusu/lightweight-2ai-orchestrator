"""
AC-168-01〜09 対応テスト: run_session.py の execution_mode fast_path v0 分岐
"""

import argparse
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))


# ---------------------------------------------------------------------------
# AC-168-01: execution_mode=full_stack の場合、_run_session_fast_path が呼ばれない
# ---------------------------------------------------------------------------

def test_full_stack_unchanged():
    """execution_mode=full_stack のとき、_run_session_fast_path が呼ばれない。"""
    from orchestration import run_session

    args = argparse.Namespace(
        session_id="session-test",
        execution_mode="full_stack",
        resume=False,
        dry_run=False,
        skip_build=False,
        max_retries=None,
        project=None,
        batch=None,
        use_selector=False,
    )

    with patch.object(run_session, "_run_session_fast_path") as mock_fast, \
         patch.object(run_session, "ensure_artifact_dirs", return_value=Path("/tmp/test")), \
         patch.object(run_session, "_iso_utc_now", return_value="2026-01-01T00:00:00Z"), \
         patch.object(run_session, "enforce_run_session_duplicate_definition_preflight"), \
         patch.object(run_session, "load_session_context", side_effect=RuntimeError("short-circuit")):
        try:
            run_session._run_single_session_impl(args)
        except RuntimeError:
            pass

    mock_fast.assert_not_called()


# ---------------------------------------------------------------------------
# AC-168-02: execution_mode=fast_path の場合、_run_session_fast_path が呼ばれる
# ---------------------------------------------------------------------------

def test_fast_path_branch_selected():
    """execution_mode=fast_path のとき、_run_session_fast_path が呼ばれる。"""
    from orchestration import run_session

    args = argparse.Namespace(
        session_id="session-test",
        execution_mode="fast_path",
        resume=False,
        dry_run=False,
        skip_build=False,
        max_retries=None,
        project=None,
        batch=None,
        use_selector=False,
    )

    with patch.object(run_session, "_run_session_fast_path", return_value=0) as mock_fast, \
         patch.object(run_session, "ensure_artifact_dirs", return_value=Path("/tmp/test")), \
         patch.object(run_session, "_iso_utc_now", return_value="2026-01-01T00:00:00Z"), \
         patch.object(run_session, "enforce_run_session_duplicate_definition_preflight"):
        result = run_session._run_single_session_impl(args)

    mock_fast.assert_called_once()
    assert result == 0


# ---------------------------------------------------------------------------
# AC-168-03: fast_path で load_session_context / validate_session_context が呼ばれる
# ---------------------------------------------------------------------------

def test_fast_path_executes_required_stages(tmp_path):
    """fast_path 実行時に session_context_loading / session_schema_validation が実行される。"""
    from orchestration import run_session

    args = argparse.Namespace(session_id="session-test", execution_mode="fast_path")
    mock_ctx = MagicMock()
    mock_ctx.session_data = {"scope": [], "forbidden_changes": []}

    with patch.object(run_session, "load_session_context", return_value=mock_ctx) as mock_load, \
         patch.object(run_session, "validate_session_context") as mock_validate, \
         patch.object(run_session, "_iso_utc_now", return_value="2026-01-01T00:00:00Z"):
        run_session._run_session_fast_path(args, tmp_path, "2026-01-01T00:00:00Z")

    mock_load.assert_called_once_with("session-test")
    mock_validate.assert_called_once_with(mock_ctx)


# ---------------------------------------------------------------------------
# AC-168-04: fast_path で provider API 呼び出しが行われない
# ---------------------------------------------------------------------------

def test_fast_path_skips_provider_call(tmp_path):
    """fast_path 実行時に call_chatgpt_for_prepared_spec / call_claude_for_implementation が呼ばれない。"""
    from orchestration import run_session

    args = argparse.Namespace(session_id="session-test", execution_mode="fast_path")
    mock_ctx = MagicMock()

    with patch.object(run_session, "load_session_context", return_value=mock_ctx), \
         patch.object(run_session, "validate_session_context"), \
         patch.object(run_session, "_iso_utc_now", return_value="2026-01-01T00:00:00Z"), \
         patch.object(run_session, "call_chatgpt_for_prepared_spec") as mock_gpt, \
         patch.object(run_session, "call_claude_for_implementation") as mock_claude:
        run_session._run_session_fast_path(args, tmp_path, "2026-01-01T00:00:00Z")

    mock_gpt.assert_not_called()
    mock_claude.assert_not_called()


# ---------------------------------------------------------------------------
# AC-168-05: fast_path で patch_apply が実行されない
# ---------------------------------------------------------------------------

def test_fast_path_skips_patch_apply(tmp_path):
    """fast_path 実行時に _apply_patch_validate_and_run_local_checks が呼ばれない。"""
    from orchestration import run_session

    args = argparse.Namespace(session_id="session-test", execution_mode="fast_path")
    mock_ctx = MagicMock()

    with patch.object(run_session, "load_session_context", return_value=mock_ctx), \
         patch.object(run_session, "validate_session_context"), \
         patch.object(run_session, "_iso_utc_now", return_value="2026-01-01T00:00:00Z"), \
         patch.object(run_session, "_apply_patch_validate_and_run_local_checks") as mock_patch:
        run_session._run_session_fast_path(args, tmp_path, "2026-01-01T00:00:00Z")

    mock_patch.assert_not_called()


# ---------------------------------------------------------------------------
# AC-168-06: fast_path 失敗時に full_stack へ fallback しない
# ---------------------------------------------------------------------------

def test_fast_path_no_fallback(tmp_path):
    """fast_path 内で例外が発生しても full_stack ロジックへ fallback せず exit code 1 を返す。"""
    from orchestration import run_session

    args = argparse.Namespace(session_id="session-test", execution_mode="fast_path")

    with patch.object(run_session, "load_session_context", side_effect=RuntimeError("load failed")), \
         patch.object(run_session, "_iso_utc_now", return_value="2026-01-01T00:00:00Z"), \
         patch.object(run_session, "call_chatgpt_for_prepared_spec") as mock_gpt, \
         patch.object(run_session, "call_claude_for_implementation") as mock_claude:
        result = run_session._run_session_fast_path(args, tmp_path, "2026-01-01T00:00:00Z")

    assert result == 1
    mock_gpt.assert_not_called()
    mock_claude.assert_not_called()


# ---------------------------------------------------------------------------
# AC-168-07: fast_path 実行時に minimal report が生成される
# ---------------------------------------------------------------------------

def test_fast_path_writes_minimal_report(tmp_path):
    """fast_path 実行後に session_report.md が生成され execution_mode=fast_path が記録される。"""
    from orchestration import run_session

    args = argparse.Namespace(session_id="session-test", execution_mode="fast_path")
    mock_ctx = MagicMock()

    with patch.object(run_session, "load_session_context", return_value=mock_ctx), \
         patch.object(run_session, "validate_session_context"), \
         patch.object(run_session, "_iso_utc_now", return_value="2026-01-01T00:00:00Z"):
        result = run_session._run_session_fast_path(args, tmp_path, "2026-01-01T00:00:00Z")

    assert result == 0
    report_path = tmp_path / "reports" / "session_report.md"
    assert report_path.exists(), f"session_report.md が存在しない: {report_path}"
    content = report_path.read_text(encoding="utf-8")
    assert "fast_path" in content
    assert "execution_mode" in content
    assert "session-test" in content
    assert "status" in content


# ---------------------------------------------------------------------------
# AC-168-08: selector 側に変更がない (md5 baseline 一致確認)
# ---------------------------------------------------------------------------

def test_selector_unchanged():
    """selector ファイルの md5 が baseline と一致する（session-167 で記録）。"""
    BASELINE = {
        "orchestration/selector/core.py":   "9b19e2cbe3487d3090096c5343c88611",
        "orchestration/selector/loader.py": "959db533bf086f83765d8f6f16fbbe7b",
        "orchestration/selector/writer.py": "aaf7e28e0e9c52d12d30c8d3349cf982",
    }
    for rel_path, expected_md5 in BASELINE.items():
        file_path = ROOT_DIR / rel_path
        assert file_path.exists(), f"selector ファイルが存在しない: {file_path}"
        proc = subprocess.run(
            ["md5sum", str(file_path)],
            capture_output=True, text=True, cwd=str(ROOT_DIR),
        )
        if proc.returncode != 0:
            # macOS では md5 コマンドを使う
            proc = subprocess.run(
                ["md5", str(file_path)],
                capture_output=True, text=True, cwd=str(ROOT_DIR),
            )
        actual_md5 = proc.stdout.split()[0].lstrip("MD5 (").rstrip(")")
        # md5sum: "hash  path" / md5: "MD5 (path) = hash"
        if "=" in proc.stdout:
            actual_md5 = proc.stdout.split("=")[-1].strip()
        else:
            actual_md5 = proc.stdout.split()[0]
        assert actual_md5 == expected_md5, (
            f"{rel_path} の md5 が baseline と一致しない: {actual_md5} != {expected_md5}"
        )


# ---------------------------------------------------------------------------
# AC-168-09: session-167 の既存テストが引き続き PASS する
# ---------------------------------------------------------------------------

def test_existing_tests_still_pass():
    """tests/test_run_session_selector.py の 19 件が PASS することを確認する。"""
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_run_session_selector.py", "-q", "--tb=short"],
        capture_output=True,
        text=True,
        cwd=str(ROOT_DIR),
        env={**__import__("os").environ, "PYTHONPATH": str(ROOT_DIR)},
    )
    assert proc.returncode == 0, (
        f"test_run_session_selector.py に失敗があります:\n{proc.stdout}\n{proc.stderr}"
    )
