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
