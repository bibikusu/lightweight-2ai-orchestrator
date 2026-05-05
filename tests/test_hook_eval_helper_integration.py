"""tests/test_hook_eval_helper_integration.py: hook wrapper 統合テスト (session-171h)."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path


HELPER_PATH = "scripts/hook_eval_helper.py"
PRE_PUSH_PATH = Path("scripts/git-hooks/pre-push")
CI_WORKFLOW_PATH = Path(".github/workflows/hook-eval-helper.yml")
POST_PUSH_PATH = Path(".claude/hooks/post_push.sh")

# hook 側で実装を禁止された判定パターン
FORBIDDEN_PATTERNS = [
    r"git\s+rev-parse\s+origin/main",
    r"git\s+diff\s+--name-only",
    r"allowed_changes",
    r"is_false_positive",
    r"head_synced",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ────────────────────────────────────────
# AC-171H-01: pre-push wrapper の存在と helper 参照
# ────────────────────────────────────────
def test_pre_push_wrapper_invokes_hook_eval_helper() -> None:
    assert PRE_PUSH_PATH.exists(), f"{PRE_PUSH_PATH} が存在しない"
    content = _read(PRE_PUSH_PATH)
    assert HELPER_PATH in content, "pre-push が scripts/hook_eval_helper.py を参照していない"


# ────────────────────────────────────────
# AC-171H-02: CI workflow の存在と helper 実行定義
# ────────────────────────────────────────
def test_ci_workflow_runs_hook_eval_helper_cli() -> None:
    assert CI_WORKFLOW_PATH.exists(), f"{CI_WORKFLOW_PATH} が存在しない"
    content = _read(CI_WORKFLOW_PATH)
    assert HELPER_PATH in content, "CI workflow が scripts/hook_eval_helper.py を参照していない"


# ────────────────────────────────────────
# AC-171H-03: Claude hook wrapper の存在と helper 参照
# ────────────────────────────────────────
def test_claude_post_push_wrapper_invokes_helper() -> None:
    assert POST_PUSH_PATH.exists(), f"{POST_PUSH_PATH} が存在しない"
    content = _read(POST_PUSH_PATH)
    assert HELPER_PATH in content, "post_push.sh が scripts/hook_eval_helper.py を参照していない"


# ────────────────────────────────────────
# AC-171H-04: helper 本体に変更なし
# ────────────────────────────────────────
def test_hook_eval_helper_file_unchanged() -> None:
    proc = subprocess.run(
        ["git", "diff", "--name-only", "--", HELPER_PATH],
        capture_output=True,
        text=True,
        check=False,
    )
    diff = proc.stdout.strip()
    assert diff == "", f"scripts/hook_eval_helper.py に変更が検出された: {diff}"


# ────────────────────────────────────────
# AC-171H-05: allowed_changes 外に diff なし
# ────────────────────────────────────────
def test_changed_files_within_allowed_changes() -> None:
    allowed = {
        "scripts/git-hooks/pre-push",
        ".github/workflows/hook-eval-helper.yml",
        ".claude/hooks/post_push.sh",
        "tests/test_hook_eval_helper_integration.py",
    }
    proc = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    changed = {f for f in proc.stdout.splitlines() if f.strip()}
    outside = changed - allowed
    assert not outside, f"allowed_changes 外のファイルが変更されている: {outside}"


# ────────────────────────────────────────
# AC-171H-06: helper CLI smoke test (exit 0)
# ────────────────────────────────────────
def test_four_gate_and_helper_cli_smoke_pass() -> None:
    import sys
    proc = subprocess.run(
        [sys.executable, HELPER_PATH],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"helper CLI smoke test 失敗: exit={proc.returncode}\n{proc.stderr}"
    import json
    result = json.loads(proc.stdout)
    assert "is_false_positive" in result
    assert "changed_files" in result
    assert "reason" in result


# ────────────────────────────────────────
# AC-171H-07: hook wrapper が false_positive 判定ロジックを再実装していない
# ────────────────────────────────────────
def test_hook_wrapper_does_not_reimplement_false_positive_logic() -> None:
    hook_files = [PRE_PUSH_PATH, POST_PUSH_PATH]
    for hook_file in hook_files:
        content = _read(hook_file)
        for pattern in FORBIDDEN_PATTERNS:
            assert not re.search(pattern, content), (
                f"{hook_file} に禁止パターン '{pattern}' が含まれている"
            )
