"""path_mode classifier の単体テスト。

判定ロジックを純関数として検証する (subprocess 不使用)。
"""
from __future__ import annotations

import pytest
from typing import Any, Dict

from orchestration.path_mode.classifier import classify_path_mode


# ---------------------------------------------------------------------------
# テスト用ヘルパー
# ---------------------------------------------------------------------------

def _session(overrides: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """最小有効セッションを生成し、overrides をマージして返す。"""
    base: Dict[str, Any] = {
        "session_id": "session-202",
        "phase_id": "phase-a",
        "title": "テストセッション",
        "goal": "テスト完了",
        "scope": ["orchestration/path_mode/"],
        "out_of_scope": ["selector/"],
        "constraints": ["sandbox-first"],
        "acceptance_ref": "docs/acceptance/session-202.yaml",
        "allowed_changes_detail": [
            "orchestration/path_mode/classifier.py"
        ],
        "forbidden_changes": ["selector/", "run_session.py"],
        "completion_criteria": "4-gate PASS",
        "acceptance_criteria": [{"id": "AC-01", "test_name": "test_fast_docs_only"}],
        "review_points": [
            "仕様一致（AC達成）",
            "変更範囲遵守",
            "副作用なし",
            "検証十分性",
        ],
        "failure_type": "implementation_error",
    }
    if overrides:
        base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Fast Path テスト
# ---------------------------------------------------------------------------

def test_fast_docs_only_scope() -> None:
    """scope に docs-only があれば fast を返す。"""
    session = _session({"scope": ["docs-only"], "allowed_changes_detail": ["docs/x.md"]})
    assert classify_path_mode(session) == "fast"


def test_fast_single_file_allowed() -> None:
    """allowed_changes_detail が1ファイルのみなら fast を返す。"""
    session = _session({"allowed_changes_detail": ["orchestration/path_mode/classifier.py"]})
    assert classify_path_mode(session) == "fast"


def test_fast_zero_files_allowed() -> None:
    """allowed_changes_detail が空リストは ValueError。"""
    session = _session({"allowed_changes_detail": []})
    with pytest.raises(ValueError, match="allowed_changes_detail"):
        classify_path_mode(session)


def test_fast_docs_only_keyword_variation() -> None:
    """'docs only'（ハイフンなし）も fast と判定する。"""
    session = _session({"scope": ["docs only"], "allowed_changes_detail": ["README.md"]})
    assert classify_path_mode(session) == "fast"


def test_fast_japanese_doc_keyword() -> None:
    """日本語スコープ 'ドキュメントのみ' は fast を返す。"""
    session = _session({"scope": ["ドキュメントのみ"], "allowed_changes_detail": ["doc.md"]})
    assert classify_path_mode(session) == "fast"


# ---------------------------------------------------------------------------
# Formal Path テスト
# ---------------------------------------------------------------------------

def test_formal_multiple_files() -> None:
    """allowed_changes_detail が2ファイル以上なら formal を返す。"""
    session = _session({
        "allowed_changes_detail": [
            "orchestration/path_mode/classifier.py",
            "orchestration/path_mode/policy.py",
        ]
    })
    assert classify_path_mode(session) == "formal"


def test_formal_implementation_change() -> None:
    """scope に実装変更を示す文字列があれば formal を返す。"""
    session = _session({
        "scope": ["新規モジュール実装"],
        "allowed_changes_detail": ["orchestration/newmod.py", "backend/tests/test_newmod.py"],
    })
    assert classify_path_mode(session) == "formal"


def test_formal_three_files() -> None:
    """3ファイル変更は formal。"""
    session = _session({
        "allowed_changes_detail": ["a.py", "b.py", "c.py"],
    })
    assert classify_path_mode(session) == "formal"


def test_formal_no_emergency_no_fast() -> None:
    """emergency / fast 条件を満たさない最小構成は formal。"""
    session = _session({
        "scope": ["backend/module/"],
        "allowed_changes_detail": ["backend/module/core.py", "backend/module/__init__.py"],
    })
    assert classify_path_mode(session) == "formal"


# ---------------------------------------------------------------------------
# Emergency Path テスト
# ---------------------------------------------------------------------------

def test_emergency_hotfix_title() -> None:
    """title に hotfix があれば emergency。"""
    session = _session({
        "title": "hotfix: 決済バグ緊急修正",
        "allowed_changes_detail": ["app/payment.py", "backend/tests/test_payment.py"],
    })
    assert classify_path_mode(session) == "emergency"


def test_emergency_production_scope() -> None:
    """scope に production があれば emergency。"""
    session = _session({
        "scope": ["production DB直結修正"],
        "allowed_changes_detail": ["app/db.py", "app/fix.py"],
    })
    assert classify_path_mode(session) == "emergency"


def test_emergency_japanese_keyword() -> None:
    """scope に '緊急' があれば emergency。"""
    session = _session({
        "scope": ["緊急対応"],
        "allowed_changes_detail": ["app/urgent.py", "app/fix.py"],
    })
    assert classify_path_mode(session) == "emergency"


def test_emergency_critical_title() -> None:
    """title に critical があれば emergency。"""
    session = _session({
        "title": "critical: セキュリティパッチ適用",
        "allowed_changes_detail": ["app/auth.py", "backend/tests/test_auth.py"],
    })
    assert classify_path_mode(session) == "emergency"


def test_emergency_takes_priority_over_single_file() -> None:
    """emergency キーワードがあれば1ファイルでも emergency（emergency > fast）。"""
    session = _session({
        "scope": ["hotfix"],
        "allowed_changes_detail": ["app/fix.py"],
    })
    assert classify_path_mode(session) == "emergency"


# ---------------------------------------------------------------------------
# バリデーション エラーテスト
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("missing_key", [
    "session_id",
    "phase_id",
    "title",
    "goal",
    "scope",
    "out_of_scope",
    "constraints",
    "acceptance_ref",
    "allowed_changes_detail",
    "forbidden_changes",
    "completion_criteria",
    "acceptance_criteria",
    "review_points",
    "failure_type",
])
def test_missing_required_key_raises(missing_key: str) -> None:
    """必須14キーのいずれかが欠けると ValueError。"""
    session = _session()
    del session[missing_key]
    with pytest.raises(ValueError, match=missing_key):
        classify_path_mode(session)


def test_empty_allowed_changes_detail_string_raises() -> None:
    """allowed_changes_detail が空文字でも ValueError。"""
    session = _session({"allowed_changes_detail": ""})
    with pytest.raises(ValueError, match="allowed_changes_detail"):
        classify_path_mode(session)
