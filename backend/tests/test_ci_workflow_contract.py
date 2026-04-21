# -*- coding: utf-8 -*-
"""session-54: validation.yml に標準4コマンドと push/pull_request トリガーが含まれることの契約テスト。"""

from pathlib import Path

import yaml

ROOT_DIR = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = ROOT_DIR / ".github" / "workflows" / "validation.yml"

# CI とローカルで同一の標準4コマンド（文字列は workflow の run と一致させる）
COMMAND_RUFF = ".venv/bin/ruff check ."
COMMAND_PYTEST = "PYTHONPATH=. .venv/bin/pytest backend/tests/ -q"
COMMAND_MYPY = (
    "PYTHONPATH=. .venv/bin/python -m mypy "
    "--explicit-package-bases orchestration --ignore-missing-imports"
)
COMMAND_COMPILEALL = (
    'PYTHONPYCACHEPREFIX="./.pycache_compileall" '
    ".venv/bin/python -m compileall -q -f orchestration backend"
)


def _merged_run_text(workflow_data: dict) -> str:
    jobs = workflow_data.get("jobs") or {}
    parts: list[str] = []
    for job in jobs.values():
        if not isinstance(job, dict):
            continue
        for step in job.get("steps") or []:
            if not isinstance(step, dict):
                continue
            run = step.get("run")
            if run is not None:
                parts.append(str(run))
    return "\n".join(parts)


def test_ci_workflow_exists():
    """workflow が存在し YAML として解釈できる（AC-54 前提）。"""
    assert WORKFLOW_PATH.is_file(), f"missing: {WORKFLOW_PATH}"
    data = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert data.get("name")
    assert "jobs" in data and isinstance(data["jobs"], dict)


def test_ci_workflow_has_triggers():
    """push / pull_request がトリガに含まれる（AC-54-02）。"""
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    data = yaml.safe_load(text) or {}
    on_block = data.get("on")
    assert isinstance(on_block, dict), "トリガ(on)が dict で定義されていない"
    assert "push" in on_block, "push トリガーが必要"
    assert "pull_request" in on_block, "pull_request トリガーが必要"


def test_ci_workflow_contains_commands():
    """標準4コマンドが workflow の run に含まれる（AC-54-01）。"""
    data = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8")) or {}
    merged = _merged_run_text(data)
    assert COMMAND_RUFF in merged
    assert COMMAND_PYTEST in merged
    assert COMMAND_MYPY in merged
    assert COMMAND_COMPILEALL in merged
