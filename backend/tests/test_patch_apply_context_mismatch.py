# -*- coding: utf-8 -*-
"""git apply context mismatch 系 stderr の分類と observability の検証。"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, List

import pytest

import orchestration.run_session as rs


class _DummyProc:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_classify_context_mismatch_from_git_apply_stderr() -> None:
    samples = [
        ("patch does not apply\n", True, "patch_does_not_apply"),
        ("foo\nwhile searching for:\nbar\n", True, "while_searching_for"),
        ("error: patch failed: corrupt patch at line 9\n", True, "error_patch_failed"),
        ("Hunk #3 FAILED at 12.\n", True, "hunk_failed"),
        ("random wrapper failure\n", False, ""),
    ]
    for stderr, want_mismatch, want_reason in samples:
        got = rs.classify_git_apply_stderr_for_context_mismatch(stderr)
        assert got.is_context_mismatch is want_mismatch, stderr
        assert got.matched_reason == want_reason, stderr


def _git_stub_for_apply_fail(calls: List[List[str]], apply_stderr: str) -> Any:
    def _git_run(args: List[str], *, check: bool = False) -> Any:  # noqa: ARG001
        calls.append(list(args))
        if args[:2] == ["diff", "--name-only"]:
            return _DummyProc(0, "", "")
        if args[:3] == ["ls-files", "--others", "--exclude-standard"]:
            return _DummyProc(0, "", "")
        if len(args) >= 4 and args[:2] == ["apply", "--check"]:
            return _DummyProc(1, "", apply_stderr)
        return _DummyProc(0, "", "")

    return _git_run


def test_log_context_mismatch_separately_from_generic_patch_apply_failure(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: List[List[str]] = []

    def _smart_cm(path: Path, root: Path) -> rs._ApplyPatchSmartOutcome:  # noqa: ARG001
        return rs._ApplyPatchSmartOutcome(
            applied=False,
            existing_files_git_apply_stderr=(
                "error: patch failed: corrupt patch at line 2\nwhile searching for:\nx\n"
            ),
        )

    def _smart_gen(path: Path, root: Path) -> rs._ApplyPatchSmartOutcome:  # noqa: ARG001
        return rs._ApplyPatchSmartOutcome(
            applied=False,
            existing_files_git_apply_stderr="unable to open object file\n",
        )

    caplog.set_level(logging.WARNING)
    monkeypatch.setattr(rs, "_git_run", _git_stub_for_apply_fail(calls, ""), raising=True)

    monkeypatch.setattr(rs, "_apply_patch_smart", _smart_cm, raising=True)
    info_cm = rs.apply_proposed_patch_and_capture_artifacts(
        tmp_path,
        {"proposed_patch": "diff --git a/x b/x\n--- a/x\n+++ b/x\n@@ -1 +1 @@\n-a\n+b\n", "changed_files": []},
    )
    assert info_cm["patch_apply_failed"] is True
    assert info_cm["patch_apply_failure_kind"] == "context_mismatch"
    assert info_cm["patch_apply_context_mismatch_reason"] == "while_searching_for"

    monkeypatch.setattr(rs, "_apply_patch_smart", _smart_gen, raising=True)
    info_gen = rs.apply_proposed_patch_and_capture_artifacts(
        tmp_path,
        {"proposed_patch": "diff --git a/x b/x\n--- a/x\n+++ b/x\n@@ -1 +1 @@\n-a\n+b\n", "changed_files": []},
    )
    assert info_gen["patch_apply_failed"] is True
    assert info_gen["patch_apply_failure_kind"] == "generic"

    msgs = [r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING]
    assert any("patch_apply context_mismatch" in m for m in msgs)
    assert any("patch_apply_failure (generic)" in m for m in msgs)
    assert any(c[:2] == ["diff", "--name-only"] for c in calls)
    assert any(c[:3] == ["ls-files", "--others", "--exclude-standard"] for c in calls)


def test_context_mismatch_handling_preserves_pre_normalization_flow(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """session-117 の patch_pre_normalize が先に実行され、ログが維持されること。"""
    caplog.set_level(logging.INFO)
    calls: List[List[str]] = []

    def _smart(_path: Path, _root: Path) -> rs._ApplyPatchSmartOutcome:
        return rs._ApplyPatchSmartOutcome(
            applied=False,
            existing_files_git_apply_stderr="patch does not apply\n",
        )

    monkeypatch.setattr(rs, "_git_run", _git_stub_for_apply_fail(calls, ""), raising=True)
    monkeypatch.setattr(rs, "_apply_patch_smart", _smart, raising=True)

    noisy = (
        "前置きテキスト\n"
        "diff --git a/z.txt b/z.txt\n"
        "--- a/z.txt\n"
        "+++ b/z.txt\n"
        "@@ -1 +1 @@\n"
        "-a\n"
        "+b\n"
    )
    rs.apply_proposed_patch_and_capture_artifacts(
        tmp_path, {"proposed_patch": noisy, "changed_files": []}
    )

    pre_logs = [r.getMessage() for r in caplog.records if "patch_pre_normalize:" in r.getMessage()]
    assert pre_logs, "事前正規化ログが残ること"
    assert any("patch_pre_normalize: done" in m for m in pre_logs)

    saved = (tmp_path / "patches" / "proposed.patch").read_text(encoding="utf-8")
    assert saved.startswith("diff --git ")
    assert "前置き" not in saved


def test_context_mismatch_handling_passes_validation_suite() -> None:
    """
    checks / failure_type の既存契約を壊さないこと（report 経路の最小検証）。
    """
    checks = rs._build_check_results_for_patch_apply_failure(
        "適用失敗メッセージ",
        failure_kind="context_mismatch",
        git_apply_stderr="patch does not apply\n",
        context_mismatch_reason="patch_does_not_apply",
    )
    assert checks["patch_apply_failed"] is True
    pa = checks["patch_apply"]
    assert pa["failure_kind"] == "context_mismatch"
    assert "patch does not apply" in pa["git_apply_stderr"]
    assert pa["context_mismatch_reason"] == "patch_does_not_apply"

    canon = rs.resolve_canonical_failure_type(checks)
    assert canon["failure_type"] == "patch_apply_failure"

    fr = rs.build_failure_record_for_report(checks, "failed", error_message=None, aborted_stage=None)
    assert fr["failure_type"] == "patch_apply_failure"
