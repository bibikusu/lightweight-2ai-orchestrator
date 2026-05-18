"""session-203: hooks_validator モジュールのテスト群"""

import textwrap

from orchestration.hooks_validator import (
    check_conflicts,
    parse_claude_md_constraints,
    parse_hook_demands,
)


# ── fixtures ─────────────────────────────────────────────────────────────────

def _write(tmp_path, filename: str, content: str) -> str:
    """tmp_path 配下にファイルを作成しパスを返す。"""
    p = tmp_path / filename
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return str(p)


CLAUDE_MD_SAMPLE = """\
## 4.1 git 操作

- `git push` は KUNIHIDE manual only — ClaudeCode は絶対に実行しない
- `git add .` / `git add -A` 禁止
- `main` ブランチへの直接 commit 禁止 — sandbox branch のみで作業
- `git stash pop / drop / apply` 禁止
- `git push --force` / `git reset --hard` は KUNIHIDE 確認後のみ

sandbox/* や claude/* ブランチは push 要求不要。
"""


# ── parser tests ─────────────────────────────────────────────────────────────

def test_parse_claude_md_extracts_forbidden_push(tmp_path):
    """CLAUDE.md から git push 禁止が抽出されること。"""
    path = _write(tmp_path, "CLAUDE.md", CLAUDE_MD_SAMPLE)
    result = parse_claude_md_constraints(path)
    assert "git push" in result["forbidden_git"]


def test_parse_claude_md_extracts_branch_exclusion(tmp_path):
    """CLAUDE.md から sandbox/ と claude/ の除外プレフィックスが抽出されること。"""
    path = _write(tmp_path, "CLAUDE.md", CLAUDE_MD_SAMPLE)
    result = parse_claude_md_constraints(path)
    exclusions = result["branch_exclusions"]
    assert any("sandbox" in e for e in exclusions)
    assert any("claude" in e for e in exclusions)


def test_parse_hook_detects_push_demand(tmp_path):
    """hook スクリプトの git push 行が要求として検出されること。"""
    hook = _write(
        tmp_path,
        "stop.sh",
        """\
        #!/bin/bash
        git push origin main
        """,
    )
    demands = parse_hook_demands(hook)
    assert "git push" in demands


def test_parse_hook_handles_comments(tmp_path):
    """コメント行の git push は要求として検出されないこと。"""
    hook = _write(
        tmp_path,
        "stop.sh",
        """\
        #!/bin/bash
        # git push origin main  <- これはコメント
        echo "done"
        """,
    )
    demands = parse_hook_demands(hook)
    assert "git push" not in demands


def test_parse_hook_handles_multiline_commands(tmp_path):
    """バックスラッシュ継続行も正しく評価されること。"""
    hook = _write(
        tmp_path,
        "stop.sh",
        """\
        #!/bin/bash
        git push \\
          origin main
        """,
    )
    demands = parse_hook_demands(hook)
    assert "git push" in demands


# ── checker tests ─────────────────────────────────────────────────────────────

def test_check_conflicts_finds_push_violation(tmp_path):
    """hook が git push を要求し CLAUDE.md が禁止している場合、矛盾が検出されること。"""
    claude_md = _write(tmp_path, "CLAUDE.md", CLAUDE_MD_SAMPLE)
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()
    _write(hooks_dir, "stop.sh", "#!/bin/bash\ngit push origin main\n")

    conflicts = check_conflicts(claude_md, str(hooks_dir))
    assert len(conflicts) >= 1
    commands = [c["command"] for c in conflicts]
    assert "git push" in commands


def test_check_conflicts_no_violation_for_allowed_branch(tmp_path):
    """sandbox/ ブランチガードが hook に含まれている場合、branch_exclusion_applies が True になること。"""
    claude_md = _write(tmp_path, "CLAUDE.md", CLAUDE_MD_SAMPLE)
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()
    _write(
        hooks_dir,
        "stop.sh",
        """\
        #!/bin/bash
        BRANCH=$(git rev-parse --abbrev-ref HEAD)
        if [[ "$BRANCH" == sandbox/* ]] || [[ "$BRANCH" == claude/* ]]; then
          exit 0
        fi
        git push origin main
        """,
    )

    conflicts = check_conflicts(claude_md, str(hooks_dir))
    push_conflicts = [c for c in conflicts if c["command"] == "git push"]
    assert len(push_conflicts) >= 1
    # branch_exclusion_applies = True が付いていること
    assert push_conflicts[0]["branch_exclusion_applies"] == "True"


def test_check_conflicts_empty_when_no_conflict(tmp_path):
    """git push を含まない hook では矛盾リストが空であること。"""
    claude_md = _write(tmp_path, "CLAUDE.md", CLAUDE_MD_SAMPLE)
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()
    _write(hooks_dir, "post_tool_use.sh", "#!/bin/bash\necho 'done'\n")

    conflicts = check_conflicts(claude_md, str(hooks_dir))
    assert conflicts == []


def test_check_conflicts_severity_levels(tmp_path):
    """git push の severity が critical であること。"""
    claude_md = _write(tmp_path, "CLAUDE.md", CLAUDE_MD_SAMPLE)
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()
    _write(hooks_dir, "stop.sh", "#!/bin/bash\ngit push origin main\n")

    conflicts = check_conflicts(claude_md, str(hooks_dir))
    push_conflicts = [c for c in conflicts if c["command"] == "git push"]
    assert push_conflicts[0]["severity"] == "critical"


def test_check_conflicts_with_branch_exclusion_pattern(tmp_path):
    """CLAUDE.md に sandbox/* 記述がある場合、branch_exclusions が正しく抽出されること。"""
    claude_md = _write(tmp_path, "CLAUDE.md", CLAUDE_MD_SAMPLE)
    constraints = parse_claude_md_constraints(claude_md)
    assert "branch_exclusions" in constraints
    assert isinstance(constraints["branch_exclusions"], list)


def test_check_conflicts_no_hooks_dir_returns_empty(tmp_path):
    """hooks ディレクトリが存在しない場合は空リストを返すこと。"""
    claude_md = _write(tmp_path, "CLAUDE.md", CLAUDE_MD_SAMPLE)
    missing_dir = str(tmp_path / "nonexistent_hooks")

    conflicts = check_conflicts(claude_md, missing_dir)
    assert conflicts == []


def test_parse_claude_md_multiple_forbidden_commands(tmp_path):
    """CLAUDE.md から複数の禁止コマンドが一度に抽出されること。"""
    path = _write(tmp_path, "CLAUDE.md", CLAUDE_MD_SAMPLE)
    result = parse_claude_md_constraints(path)
    forbidden = result["forbidden_git"]
    # git push, git add ., git add -A が最低限含まれること
    assert "git push" in forbidden
    assert "git add ." in forbidden
    assert "git add -A" in forbidden


def test_parse_hook_detects_force_push(tmp_path):
    """git push --force も要求として検出されること。"""
    hook = _write(
        tmp_path,
        "stop.sh",
        "#!/bin/bash\ngit push --force origin main\n",
    )
    demands = parse_hook_demands(hook)
    assert "git push --force" in demands or "git push" in demands
