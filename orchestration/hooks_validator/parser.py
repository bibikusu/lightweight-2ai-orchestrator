"""CLAUDE.md / hook ファイルから制約・要求を抽出するパーサー"""

import re
from typing import Dict, List

from .constants import FORBIDDEN_GIT_COMMANDS


def parse_claude_md_constraints(path: str) -> Dict[str, List[str]]:
    """
    CLAUDE.md を解析し、禁止操作リストを返す。

    戻り値:
        {
          "forbidden_git": ["git push", "git add .", ...],
          "protected_branches": ["main", "master", ...],
          "branch_exclusions": ["sandbox/", "claude/", ...],
        }
    """
    with open(path, encoding="utf-8") as f:
        content = f.read()

    return {
        "forbidden_git": _extract_forbidden_git(content),
        "protected_branches": _extract_protected_branches(content),
        "branch_exclusions": _extract_branch_exclusions(content),
    }


def parse_hook_demands(hook_path: str) -> List[str]:
    """
    hook スクリプトを解析し、実行を要求する git コマンドリストを返す。

    コメント行・空行はスキップ。
    複数行コマンドも結合して評価する。
    """
    with open(hook_path, encoding="utf-8") as f:
        lines = f.readlines()

    demands: List[str] = []
    continuation = ""

    for raw_line in lines:
        # コメント行をスキップ
        stripped = raw_line.rstrip()
        code_part = _strip_comment(stripped)

        # 行継続 (バックスラッシュ) の処理
        if code_part.endswith("\\"):
            continuation += code_part[:-1].strip() + " "
            continue

        full_line = (continuation + code_part).strip()
        continuation = ""

        if not full_line:
            continue

        matched = _match_git_demands(full_line)
        demands.extend(matched)

    return demands


# ── private helpers ──────────────────────────────────────────────────────────

def _strip_comment(line: str) -> str:
    """シェルコメント (#) 以降を除去する。"""
    # 行頭コメントは全除去
    if re.match(r"^\s*#", line):
        return ""
    # インラインコメント除去 (簡易: # 以降を削除)
    idx = line.find(" #")
    if idx != -1:
        return line[:idx].rstrip()
    return line


def _match_git_demands(line: str) -> List[str]:
    """行に含まれる禁止対象 git コマンドを返す。"""
    found: List[str] = []
    for cmd in FORBIDDEN_GIT_COMMANDS:
        # コマンドが行に含まれているかをワード境界で確認
        pattern = re.escape(cmd)
        if re.search(pattern, line):
            found.append(cmd)
    return found


def _extract_forbidden_git(content: str) -> List[str]:
    """CLAUDE.md のコードブロック・箇条書きから禁止 git コマンドを抽出。"""
    found: List[str] = []
    for cmd in FORBIDDEN_GIT_COMMANDS:
        if cmd in content:
            found.append(cmd)
    return found


def _extract_protected_branches(content: str) -> List[str]:
    """CLAUDE.md から保護ブランチ名を抽出。"""
    branches: List[str] = []
    # "main" ブランチへの直接 commit 禁止 などのパターン
    patterns = [
        r"`(main|master)`\s*ブランチ",
        r"branch[:\s]+`?(main|master)`?",
        r"(main|master)\s*branch",
    ]
    for pat in patterns:
        for m in re.finditer(pat, content, re.IGNORECASE):
            branch = m.group(1).lower()
            if branch not in branches:
                branches.append(branch)
    return branches


def _extract_branch_exclusions(content: str) -> List[str]:
    """CLAUDE.md から push 要求除外ブランチプレフィックスを抽出。"""
    exclusions: List[str] = []
    # sandbox/ / claude/ などのプレフィックスを抽出
    pattern = r"(sandbox|claude)/\*"
    for m in re.finditer(pattern, content):
        prefix = m.group(0).replace("*", "")  # "sandbox/" or "claude/"
        if prefix not in exclusions:
            exclusions.append(prefix)
    return exclusions
