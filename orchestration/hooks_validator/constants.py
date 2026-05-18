"""hooks_validator 既知の禁止操作リスト"""

from typing import Dict, List

# CLAUDE.md §4.1 に基づく禁止 git 操作パターン
FORBIDDEN_GIT_COMMANDS: List[str] = [
    "git push",
    "git push --force",
    "git reset --hard",
    "git add .",
    "git add -A",
    "git stash pop",
    "git stash drop",
    "git stash apply",
]

# sandbox/claude/* ブランチは push 要求不要
SAFE_BRANCH_PREFIXES: List[str] = [
    "sandbox/",
    "claude/",
]

# main/master は push 禁止対象ブランチ
PROTECTED_BRANCHES: List[str] = [
    "main",
    "master",
]

# CLAUDE.md §4 から抽出した制約セクション見出しパターン
CONSTRAINT_SECTION_HEADERS: List[str] = [
    "4.1",
    "4.2",
    "4.3",
    "4.4",
    "4.5",
    "4.6",
    "絶対禁則",
    "forbidden actions",
]

# severity レベル定義
SEVERITY_LEVELS: Dict[str, int] = {
    "critical": 3,  # main branch push、production DB アクセス
    "high": 2,      # force push、hard reset
    "medium": 1,    # git add -A、stash 操作
}

# 操作ごとの severity マッピング
COMMAND_SEVERITY: Dict[str, str] = {
    "git push": "critical",
    "git push --force": "critical",
    "git reset --hard": "high",
    "git add .": "medium",
    "git add -A": "medium",
    "git stash pop": "medium",
    "git stash drop": "medium",
    "git stash apply": "medium",
}
