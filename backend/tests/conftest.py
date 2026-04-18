from pathlib import Path
from typing import List

import pytest
from unittest.mock import patch

import orchestration.run_session as _phase12_rs

# Git command mock registry with default responses
GIT_COMMAND_REGISTRY = {
    'status': {'returncode': 0, 'stdout': 'On branch main\nnothing to commit, working tree clean\n', 'stderr': ''},
    'branch': {'returncode': 0, 'stdout': '* main\n', 'stderr': ''},
    'log': {'returncode': 0, 'stdout': 'commit abc123\nAuthor: Test User\n\n    Initial commit\n', 'stderr': ''},
    'diff': {'returncode': 0, 'stdout': '', 'stderr': ''},
    'add': {'returncode': 0, 'stdout': '', 'stderr': ''},
    'commit': {'returncode': 0, 'stdout': '[main abc123] Test commit\n', 'stderr': ''},
    'push': {'returncode': 0, 'stdout': 'Everything up-to-date\n', 'stderr': ''},
    'pull': {'returncode': 0, 'stdout': 'Already up to date.\n', 'stderr': ''},
    'clone': {'returncode': 0, 'stdout': 'Cloning into repository...\n', 'stderr': ''},
    'fetch': {'returncode': 0, 'stdout': '', 'stderr': ''},
    'merge': {'returncode': 0, 'stdout': 'Already up to date.\n', 'stderr': ''},
    'checkout': {'returncode': 0, 'stdout': 'Switched to branch\n', 'stderr': ''},
    'remote': {'returncode': 0, 'stdout': 'origin\n', 'stderr': ''},
    'config': {'returncode': 0, 'stdout': '', 'stderr': ''},
    'init': {'returncode': 0, 'stdout': 'Initialized empty Git repository\n', 'stderr': ''},
    'tag': {'returncode': 0, 'stdout': '', 'stderr': ''},
    'show': {'returncode': 0, 'stdout': 'commit abc123\n', 'stderr': ''},
    'reset': {'returncode': 0, 'stdout': '', 'stderr': ''},
    'rebase': {'returncode': 0, 'stdout': 'Successfully rebased\n', 'stderr': ''},
    'stash': {'returncode': 0, 'stdout': '', 'stderr': ''}
}

# Default response for unknown git commands
DEFAULT_GIT_RESPONSE = {
    'returncode': 0,
    'stdout': '',
    'stderr': ''
}

class MockGitResult:
    """Mock object that mimics subprocess.CompletedProcess for git commands."""
    def __init__(self, returncode: int = 0, stdout: str = '', stderr: str = ''):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.args = []

def parse_git_command(cmd_args: List[str]) -> str:
    """Extract the git subcommand from command arguments."""
    if not cmd_args or len(cmd_args) < 2:
        return 'unknown'
    
    # Handle 'git' as first argument
    if cmd_args[0] == 'git':
        return cmd_args[1] if len(cmd_args) > 1 else 'unknown'
    
    # Handle direct subcommand
    return cmd_args[0]

def mock_git_subprocess_run(cmd_args: List[str], **kwargs) -> MockGitResult:
    """Mock subprocess.run for git commands with registry-based responses."""
    git_cmd = parse_git_command(cmd_args)
    
    # Get response from registry or use default
    response = GIT_COMMAND_REGISTRY.get(git_cmd, DEFAULT_GIT_RESPONSE)
    
    return MockGitResult(
        returncode=response['returncode'],
        stdout=response['stdout'],
        stderr=response['stderr']
    )

@pytest.fixture
def mock_git_command():
    """Shared fixture for mocking git commands with resilient defaults.
    
    This fixture provides a foundation for git command mocking that:
    - Returns sensible defaults for known git commands
    - Gracefully handles unknown commands without breaking tests
    - Can be extended by individual tests as needed
    
    Usage:
        def test_something(mock_git_command):
            # Git commands are automatically mocked
            result = subprocess.run(['git', 'status'], capture_output=True, text=True)
            assert result.returncode == 0
    """
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = mock_git_subprocess_run
        yield mock_run

