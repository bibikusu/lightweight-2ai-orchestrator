# -*- coding: utf-8 -*-
"""session-06: CI ワークフロー契約テスト（run_session 本体は変更しない）。"""

import json
import re
import sys
from pathlib import Path

import pytest
import yaml

ROOT_DIR = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = ROOT_DIR / ".github" / "workflows" / "run-orchestrator.yml"
RUN_SESSION_PATH = ROOT_DIR / "orchestration" / "run_session.py"


@pytest.fixture
def workflow_text() -> str:
    return WORKFLOW_PATH.read_text(encoding="utf-8")


@pytest.fixture
def workflow_data(workflow_text: str) -> dict:
    return yaml.safe_load(workflow_text) or {}


def test_ci_workflow_exists():
    """AC-01: ワークフローファイルが存在し YAML として解釈できる"""
    assert WORKFLOW_PATH.is_file(), f"missing: {WORKFLOW_PATH}"
    data = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert data.get("name")
    assert "jobs" in data and isinstance(data["jobs"], dict)


def test_ci_commands_match_local_contract():
    """AC-10-01: ci.yml が push/pull_request と checks の契約に一致する。"""
    ci_path = ROOT_DIR / ".github" / "workflows" / "ci.yml"
    assert ci_path.is_file(), f"missing: {ci_path}"

    workflow_text = ci_path.read_text(encoding="utf-8")
    workflow_data = yaml.safe_load(workflow_text) or {}

    on_block = workflow_data.get("on")
    assert isinstance(on_block, dict), "トリガー(on)が dict で定義されていない"
    assert "push" in on_block, "push トリガーが必要"
    assert "pull_request" in on_block, "pull_request トリガーが必要"

    jobs = workflow_data.get("jobs") or {}
    assert isinstance(jobs, dict) and jobs, "jobs が未定義"
    checks = jobs.get("checks")
    assert isinstance(checks, dict), "checks ジョブが未定義"
    steps = checks.get("steps") or []
    run_snippets = [
        str(step.get("run", ""))
        for step in steps
        if isinstance(step, dict) and "run" in step
    ]
    merged = "\n".join(run_snippets)

    assert re.search(r"PYTHONPATH=\.\s+pytest\s+backend/tests/?\s+-q", merged)
    assert (
        "python -m mypy --explicit-package-bases orchestration "
        "--ignore-missing-imports --disable-error-code import-untyped"
    ) in merged
    assert (
        'PYTHONPYCACHEPREFIX="./.pycache_compileall" python -m compileall -q -f '
        "orchestration backend"
    ) in merged


def test_ci_does_not_require_api_keys_for_checks_only():
    """AC-10-02: checks 専用 CI は API キー前提にしない。"""
    ci_path = ROOT_DIR / ".github" / "workflows" / "ci.yml"
    workflow_text = ci_path.read_text(encoding="utf-8")

    assert "OPENAI_API_KEY" not in workflow_text
    assert "ANTHROPIC_API_KEY" not in workflow_text
    assert "CLAUDE_API_KEY" not in workflow_text
    assert "run_session.py" not in workflow_text
    assert "--dry-run" not in workflow_text


def test_existing_local_flow_not_broken(monkeypatch, tmp_path):
    """AC-04: 既存の dry-run main 呼び出しがローカルで成立する"""
    import orchestration.run_session as rs

    monkeypatch.setattr(rs, "ARTIFACTS_DIR", tmp_path / "artifacts")
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_session.py", "--dry-run", "--session-id", "session-01"],
    )
    assert rs.main() == 0
    reports = tmp_path / "artifacts" / "session-01" / "reports"
    assert (reports / "session_report.json").is_file()
    data = json.loads(
        (reports / "session_report.json").read_text(encoding="utf-8")
    )
    assert data["session_id"] == "session-01"
