# -*- coding: utf-8 -*-
"""session-119: patch_apply_failure の cause_summary 診断強化テスト。

テスト観点:
  AC-119-01: context_mismatch 系 stderr → cause_summary に "patch context mismatch:" を含む
  AC-119-02: 非 context_mismatch だが stderr あり → "git apply error:" を含む
  AC-119-03: stderr なし（diff ゼロ）→ "差分が検出されませんでした" を含む
  AC-119-04: failure_type は常に patch_apply_failure を維持
  AC-119-05: success ケースは cause_summary が None（汚染なし）
"""

from __future__ import annotations

from typing import Any, Dict

import orchestration.run_session as rs


def _make_patch_apply_checks(
    *,
    failure_kind: str,
    git_apply_stderr: str,
    context_mismatch_reason: str = "",
) -> Dict[str, Any]:
    """_build_check_results_for_patch_apply_failure を使って checks ブロックを生成するヘルパー。"""
    return rs._build_check_results_for_patch_apply_failure(
        "git apply 相当の処理後も実差分が得られませんでした",
        failure_kind=failure_kind,
        git_apply_stderr=git_apply_stderr,
        context_mismatch_reason=context_mismatch_reason,
    )


# ---- AC-119-01: context_mismatch 系 ----------------------------------------

def test_cause_summary_contains_context_mismatch_label_for_context_mismatch_kind() -> None:
    """AC-119-01a: failure_kind=context_mismatch → cause_summary が 'patch context mismatch:' で始まる。"""
    checks = _make_patch_apply_checks(
        failure_kind="context_mismatch",
        git_apply_stderr="error: patch failed: foo.py:10\nerror: foo.py: patch does not apply\n",
        context_mismatch_reason="patch_does_not_apply",
    )
    cf = rs.classify_failure(checks)
    assert cf["cause_summary"].startswith("patch context mismatch:"), cf["cause_summary"]


def test_cause_summary_includes_context_mismatch_reason() -> None:
    """AC-119-01b: context_mismatch_reason が cause_summary に含まれる。"""
    checks = _make_patch_apply_checks(
        failure_kind="context_mismatch",
        git_apply_stderr="while searching for:\nfoo\n",
        context_mismatch_reason="while_searching_for",
    )
    cf = rs.classify_failure(checks)
    assert "while_searching_for" in cf["cause_summary"], cf["cause_summary"]


def test_cause_summary_includes_git_stderr_for_context_mismatch() -> None:
    """AC-119-01c: git_apply_stderr の内容が cause_summary に含まれる。"""
    checks = _make_patch_apply_checks(
        failure_kind="context_mismatch",
        git_apply_stderr="Hunk #2 FAILED at 42.\n",
        context_mismatch_reason="hunk_failed",
    )
    cf = rs.classify_failure(checks)
    assert "Hunk #2 FAILED" in cf["cause_summary"], cf["cause_summary"]


# ---- AC-119-02: generic + stderr あり ----------------------------------------

def test_cause_summary_contains_git_apply_error_label_for_generic_with_stderr() -> None:
    """AC-119-02a: failure_kind=generic + stderr あり → 'git apply error:' で始まる。"""
    checks = _make_patch_apply_checks(
        failure_kind="generic",
        git_apply_stderr="error: unable to open object file\n",
    )
    cf = rs.classify_failure(checks)
    assert cf["cause_summary"].startswith("git apply error:"), cf["cause_summary"]


def test_cause_summary_includes_stderr_content_for_generic_with_stderr() -> None:
    """AC-119-02b: stderr 内容が cause_summary に含まれる。"""
    checks = _make_patch_apply_checks(
        failure_kind="generic",
        git_apply_stderr="corrupt patch at line 99\n",
    )
    cf = rs.classify_failure(checks)
    assert "corrupt patch at line 99" in cf["cause_summary"], cf["cause_summary"]


# ---- AC-119-03: stderr なし（diff ゼロ）--------------------------------------

def test_cause_summary_indicates_empty_diff_when_no_stderr() -> None:
    """AC-119-03a: failure_kind=generic + stderr なし → 差分ゼロメッセージ。"""
    checks = _make_patch_apply_checks(
        failure_kind="generic",
        git_apply_stderr="",
    )
    cf = rs.classify_failure(checks)
    assert "差分が検出されませんでした" in cf["cause_summary"], cf["cause_summary"]


