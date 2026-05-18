"""hook ファイルと CLAUDE.md の制約を突合し、矛盾を検出する"""

import os
from typing import Dict, List

from .constants import COMMAND_SEVERITY, SAFE_BRANCH_PREFIXES
from .parser import parse_claude_md_constraints, parse_hook_demands


def check_conflicts(
    claude_md_path: str,
    hooks_dir: str,
) -> List[Dict[str, str]]:
    """
    CLAUDE.md の禁止制約と hooks/ 配下のスクリプトを照合し、矛盾リストを返す。

    戻り値:
        [
          {
            "hook_file": "post_push.sh",
            "command": "git push",
            "reason": "CLAUDE.md §4.1 が git push を禁止",
            "severity": "critical",
            "branch_exclusion_applies": "False",
          },
          ...
        ]
    矛盾がなければ空リスト。
    """
    constraints = parse_claude_md_constraints(claude_md_path)
    forbidden = set(constraints.get("forbidden_git", []))
    branch_exclusions = constraints.get("branch_exclusions", []) or list(SAFE_BRANCH_PREFIXES)

    conflicts: List[Dict[str, str]] = []

    hook_files = _collect_hook_files(hooks_dir)
    for hook_path in hook_files:
        demands = parse_hook_demands(hook_path)
        hook_name = os.path.basename(hook_path)

        for demand in demands:
            if demand not in forbidden:
                continue

            # ブランチ除外パターンが hook 内に記述されているか確認
            exclusion_applies = _hook_has_branch_exclusion(hook_path, branch_exclusions)

            conflicts.append(
                {
                    "hook_file": hook_name,
                    "command": demand,
                    "reason": f"CLAUDE.md §4.1 が {demand!r} を禁止",
                    "severity": COMMAND_SEVERITY.get(demand, "medium"),
                    "branch_exclusion_applies": str(exclusion_applies),
                }
            )

    return conflicts


# ── private helpers ──────────────────────────────────────────────────────────

def _collect_hook_files(hooks_dir: str) -> List[str]:
    """hooks_dir 配下の .sh ファイルを列挙する (proposals サブディレクトリは除外)。"""
    result: List[str] = []
    if not os.path.isdir(hooks_dir):
        return result
    for entry in sorted(os.listdir(hooks_dir)):
        full = os.path.join(hooks_dir, entry)
        if os.path.isfile(full) and entry.endswith(".sh"):
            result.append(full)
    return result


def _hook_has_branch_exclusion(hook_path: str, exclusions: List[str]) -> bool:
    """hook スクリプトがブランチ除外ガードを含んでいれば True。"""
    with open(hook_path, encoding="utf-8") as f:
        content = f.read()
    for prefix in exclusions:
        # "sandbox/*" or 'claude/*' のようなガードが含まれるかチェック
        safe_prefix = prefix.rstrip("/")
        if safe_prefix in content:
            return True
    return False
