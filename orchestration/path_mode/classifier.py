"""session.json → PathMode 判定器。

判定優先順位:
  1. Emergency: scope / title / goal にキーワードあり
  2. Fast:      docs-only / 1ファイル以下 / scope狭
  3. Formal:    それ以外
"""
from __future__ import annotations

from typing import Any, Dict, Literal

from orchestration.path_mode.constants import (
    EMERGENCY_SCOPE_KEYWORDS,
    EMERGENCY_TITLE_KEYWORDS,
    FAST_MAX_ALLOWED_FILES,
    FAST_SCOPE_KEYWORDS,
    PATH_MODE_EMERGENCY,
    PATH_MODE_FAST,
    PATH_MODE_FORMAL,
    REQUIRED_SESSION_KEYS,
)

PathMode = Literal["fast", "formal", "emergency"]


def _validate(session: Dict[str, Any]) -> None:
    """必須14キーの存在と allowed_changes_detail の非空を検証する。"""
    for key in REQUIRED_SESSION_KEYS:
        if key not in session:
            raise ValueError(f"session missing required key: {key!r}")
    acd = session.get("allowed_changes_detail")
    if acd is None or (isinstance(acd, (list, dict, str)) and len(acd) == 0):
        raise ValueError("allowed_changes_detail must not be empty")


def _is_emergency(session: Dict[str, Any]) -> bool:
    """scope / title / goal に emergency キーワードがあるか検査する。"""
    scope_items: list[str] = session.get("scope", []) or []
    scope_text = " ".join(str(s).lower() for s in scope_items)
    for kw in EMERGENCY_SCOPE_KEYWORDS:
        if kw.lower() in scope_text:
            return True

    title = str(session.get("title", "")).lower()
    goal = str(session.get("goal", "")).lower()
    combined = title + " " + goal
    for kw in EMERGENCY_TITLE_KEYWORDS:
        if kw.lower() in combined:
            return True
    return False


def _is_fast(session: Dict[str, Any]) -> bool:
    """docs-only / 1ファイル以下の変更であるかを検査する。"""
    scope_items: list[str] = session.get("scope", []) or []
    scope_text = " ".join(str(s).lower() for s in scope_items)
    for kw in FAST_SCOPE_KEYWORDS:
        if kw.lower() in scope_text:
            return True

    acd = session.get("allowed_changes_detail", [])
    if isinstance(acd, list) and len(acd) <= FAST_MAX_ALLOWED_FILES:
        return True
    return False


def classify_path_mode(session: Dict[str, Any]) -> PathMode:
    """session.json を受け取り PathMode を返す。

    Returns:
        "fast" | "formal" | "emergency"
    Raises:
        ValueError: 必須キー欠落 / allowed_changes_detail が空の場合
    """
    _validate(session)

    if _is_emergency(session):
        return PATH_MODE_EMERGENCY
    if _is_fast(session):
        return PATH_MODE_FAST
    return PATH_MODE_FORMAL
