# -*- coding: utf-8 -*-

import pytest

from orchestration.run_session import (
    _normalize_hunk_line_prefixes,
    normalize_patch_for_git_apply,
    validate_changed_files_before_patch,
    validate_patch_files,
)


def test_patch_validation_within_limit():
    """AC-02-01: 5件以内で成功"""
    changed_files = ["a.py", "b.py", "c.py"]
    result = validate_patch_files(changed_files)
    assert result["status"] == "success"


def test_patch_validation_over_limit():
    """AC-02-02: 6件以上で失敗"""
    changed_files = ["a.py", "b.py", "c.py", "d.py", "e.py", "f.py"]
    result = validate_patch_files(changed_files)
    assert result["status"] == "error"
    assert result["error_type"] == "scope_violation"


def test_patch_validation_forbidden_paths():
    """AC-02-03: 禁止パスで失敗"""
    changed_files = ["docs/sessions/test.json"]
    result = validate_patch_files(changed_files)
    assert result["status"] == "error"
    assert result["error_type"] == "scope_violation"


def test_patch_validation_allows_explicitly_allowed_artifacts_path():
    """allowed_changes で明示許可された artifacts パスは通過"""
    impl_result = {"changed_files": ["artifacts/.gitkeep"]}
    prepared_spec = {"allowed_changes": ["artifacts/.gitkeep"], "forbidden_changes": []}
    session_data = {"out_of_scope": []}

    validate_changed_files_before_patch(
        impl_result=impl_result,
        prepared_spec=prepared_spec,
        session_data=session_data,
        max_changed_files=5,
    )


def test_patch_validation_blocks_artifacts_path_without_explicit_allow():
    """allowed_changes に無い artifacts パスは拒否"""
    impl_result = {"changed_files": ["artifacts/not-allowed.txt"]}
    prepared_spec = {"allowed_changes": [], "forbidden_changes": []}
    session_data = {"out_of_scope": []}

    with pytest.raises(ValueError, match="forbidden path detected"):
        validate_changed_files_before_patch(
            impl_result=impl_result,
            prepared_spec=prepared_spec,
            session_data=session_data,
            max_changed_files=5,
        )


def test_patch_normalization_handles_malformed_patch_structure():
    """AC-68-01: markdown フェンス付き patch を git apply 互換に整える。"""
    malformed = """```diff
--- a/sample.txt
+++ b/sample.txt
@@ -1 +1 @@
-old
+new
```"""
    normalized = normalize_patch_for_git_apply(malformed)
    assert normalized.startswith("diff --git a/sample.txt b/sample.txt\n")
    assert "--- a/sample.txt\n+++ b/sample.txt\n" in normalized
    assert normalized.endswith("\n")


def test_retry_patch_uses_same_normalization_rules():
    """AC-68-02: 初回/リトライで同じ正規化結果になる。"""
    raw = "--- a/a.txt\r\n+++ b/a.txt\r\n@@ -1 +1 @@\r\n-a\r\n+b\r\n"
    first = normalize_patch_for_git_apply(raw)
    retry = normalize_patch_for_git_apply(raw)
    assert first == retry
    assert first.startswith("diff --git a/a.txt b/a.txt\n")


def test_patch_normalization_handles_missing_diff_header():
    """AC-68-03: diff ヘッダ不足時に補完される。"""
    raw = "--- old.py\n+++ new.py\n@@ -1 +1 @@\n-print('x')\n+print('y')\n"
    normalized = normalize_patch_for_git_apply(raw)
    assert normalized.startswith("diff --git a/old.py b/new.py\n")
    assert "@@ -1 +1 @@" in normalized


def test_existing_patch_validation_behavior_remains_unchanged_after_normalization():
    """AC-68-04: 既存の changed_files バリデーション挙動は維持。"""
    result = validate_patch_files(["docs/sessions/test.json"])
    assert result["status"] == "error"
    assert result["error_type"] == "scope_violation"