@pytest.fixture
def git_mock_registry():
    """Fixture providing access to git command registry for test customization."""
    return GIT_COMMAND_REGISTRY.copy()


# --- Phase12 E2E: isolate canonical docs reads (session-130) ---
# load_session_context 以外の経路や将来のテスト変更でも、repo の docs 実ファイル変更で結果がぶれないよう
# global_rules / master_instruction / roadmap の実パスに対する load_text のみ決定論的スタブへ差し替える。

_ORIGINAL_LOAD_TEXT = _phase12_rs.load_text
_ORIGINAL_APPLY_PATCH_CAPTURE = _phase12_rs.apply_proposed_patch_and_capture_artifacts

PHASE12_E2E_STUB_GLOBAL_RULES = """# Global Rules (phase12 e2e stub)

本スタブは pytest phase12 E2E 用。正本 `global_rules.md` の役割分担・検収思想と矛盾しない最小構成。

## 2. 役割固定（要約）

- GPT: 仕様整理・判定（実装担当にならない）
- Claude: 分析・修正案（仕様の最終確定はしない）
- Cursor: 実作業・検証（正本・スコープ順守）

## Review points（4 軸の例）

1. 仕様一致（AC 達成）
2. 変更範囲遵守
3. 副作用なし（既存破壊なし）
4. 検証十分性

---

## 8. 禁止事項（抜粋）

- スコープ外ファイルの変更
- 正本ドキュメントの独断変更
"""

PHASE12_E2E_STUB_MASTER_INSTRUCTION = """# Master Instruction (phase12 e2e stub)

本スタブは `global_rules.md` と整合する前提の最小本文。
セッションは1目的、allowed_changes と forbidden_changes を尊重する。
"""

PHASE12_E2E_STUB_ROADMAP = """# Roadmap stub for phase12 e2e tests
version: phase12-e2e-stub
milestones: []
"""


def _phase12_e2e_stable_load_text(path):
    """Return fixed text for canonical docs files; otherwise delegate to run_session.load_text."""
    p = Path(path)
    try:
        resolved = p.resolve()
    except OSError:
        resolved = p
    docs_root = _phase12_rs.DOCS_DIR.resolve()
    canonical = {
        docs_root / "global_rules.md": PHASE12_E2E_STUB_GLOBAL_RULES,
        docs_root / "master_instruction.md": PHASE12_E2E_STUB_MASTER_INSTRUCTION,
        docs_root / "roadmap.yaml": PHASE12_E2E_STUB_ROADMAP,
    }
    for doc_path, stub in canonical.items():
        if resolved == doc_path.resolve():
            return stub
    return _ORIGINAL_LOAD_TEXT(p)


def _phase12_e2e_apply_patch_ignore_docs_worktree_noise(session_dir, impl_result, *, session_id=None):
    """git diff が作業ツリー上の docs 変更を拾うと forbidden 検証で誤検知するため除外する。"""
    out = _ORIGINAL_APPLY_PATCH_CAPTURE(session_dir, impl_result, session_id=session_id)
    raw = list(out.get("changed_files") or [])
    filtered = [p for p in raw if not str(p).replace("\\", "/").startswith("docs/")]
    out["changed_files"] = filtered
    return out


@pytest.fixture
def isolate_phase12_e2e_docs_reads(monkeypatch):
    """Isolate phase12 E2E from docs edits: stub canonical load_text + ignore docs/ in git-diff rollups."""
    monkeypatch.setattr(_phase12_rs, "load_text", _phase12_e2e_stable_load_text)
    monkeypatch.setattr(
        _phase12_rs,
        "apply_proposed_patch_and_capture_artifacts",
        _phase12_e2e_apply_patch_ignore_docs_worktree_noise,
    )