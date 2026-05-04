"""Lock Manager: 同一 session_id の二重実行を防ぐ in-memory 最小実装。

- single-thread 前提（thread safety なし）
- 分散ロック・timeout 機構は scope 外
"""
from __future__ import annotations

_locks: dict[str, bool] = {}


def acquire_lock(key: str) -> bool:
    """ロックを取得する。既に取得済みなら False を返す。"""
    if _locks.get(key):
        return False
    _locks[key] = True
    return True


def release_lock(key: str) -> None:
    """ロックを解放する。未取得キーへの呼出は no-op。"""
    _locks.pop(key, None)
