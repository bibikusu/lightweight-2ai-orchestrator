"""hook_eval_helper: hook test false-positive 判定 helper.

session-171f-pre 仕様に基づく実装:
- HEAD == origin/main → false_positive = False
- HEAD != origin/main かつ changed_files が allowed_changes に全包含 → True
- HEAD != origin/main かつ allowed_changes 外の変更を含む → False (scope violation)
"""
from __future__ import annotations

import subprocess
import sys
from typing import Dict, List, Optional


def get_changed_files() -> List[str]:
    """origin/main との差分ファイル一覧を返す。"""
    proc = subprocess.run(
        ["git", "diff", "--name-only", "origin/main"],
        capture_output=True,
        text=True,
        check=False,
    )
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def is_head_synced() -> bool:
    """HEAD が origin/main と同一かを返す。origin/main 未解決時は True (neutral skip) を返す。"""
    try:
        head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
    except subprocess.CalledProcessError:
        print("[hook_eval_helper] WARNING: HEAD 解決失敗 — neutral skip", file=sys.stderr)
        return True
    try:
        origin = subprocess.check_output(
            ["git", "rev-parse", "origin/main"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
    except subprocess.CalledProcessError:
        print("[hook_eval_helper] WARNING: origin/main 未解決 — neutral skip", file=sys.stderr)
        return True
    return head == origin


def is_false_positive(
    changed_files: List[str],
    allowed_changes: List[str],
    head_synced: bool,
) -> bool:
    """false-positive 判定 (pure 関数, 副作用なし)。

    Args:
        changed_files: origin/main からの変更ファイル一覧
        allowed_changes: current session の allowed_changes 一覧
        head_synced: HEAD == origin/main か

    Returns:
        True なら false-positive (push 後に解消する見込みの hook test 失敗)、
        False なら real failure (scope violation または HEAD 同期済み)
    """
    if head_synced:
        return False
    if not changed_files:
        return False
    return all(f in allowed_changes for f in changed_files)


def evaluate(
    allowed_changes: Optional[List[str]] = None,
    changed_files: Optional[List[str]] = None,
    head_synced: Optional[bool] = None,
) -> Dict:
    """評価結果を dict で返す。引数省略時は git から取得。"""
    files = changed_files if changed_files is not None else get_changed_files()
    synced = head_synced if head_synced is not None else is_head_synced()
    allowed = allowed_changes if allowed_changes is not None else []

    fp = is_false_positive(files, allowed, synced)

    if synced:
        reason = "head_synced"
    elif fp:
        reason = "diff vs origin/main only, all files within allowed_changes"
    elif not files:
        reason = "no diff"
    else:
        outside = [f for f in files if f not in allowed]
        reason = f"scope violation: {outside}"

    return {
        "is_false_positive": fp,
        "changed_files": files,
        "reason": reason,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(evaluate(), ensure_ascii=False, indent=2))
    sys.exit(0)
