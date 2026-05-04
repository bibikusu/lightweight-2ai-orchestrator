"""Lock Manager semantics テスト (session-171 AC-171-01〜03 対応)。"""
import pytest
from orchestration.lock.manager import acquire_lock, release_lock, _locks


@pytest.fixture(autouse=True)
def _clear_locks():
    """各テスト前後に _locks を初期化して test 間汚染を防ぐ。"""
    _locks.clear()
    yield
    _locks.clear()


def test_acquire_lock_returns_true_on_first_acquire():
    """AC-171-01: acquire_lock(key: str) -> bool の interface 確認 + 初回取得は True。"""
    result = acquire_lock("session-171")
    assert result is True


def test_acquire_lock_returns_false_on_double_acquire():
    """AC-171-03: 二重 acquire 不可 — 2 回目は False。"""
    acquire_lock("session-171")
    result = acquire_lock("session-171")
    assert result is False


def test_release_then_reacquire_returns_true():
    """AC-171-03: release 後再 acquire 可 — release_lock(key: str) -> None の interface 確認。"""
    acquire_lock("session-171")
    release_lock("session-171")
    result = acquire_lock("session-171")
    assert result is True


def test_release_unlocked_key_is_noop():
    """AC-171-02: 未取得キーへの release_lock は例外を送出しない (no-op)。"""
    release_lock("session-never-acquired")
