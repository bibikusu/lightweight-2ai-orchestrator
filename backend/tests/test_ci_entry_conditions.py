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


def test_ci_workflow_runs_dry_run_entry(workflow_data: dict, workflow_text: str):
    """AC-02: dry-run エントリと session 指定がワークフローに明示されている"""
    on_block = workflow_data.get("on")
    assert on_block is not None and isinstance(
        on_block, dict
    ), "トリガー(on)が未定義または dict でない（ワークフローでは 'on': を使用すること）"
    assert (
        "workflow_dispatch" in on_block
        or "pull_request" in on_block
        or "push" in on_block
    ), "push / pull_request / workflow_dispatch のいずれかが必要"

    assert "--dry-run" in workflow_text
    assert "session-01" in workflow_text or "--session-id" in workflow_text
    assert "run_session.py" in workflow_text

    jobs = workflow_data.get("jobs") or {}
    assert jobs, "jobs が空"
    job_def = next(iter(jobs.values()))
    steps = job_def.get("steps") or []
    run_snippets = [
        str(s.get("run", "")) for s in steps if isinstance(s, dict) and "run" in s
    ]
    merged = "\n".join(run_snippets)
    assert "--dry-run" in merged
    assert "pytest" in merged and "test_ci_entry_conditions" in merged


def test_ci_does_not_modify_runtime_code(workflow_text: str):
    """AC-03: CI が orchestration/run_session.py を書き換えない"""
    assert RUN_SESSION_PATH.is_file()
    before = RUN_SESSION_PATH.read_bytes()

    dangerous = [
        r">>\s*orchestration/run_session\.py",
        r">\s*orchestration/run_session\.py",
        r"sed\s+-i.*run_session\.py",
        r"tee\s+.*run_session\.py",
    ]
    for pat in dangerous:
        assert re.search(pat, workflow_text, re.IGNORECASE) is None, (
            f"禁止パターンに一致: {pat}"
        )

    # ローカル検証でファイルが触られていないこと
    after = RUN_SESSION_PATH.read_bytes()
    assert before == after


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