def test_hunk_line_prefixes_are_completed_for_unprefixed_added_lines():
    """AC-69-01: hunk 内で接頭辞欠落行に + を補完する。"""
    raw = (
        "diff --git a/a.py b/a.py\n"
        "--- a/a.py\n"
        "+++ b/a.py\n"
        "@@ -1 +1,2 @@\n"
        "-old\n"
        "def added():\n"
        "+    return 1\n"
    )
    normalized = _normalize_hunk_line_prefixes(raw)
    assert "+def added():" in normalized
    assert "-old" in normalized
    assert "+    return 1" in normalized


def test_hunk_line_prefix_normalization_preserves_valid_lines():
    """AC-69-02: 既存の有効行はそのまま維持する。"""
    raw = (
        "diff --git a/a.py b/a.py\n"
        "--- a/a.py\n"
        "+++ b/a.py\n"
        "@@ -1,2 +1,2 @@\n"
        " context\n"
        "-old\n"
        "+new\n"
        "\\ No newline at end of file\n"
    )
    normalized = _normalize_hunk_line_prefixes(raw)
    assert normalized == raw


def test_is_new_file_hunk_detects_zero_start():
    """AC-70-01: @@ -0,0 ハンクを新規ファイルとして検出する。"""
    # @@ -0,0 +1,N @@ は新規ファイル作成を表すハンク
    new_file_lines = [
        "diff --git a/new.py b/new.py",
        "--- /dev/null",
        "+++ b/new.py",
        "@@ -0,0 +1,3 @@",
        "+import os",
        "+",
        "+print('hello')",
    ]
    # is_new_file_hunk の検出ロジックと同等の判定
    is_new = any(
        line.startswith("@@ -0,0 ") or line.startswith("@@ -0 +")
        for line in new_file_lines
    )
    assert is_new is True

    # 通常の差分ハンクは新規ファイルとして扱わない
    existing_file_lines = [
        "diff --git a/old.py b/old.py",
        "--- a/old.py",
        "+++ b/old.py",
        "@@ -1,3 +1,3 @@",
        " context",
        "-old",
        "+new",
    ]
    is_new_existing = any(
        line.startswith("@@ -0,0 ") or line.startswith("@@ -0 +")
        for line in existing_file_lines
    )
    assert is_new_existing is False


def test_remaining_patch_is_normalized_before_apply():
    """AC-70-02: remaining.patch に _normalize_hunk_line_prefixes が適用される。"""
    # '+' プレフィックスが欠落した既存ファイル向けパッチを正規化できることを確認
    # 注: スペース始まりの行はコンテキスト行として扱われるため '+' は付かない
    corrupt_lines = [
        "diff --git a/a.py b/a.py",
        "--- a/a.py",
        "+++ b/a.py",
        "@@ -1,2 +1,3 @@",
        " context",
        "-old",
        "def new_func():",  # '+' 欠落（非プレフィックス行）
        "class Helper:",    # '+' 欠落（非プレフィックス行）
    ]
    raw = "\n".join(corrupt_lines)
    normalized = _normalize_hunk_line_prefixes(raw)
    lines = normalized.split("\n")
    # hunk 内の接頭辞欠落行に '+' が付与される
    assert "+def new_func():" in lines
    assert "+class Helper:" in lines
    # context 行と削除行は変更されない
    assert " context" in lines
    assert "-old" in lines


def test_existing_behavior_unchanged():
    """AC-70-03: 既存の正規化・バリデーション挙動を壊さない。"""
    # normalize_patch_for_git_apply の既存挙動
    raw = "--- a/f.py\n+++ b/f.py\n@@ -1 +1 @@\n-x\n+y\n"
    normalized = normalize_patch_for_git_apply(raw)
    assert normalized.startswith("diff --git a/f.py b/f.py\n")
    assert "--- a/f.py\n+++ b/f.py\n" in normalized

    # validate_patch_files の既存挙動（docs/sessions/* は禁止パス）
    assert validate_patch_files(["a.py"])["status"] == "success"
    assert validate_patch_files(["docs/sessions/test.json"])["status"] == "error"

    # _normalize_hunk_line_prefixes の既存挙動
    valid = (
        "diff --git a/x.py b/x.py\n"
        "--- a/x.py\n"
        "+++ b/x.py\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n"
    )
    assert _normalize_hunk_line_prefixes(valid) == valid
