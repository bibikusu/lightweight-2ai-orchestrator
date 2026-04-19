"""session-141: Claude Code Hooks / MCP 設定ファイルの静的検証."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

PREFLIGHT_SRC = REPO_ROOT / "scripts" / "preflight_session.sh"


def _workspace_tmp_parent() -> Path:
    """Writable under repo root (sandbox-safe); caller must shutil.rmtree when done."""
    return Path(tempfile.mkdtemp(prefix="preflight-", dir=str(REPO_ROOT)))


def _make_preflight_repo(
    tmp_path: Path,
    session_id: str = "session-142-test",
    *,
    valid: bool = True,
) -> Path:
    """Minimal git repo with preflight, dummy venv, optional session docs; synced with bare origin."""
    bare = tmp_path / "origin.git"
    bare.mkdir(parents=True)
    subprocess.run(["git", "init", "--bare"], cwd=bare, check=True, capture_output=True)
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "preflight-test"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    (repo / "README.md").write_text("readme\n", encoding="utf-8")
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir(parents=True)
    shutil.copy2(PREFLIGHT_SRC, scripts_dir / "preflight_session.sh")

    venv_bin = repo / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    dummy_py = venv_bin / "python"
    dummy_py.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    os.chmod(dummy_py, 0o755)

    sess_dir = repo / "docs" / "sessions"
    acc_dir = repo / "docs" / "acceptance"
    sess_dir.mkdir(parents=True)
    acc_dir.mkdir(parents=True)
    if valid:
        (sess_dir / f"{session_id}.json").write_text("{}\n", encoding="utf-8")
        (acc_dir / f"{session_id}.yaml").write_text("acceptance: []\n", encoding="utf-8")

    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "branch", "-M", "main"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "remote", "add", "origin", str(bare)],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "push", "-u", "origin", "main"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    return repo


def test_pre_tool_use_hook_exists_and_executable() -> None:
    hook = REPO_ROOT / ".claude" / "hooks" / "pre_tool_use.sh"
    assert hook.is_file(), f"missing {hook}"
    assert os.access(hook, os.X_OK), f"not executable: {hook}"


def test_post_tool_use_hook_exists_and_executable() -> None:
    hook = REPO_ROOT / ".claude" / "hooks" / "post_tool_use.sh"
    assert hook.is_file(), f"missing {hook}"
    assert os.access(hook, os.X_OK), f"not executable: {hook}"


def test_claude_settings_registers_hooks_and_plan_mode() -> None:
    settings_path = REPO_ROOT / ".claude" / "settings.json"
    data = json.loads(settings_path.read_text(encoding="utf-8"))
    assert data.get("permission_mode") == "plan"
    hooks = data.get("hooks") or {}
    assert "PreToolUse" in hooks and "PostToolUse" in hooks
    pre_cmds = [e.get("command") for e in hooks["PreToolUse"]]
    post_cmds = [e.get("command") for e in hooks["PostToolUse"]]
    assert ".claude/hooks/pre_tool_use.sh" in pre_cmds
    assert ".claude/hooks/post_tool_use.sh" in post_cmds


def test_mcp_json_registers_filesystem_readonly() -> None:
    mcp_path = REPO_ROOT / ".mcp.json"
    data = json.loads(mcp_path.read_text(encoding="utf-8"))
    servers = data.get("mcpServers") or {}
    fs = servers.get("filesystem-readonly")
    assert isinstance(fs, dict), "filesystem-readonly server missing"
    assert fs.get("command") == "npx"
    env = fs.get("env") or {}
    assert env.get("READ_ONLY") == "true"


def test_pre_hook_delegates_to_preflight_script() -> None:
    script = (REPO_ROOT / ".claude" / "hooks" / "pre_tool_use.sh").read_text(
        encoding="utf-8"
    )
    assert "scripts/preflight_session.sh" in script
    assert "bash" in script and "PREFLIGHT" in script
    assert "set -e" in script
    assert "${CLAUDE_SESSION_ID:-}" in script


def test_post_hook_runs_four_gates_and_fails_fast() -> None:
    script = (REPO_ROOT / ".claude" / "hooks" / "post_tool_use.sh").read_text(
        encoding="utf-8"
    )
    assert "set -e" in script
    assert "-m ruff check orchestration/" in script
    assert "-m pytest tests/" in script
    assert "-m mypy --explicit-package-bases orchestration/" in script
    assert "-m compileall orchestration/" in script


def test_session_141_does_not_modify_core_files() -> None:
    verify = subprocess.run(
        ["git", "rev-parse", "--verify", "origin/main"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if verify.returncode != 0:
        pytest.skip("origin/main ref unavailable")

    proc = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "origin/main",
            "--",
            "orchestration/",
            "scripts/",
            "docs/",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    allowed = {
        "docs/sessions/session-141.json",
        "docs/acceptance/session-141.yaml",
        "scripts/preflight_session.sh",
    }
    unexpected = sorted(set(lines) - allowed)
    assert unexpected == [], f"unexpected changes under orchestration/scripts/docs: {unexpected}"


def test_preflight_returns_nonzero_on_dirty_worktree() -> None:
    root = _workspace_tmp_parent()
    try:
        repo = _make_preflight_repo(root)
        readme = repo / "README.md"
        readme.write_text(readme.read_text(encoding="utf-8") + "dirty\n", encoding="utf-8")
        result = subprocess.run(
            ["bash", "scripts/preflight_session.sh", "session-142-test"],
            cwd=str(repo),
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_preflight_returns_nonzero_on_branch_sync_failure() -> None:
    root = _workspace_tmp_parent()
    try:
        repo = _make_preflight_repo(root)
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "ahead-no-push"],
            cwd=repo,
            check=True,
            capture_output=True,
        )
        result = subprocess.run(
            ["bash", "scripts/preflight_session.sh", "session-142-test"],
            cwd=str(repo),
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_preflight_returns_nonzero_on_venv_failure() -> None:
    root = _workspace_tmp_parent()
    try:
        repo = _make_preflight_repo(root)
        dummy_py = repo / ".venv" / "bin" / "python"
        dummy_py.unlink()
        result = subprocess.run(
            ["bash", "scripts/preflight_session.sh", "session-142-test"],
            cwd=str(repo),
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_preflight_returns_nonzero_on_missing_session_files() -> None:
    root = _workspace_tmp_parent()
    try:
        repo = _make_preflight_repo(root, session_id="session-142-missing", valid=False)
        result = subprocess.run(
            ["bash", "scripts/preflight_session.sh", "session-142-missing"],
            cwd=str(repo),
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_preflight_returns_zero_on_clean_valid_state() -> None:
    root = _workspace_tmp_parent()
    try:
        repo = _make_preflight_repo(root)
        result = subprocess.run(
            ["bash", "scripts/preflight_session.sh", "session-142-test"],
            cwd=str(repo),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_session_142_does_not_modify_core_files() -> None:
    verify = subprocess.run(
        ["git", "rev-parse", "--verify", "origin/main"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if verify.returncode != 0:
        pytest.skip("origin/main ref unavailable")

    proc = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "origin/main",
            "--",
            "orchestration/",
            ".claude/",
            ".mcp.json",
            "docs/",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    allowed = {
        "docs/sessions/session-142.json",
        "docs/acceptance/session-142.yaml",
    }
    unexpected = sorted(set(lines) - allowed)
    assert unexpected == [], f"unexpected changes under core paths: {unexpected}"
