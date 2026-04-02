# -*- coding: utf-8 -*-

from pathlib import Path

import pytest

import orchestration.run_session as rs


def test_patch_validation():
    """不正パッチ/危険パスが検出されること。"""
    # 絶対パス
    assert rs.validate_patch_files(["/etc/passwd"])["status"] == "error"
    # トラバーサル
    assert rs.validate_patch_files(["../secrets.txt"])["status"] == "error"


def test_hunk_accuracy():
    """hunk カウント再計算が正確であること（count=1省略、末尾空行、No newline 行）。"""
    patch = (
        "diff --git a/a.txt b/a.txt\n"
        "--- a/a.txt\n"
        "+++ b/a.txt\n"
        "@@ -1 +1,2 @@\n"
        "-old\n"
        "+new\n"
        "+\n"
        "\\ No newline at end of file\n"
        "\n"
    )
    recounted = rs._recount_hunk_headers(patch.rstrip("\n"))
    # old: -1,1 は省略（-1） / new: +1,2 は明示
    assert "@@ -1 +1,2 @@" in recounted


def test_safe_apply(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """apply 前の dry-run（git apply --check）が実行されること。"""
    calls: list[list[str]] = []

    def _fake_git_run(args: list[str], *, check: bool = False):  # noqa: ARG001
        calls.append(list(args))

        class _R:
            returncode = 0
            stdout = ""
            stderr = ""

        return _R()

    monkeypatch.setattr(rs, "_git_run", _fake_git_run, raising=True)

    # 既存ファイル扱いにするため、確実に存在するファイルを対象にする
    patch_text = (
        "diff --git a/README.md b/README.md\n"
        "--- a/README.md\n"
        "+++ b/README.md\n"
        "@@ -1 +1 @@\n"
        "-x\n"
        "+y\n"
    )
    patch_path = tmp_path / "p.patch"
    patch_path.write_text(patch_text, encoding="utf-8")

    applied = rs._apply_patch_smart(patch_path, rs.ROOT_DIR)
    assert applied is True

    # 先に --check が呼ばれていること（要件: apply 前の dry-run）
    assert any(call[:2] == ["apply", "--check"] for call in calls), calls


def test_no_regression():
    """既存の正規化・バリデーション挙動が壊れていないこと。"""
    raw = "--- a/f.py\n+++ b/f.py\n@@ -1 +1 @@\n-x\n+y\n"
    normalized = rs.normalize_patch_for_git_apply(raw)
    assert normalized.startswith("diff --git a/f.py b/f.py\n")
    assert "--- a/f.py\n+++ b/f.py\n" in normalized
    assert rs.validate_patch_files(["a.py"])["status"] == "success"
    assert rs.validate_patch_files(["docs/sessions/test.json"])["status"] == "error"

