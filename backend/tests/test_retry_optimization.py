"""session-102: retry最適化（既存改善）の追加テスト。"""

from __future__ import annotations

from orchestration.run_session import (
    VALID_FAILURE_TYPES,
    _compute_retry_cause_fingerprint,
    classify_failure,
    classify_failure_type,
    resolve_canonical_failure_type,
    retry_loop,
)


def test_failure_type_normalized() -> None:
    """failure_type が常に enum（VALID_FAILURE_TYPES）に正規化されること。"""
    checks = {
        "test": {"status": "failed", "stderr": "AssertionError: x", "stdout": ""},
        "lint": {"status": "skipped"},
        "typecheck": {"status": "skipped"},
        "build": {"status": "skipped"},
        "success": False,
    }
    canonical = resolve_canonical_failure_type(checks)
    assert canonical["failure_type"] in VALID_FAILURE_TYPES

    failure = classify_failure(checks)
    assert failure["failure_type"] in VALID_FAILURE_TYPES


def test_same_cause_detection() -> None:
    """同一 fingerprint が2回連続した場合に retry_loop が停止すること。"""
    history = [
        {"attempt": 1, "failure_type": "type_mismatch", "cause_summary": "old", "cause_fingerprint": "deadbeef"}
    ]
    failure = {"failure_type": "test_failure", "cause_summary": "new", "cause_fingerprint": "deadbeef"}
    out = retry_loop(retry_history=history, failure=failure, retry_count=1, max_retries=5)
    assert out["should_retry"] is False
    assert out["stop_reason"] == "cause_fingerprint_repeated"


def test_retry_limit() -> None:
    """retry 上限で停止すること。"""
    out = retry_loop(
        retry_history=[],
        failure={"failure_type": "test_failure", "cause_summary": "x", "cause_fingerprint": "fp"},
        retry_count=2,
        max_retries=2,
    )
    assert out["should_retry"] is False
    assert out["stop_reason"] == "max_retries_reached"


def test_no_regression() -> None:
    """既存の分類・fingerprint・retry_loopの基本仕様を壊さない（スモーク）。"""
    # 旧互換の classify_failure_type は維持
    legacy = classify_failure_type(
        {
            "build": {"status": "failed"},
            "typecheck": {"status": "failed"},
            "lint": {"status": "failed"},
            "test": {"status": "failed"},
        }
    )
    assert legacy["failure_type"] == "build_failure"
    assert legacy["priority"] == 4

    # fingerprint は安定した短い文字列
    fp = _compute_retry_cause_fingerprint(
        {
            "test": {"status": "failed", "stderr": "AssertionError: expected 1 got 2", "stdout": ""},
            "lint": {"status": "skipped"},
            "typecheck": {"status": "skipped"},
            "build": {"status": "skipped"},
            "success": False,
        }
    )
    assert isinstance(fp, str)
    assert len(fp) == 16