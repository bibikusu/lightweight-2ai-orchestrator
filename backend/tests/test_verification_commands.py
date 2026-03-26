# -*- coding: utf-8 -*-
"""session-07a: config の verification commands と pyproject の mypy 正本を検証する。

検収時（および CI で本テストを実走する場合）は、事前に次を実行済みであること:
  pip install -e ".[dev]"

pytest.importorskip("mypy") は、mypy 未導入環境では AC-05 をスキップする。
テスト内で pip install は行わない。
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT_DIR / "orchestration" / "config.yaml"
PYPROJECT_PATH = ROOT_DIR / "pyproject.toml"

EXPECTED_TYPECHECK = "python3 -m mypy orchestration --ignore-missing-imports"
EXPECTED_BUILD = (
    'PYTHONPYCACHEPREFIX="./.pycache_compileall" '
    "python3 -m compileall -q -f orchestration backend"
)


def _load_commands() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("commands") or {}


def _command_with_current_interpreter(cmd: str) -> str:
    """config の先頭の python3 を pytest 実行インタープリタに置換（run_command が shell で別 python3 を拾わないようにする）。"""
    if not cmd.strip():
        return cmd
    return cmd.replace("python3", sys.executable, 1)


def test_config_has_typecheck_command():
    """AC-01: typecheck コマンドが session-07a 指定どおり設定されている"""
    cmds = _load_commands()
    assert cmds.get("typecheck") == EXPECTED_TYPECHECK


def test_config_has_build_command():
    """AC-02: build コマンドが session-07a 指定どおり設定されている"""
    cmds = _load_commands()
    assert cmds.get("build") == EXPECTED_BUILD


def test_verification_commands_are_non_empty():
    """AC-03: typecheck / build が空でなく、明らかな no-op でない"""
    cmds = _load_commands()
    for key in ("typecheck", "build"):
        val = (cmds.get(key) or "").strip()
        assert val, f"{key} が空です"
        assert not re.match(r"^\s*echo\s", val, re.IGNORECASE), f"{key} が echo のみに近い"
    assert "pip install" not in cmds.get("typecheck", "").lower()
    assert "pip install" not in cmds.get("build", "").lower()


def test_pyproject_declares_mypy_dev_dependency():
    """AC-04: pyproject.toml の project.optional-dependencies.dev に mypy がある"""
    text = PYPROJECT_PATH.read_text(encoding="utf-8")
    assert "[project.optional-dependencies]" in text
    block = re.search(
        r"\[project\.optional-dependencies\]([\s\S]+?)(?=\n\[|\Z)",
        text,
    )
    assert block is not None, "[project.optional-dependencies] ブロックが見つかりません"
    inner = block.group(1)
    assert re.search(r"dev\s*=\s*\[", inner), "dev 配列がありません"
    assert re.search(r"mypy", inner, re.IGNORECASE), "dev に mypy がありません"


def test_existing_run_local_checks_contract_not_broken():
    """AC-05: run_command の連鎖が run_local_checks と整合。検収時は pip install -e ".[dev]" 済み前提。

    config の python3 は shell 解決で環境により異なるため、本テストでは sys.executable に置換して同一環境で実走する。
    """
    pytest.importorskip(
        "mypy",
        reason='検収時は pip install -e ".[dev]" 済みであること（mypy 未導入のためスキップ）',
    )
    from orchestration.run_session import run_command

    cmds = _load_commands()
    assert set(cmds.keys()) >= {"test", "lint", "typecheck", "build"}

    tr = run_command(cmds.get("test", ""))
    assert tr["status"] == "skipped"

    lr = run_command(_command_with_current_interpreter(cmds.get("lint", "")))
    assert lr["status"] == "passed", lr

    ty = run_command(_command_with_current_interpreter(cmds.get("typecheck", "")))
    assert ty["status"] == "passed", ty

    br = run_command(_command_with_current_interpreter(cmds.get("build", "")))
    assert br["status"] == "passed", br


def test_dry_run_flow_not_broken_by_verification_config():
    """AC-06: dry-run が追加の環境変数注入なしで成立する（env は継承のみ、PYTHONPATH は触らない）"""
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT_DIR / "orchestration" / "run_session.py"),
            "--dry-run",
            "--session-id",
            "session-01",
        ],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
