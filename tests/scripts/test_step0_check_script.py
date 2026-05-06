from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "step0_check.sh"


def _run(
    args: list[str] | None = None,
    env_override: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    import os
    env = os.environ.copy()
    if env_override:
        env.update(env_override)
    return subprocess.run(
        [str(SCRIPT)] + (args or []),
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        env=env,
    )


def test_step0_check_exits_0_no_args() -> None:
    """AC-177-01: 引数なし実行で exit 0 を返す。"""
    result = _run()
    assert result.returncode == 0, (
        f"Expected exit 0 with no args, got {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_step0_check_exits_nonzero_bad_hash() -> None:
    """AC-177-02: 存在しない hash を渡すと exit 非0 を返す。"""
    bad_hash = "0000000"
    result = _run([bad_hash])
    assert result.returncode != 0, (
        f"Expected non-zero exit for bad hash, got {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_step0_check_no_hardcoded_hashes() -> None:
    """AC-177-03: スクリプト本体に40桁固定 hex hash がハードコードされていない。"""
    source = SCRIPT.read_text(encoding="utf-8")
    matches = re.findall(r"[0-9a-f]{40}", source)
    assert not matches, (
        f"Hardcoded 40-hex hashes found in {SCRIPT.name}: {matches}"
    )


def test_step0_check_allowlist_env_override() -> None:
    """AC-177-04: STEP0_UNTRACKED_ALLOWLIST env var を指定しても exit 0 を返す。"""
    allowlist = "^DL/\n^artifacts/"
    result = _run(env_override={"STEP0_UNTRACKED_ALLOWLIST": allowlist})
    assert result.returncode == 0, (
        f"Expected exit 0 with STEP0_UNTRACKED_ALLOWLIST override, "
        f"got {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    source = SCRIPT.read_text(encoding="utf-8")
    assert "DEFAULT_ALLOWED_UNTRACKED" in source or "ALLOWED_UNTRACKED" in source, (
        "allowlist array variable not found in script"
    )
    assert "STEP0_UNTRACKED_ALLOWLIST" in source, (
        "STEP0_UNTRACKED_ALLOWLIST env var not implemented in script"
    )
