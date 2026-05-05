"""tests/test_hook_eval_helper.py: scripts/hook_eval_helper.py のユニットテスト."""
from __future__ import annotations

import re
from pathlib import Path

from scripts.hook_eval_helper import (
    evaluate,
    get_changed_files,
    is_false_positive,
    is_head_synced,
)


# ────────────────────────────────────────
# AC-171F-01: exports
# ────────────────────────────────────────
def test_hook_eval_helper_exports() -> None:
    assert callable(get_changed_files)
    assert callable(is_head_synced)
    assert callable(is_false_positive)
    assert callable(evaluate)


# ────────────────────────────────────────
# AC-171F-02: head_synced=True → False
# ────────────────────────────────────────
def test_is_false_positive_returns_false_when_head_synced() -> None:
    assert is_false_positive(["x.py"], ["x.py"], head_synced=True) is False
    assert is_false_positive([], [], head_synced=True) is False
    assert is_false_positive(
        ["a.py", "b.py"], ["a.py", "b.py"], head_synced=True
    ) is False


# ────────────────────────────────────────
# AC-171F-03: head_synced=False, all in allowed → True
# ────────────────────────────────────────
def test_is_false_positive_true_when_within_allowed_changes() -> None:
    allowed = [
        "scripts/hook_eval_helper.py",
        "tests/test_hook_eval_helper.py",
        "docs/sessions/session-171f.json",
        "docs/acceptance/session-171f.yaml",
    ]
    changed = [
        "scripts/hook_eval_helper.py",
        "tests/test_hook_eval_helper.py",
    ]
    assert is_false_positive(changed, allowed, head_synced=False) is True


# ────────────────────────────────────────
# AC-171F-04: scope violation → False
# ────────────────────────────────────────
def test_is_false_positive_false_when_scope_violation() -> None:
    allowed = ["scripts/hook_eval_helper.py"]
    changed_with_violation = [
        "scripts/hook_eval_helper.py",
        "orchestration/run_session.py",
    ]
    assert is_false_positive(changed_with_violation, allowed, head_synced=False) is False

    # empty changed_files in unsync state → also False (no diff to classify)
    assert is_false_positive([], allowed, head_synced=False) is False


# ────────────────────────────────────────
# AC-171F-05: evaluate() schema
# ────────────────────────────────────────
def test_evaluate_returns_expected_schema() -> None:
    result = evaluate(
        allowed_changes=["scripts/hook_eval_helper.py"],
        changed_files=["scripts/hook_eval_helper.py"],
        head_synced=False,
    )
    assert set(result.keys()) == {"is_false_positive", "changed_files", "reason"}
    assert result["is_false_positive"] is True
    assert result["changed_files"] == ["scripts/hook_eval_helper.py"]
    assert isinstance(result["reason"], str)

    # scope violation case
    result2 = evaluate(
        allowed_changes=["scripts/hook_eval_helper.py"],
        changed_files=["scripts/hook_eval_helper.py", "orchestration/x.py"],
        head_synced=False,
    )
    assert result2["is_false_positive"] is False
    assert "scope violation" in result2["reason"]

    # head_synced case
    result3 = evaluate(
        allowed_changes=["x"], changed_files=["x"], head_synced=True
    )
    assert result3["is_false_positive"] is False
    assert result3["reason"] == "head_synced"


# ────────────────────────────────────────
# AC-171F-06: helper isolation (no orchestration / tests/hooks import)
# ────────────────────────────────────────
def test_hook_eval_helper_isolation() -> None:
    src = Path("scripts/hook_eval_helper.py").read_text()
    forbidden_patterns = [
        r"from orchestration",
        r"^import orchestration",
        r"from tests\.hooks",
        r"from \.\.tests\.hooks",
    ]
    for pattern in forbidden_patterns:
        assert not re.search(pattern, src, re.MULTILINE), (
            f"forbidden import found: {pattern}"
        )