def test_cause_summary_no_context_mismatch_label_when_no_stderr() -> None:
    """AC-119-03b: stderr なし → 'patch context mismatch:' でも 'git apply error:' でもない。"""
    checks = _make_patch_apply_checks(
        failure_kind="generic",
        git_apply_stderr="",
    )
    cf = rs.classify_failure(checks)
    assert "patch context mismatch:" not in cf["cause_summary"]
    assert "git apply error:" not in cf["cause_summary"]


# ---- AC-119-04: failure_type 維持 -------------------------------------------

def test_failure_type_remains_patch_apply_failure_for_all_diagnosis_variants() -> None:
    """AC-119-04: 3 ケースすべてで failure_type == 'patch_apply_failure' を維持。"""
    cases = [
        _make_patch_apply_checks(
            failure_kind="context_mismatch",
            git_apply_stderr="patch does not apply\n",
            context_mismatch_reason="patch_does_not_apply",
        ),
        _make_patch_apply_checks(
            failure_kind="generic",
            git_apply_stderr="unable to open object file\n",
        ),
        _make_patch_apply_checks(
            failure_kind="generic",
            git_apply_stderr="",
        ),
    ]
    for checks in cases:
        cf = rs.classify_failure(checks)
        assert cf["failure_type"] == "patch_apply_failure", cf

        fr = rs.build_failure_record_for_report(
            checks, "failed", error_message=None, aborted_stage=None
        )
        assert fr["failure_type"] == "patch_apply_failure", fr


# ---- AC-119-05: success 汚染なし --------------------------------------------

def test_cause_summary_is_none_for_success_status() -> None:
    """AC-119-05: status=success のとき cause_summary は None（診断が混入しない）。"""
    checks = {
        "patch_apply": {"status": "passed"},
        "test": {"status": "passed"},
        "lint": {"status": "passed"},
        "typecheck": {"status": "passed"},
        "build": {"status": "passed"},
        "success": True,
        "patch_apply_failed": False,
    }
    fr = rs.build_failure_record_for_report(
        checks, "success", error_message=None, aborted_stage=None
    )
    assert fr["cause_summary"] is None, fr


# ---- _build_patch_apply_cause_summary の単体テスト --------------------------

def test_build_patch_apply_cause_summary_context_mismatch() -> None:
    """ヘルパー単体: context_mismatch ケース。"""
    pa: Dict[str, Any] = {
        "failure_kind": "context_mismatch",
        "git_apply_stderr": "patch does not apply\n",
        "context_mismatch_reason": "patch_does_not_apply",
    }
    result = rs._build_patch_apply_cause_summary(pa)
    assert result.startswith("patch context mismatch:")
    assert "patch_does_not_apply" in result
    assert "patch does not apply" in result


def test_build_patch_apply_cause_summary_generic_with_stderr() -> None:
    """ヘルパー単体: generic + stderr あり。"""
    pa: Dict[str, Any] = {
        "failure_kind": "generic",
        "git_apply_stderr": "error: something went wrong\n",
        "context_mismatch_reason": "",
    }
    result = rs._build_patch_apply_cause_summary(pa)
    assert result.startswith("git apply error:")
    assert "something went wrong" in result


def test_build_patch_apply_cause_summary_empty_stderr() -> None:
    """ヘルパー単体: stderr なし → 差分ゼロメッセージ。"""
    pa: Dict[str, Any] = {
        "failure_kind": "generic",
        "git_apply_stderr": "",
        "context_mismatch_reason": "",
    }
    result = rs._build_patch_apply_cause_summary(pa)
    assert "差分が検出されませんでした" in result


def test_build_patch_apply_cause_summary_context_mismatch_no_reason() -> None:
    """ヘルパー単体: context_mismatch + reason なし → フォールバック文言。"""
    pa: Dict[str, Any] = {
        "failure_kind": "context_mismatch",
        "git_apply_stderr": "",
        "context_mismatch_reason": "",
    }
    result = rs._build_patch_apply_cause_summary(pa)
    assert result.startswith("patch context mismatch:")
    assert "詳細不明" in result
