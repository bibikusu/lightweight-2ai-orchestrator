# -*- coding: utf-8 -*-
"""proposed.patch 適用前の最小正規化（run_session.normalize_proposed_patch_text_minimal_before_git_apply）の検証。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

import orchestration.run_session as rs


def test_strip_trailing_whitespace_from_patch_before_apply() -> None:
    raw = (
        "diff --git a/foo.txt b/foo.txt\n"
        "--- a/foo.txt\n"
        "+++ b/foo.txt\n"
        "@@ -1 +1 @@\n"
        "-a\n"
        "+b  \n"
    )
    out = rs.normalize_proposed_patch_text_minimal_before_git_apply(raw)
    assert "+b" in out.splitlines()
    assert not any(line.endswith(" ") for line in out.splitlines())


def test_remove_non_diff_noise_from_patch_before_apply() -> None:
    core = (
        "diff --git a/foo.txt b/foo.txt\n"
        "--- a/foo.txt\n"
        "+++ b/foo.txt\n"
        "@@ -1 +1 @@\n"
        "-x\n"
        "+y\n"
    )
    raw = (
        "ここは説明文です。\n\n```\n"
        + core
        + "\n```\nThanks for reading.\n"
    )
    out = rs.normalize_proposed_patch_text_minimal_before_git_apply(raw)
    assert out.startswith("diff --git ")
    assert "Thanks" not in out
    assert "説明文" not in out
    assert core.strip() in out.replace("\r\n", "\n").strip()


def test_patch_normalization_preserves_diff_header_and_body() -> None:
    core = (
        "diff --git a/z.txt b/z.txt\n"
        "--- a/z.txt\n"
        "+++ b/z.txt\n"
        "@@ -1,2 +1,2 @@\n"
        " line1\n"
        "-old\n"
        "+new\n"
    )
    raw = "noise before\n" + core + "\ntrailing noise"
    out = rs.normalize_proposed_patch_text_minimal_before_git_apply(raw)
    assert "diff --git a/z.txt b/z.txt" in out
    assert "--- a/z.txt" in out
    assert "+++ b/z.txt" in out
    assert "@@ -1,2 +1,2 @@" in out
    assert "-old" in out
    assert "+new" in out
    assert "noise before" not in out
    assert "trailing noise" not in out

    normalized_full = rs.normalize_patch_for_git_apply(out)
    assert "diff --git a/z.txt b/z.txt" in normalized_full
    assert "-old" in normalized_full
    assert "+new" in normalized_full


def test_apply_check_uses_normalized_patch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """既存ファイル向けパスで git apply --check に渡る patch 内容が事前正規化済みであること。"""
    checked_snapshots: list[str] = []

    class _R:
        returncode = 0
        stdout = ""
        stderr = ""

    def _fake_git_run(args: list[str], *, check: bool = False):  # noqa: ARG001
        # git apply --check --whitespace=fix <path>（remaining.patch は処理後に削除される）
        if len(args) >= 4 and args[:2] == ["apply", "--check"] and args[2] == "--whitespace=fix":
            checked_snapshots.append(Path(args[3]).read_text(encoding="utf-8"))
        return _R()

    monkeypatch.setattr(rs, "_git_run", _fake_git_run, raising=True)

    noisy = (
        "LLM の前置き\n"
        "diff --git a/README.md b/README.md\n"
        "--- a/README.md\n"
        "+++ b/README.md\n"
        "@@ -1 +1 @@\n"
        "-x\n"
        "+y\r\n"
        "  \n"
        "以上です。\n"
    )
    impl_result: dict[str, Any] = {"proposed_patch": noisy, "changed_files": []}
    rs.apply_proposed_patch_and_capture_artifacts(tmp_path, impl_result)

    assert checked_snapshots, "git apply --check が呼ばれること"
    checked = checked_snapshots[0]
    assert "LLM" not in checked
    assert "以上です" not in checked
    assert "\r\n" not in checked
    assert "+y" in checked.splitlines()
