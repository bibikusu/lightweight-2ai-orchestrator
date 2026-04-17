# -*- coding: utf-8 -*-
"""session-120: M01 plan loader + validation テスト。"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from orchestration.plan_schema import validate_plan_schema
from orchestration.run_plan import main as run_plan_main


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_PLAN_PATH = ROOT_DIR / "docs" / "plans" / "plan-01.yaml"


def _load_plan_dict() -> dict:
    with DEFAULT_PLAN_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_plan_loader_reads_standard_plan_path() -> None:
    assert DEFAULT_PLAN_PATH.exists()
    plan_data = _load_plan_dict()
    assert plan_data["plan_id"] == "plan-01"


def test_plan_loader_accepts_standard_backlog_path() -> None:
    plan_data = _load_plan_dict()
    assert plan_data["backlog_ref"] == "docs/backlogs/backlog-01.yaml"
    assert (ROOT_DIR / plan_data["backlog_ref"]).exists()


def test_plan_loader_reports_missing_required_keys_fail_fast() -> None:
    broken = {
        "plan_id": "plan-01",
    }
    with pytest.raises(ValueError, match="missing required keys: backlog_ref, execution_mode, session_source"):
        validate_plan_schema(broken)


@pytest.mark.parametrize("execution_mode", ["generate_sessions", "mixed"])
def test_plan_loader_rejects_generate_or_mixed_before_m04(execution_mode: str) -> None:
    plan_data = _load_plan_dict()
    plan_data["execution_mode"] = execution_mode
    with pytest.raises(ValueError, match="execution_mode must be run_existing_sessions before M04"):
        validate_plan_schema(plan_data)


def test_run_plan_dry_run_does_not_execute_sessions(monkeypatch: pytest.MonkeyPatch) -> None:
    import orchestration.run_plan as run_plan_module

    called = False

    def _forbidden_execute(*_args, **_kwargs):  # pragma: no cover
        nonlocal called
        called = True
        raise AssertionError("M01 dry-run should not execute sessions")

    monkeypatch.setattr(run_plan_module, "execute_sessions", _forbidden_execute, raising=False)
    monkeypatch.setattr(sys, "argv", ["run_plan.py", "--dry-run"])
    rc = run_plan_main()
    assert rc == 0
    assert called is False


def test_m01_does_not_modify_retry_logic() -> None:
    run_session_path = ROOT_DIR / "orchestration" / "run_session.py"
    text = run_session_path.read_text(encoding="utf-8")
    assert "def build_retry_prompts(" in text
    assert "def call_chatgpt_for_retry_instruction(" in text
    assert "retry_instruction.json" in text


def test_existing_checks_pass_for_m01() -> None:
    commands = [
        [
            sys.executable,
            "-m",
            "pytest",
            "backend/tests/test_run_plan_loader_validation.py",
            "-k",
            "not test_existing_checks_pass_for_m01",
        ],
        [sys.executable, "orchestration/run_plan.py", "--dry-run"],
        [sys.executable, "orchestration/run_plan.py", "--plan-id", "plan-01", "--dry-run"],
        [sys.executable, "orchestration/run_plan.py", "--plan-id", "plan-01"],
    ]

    for cmd in commands:
        completed = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True, text=True, check=False)
        assert completed.returncode == 0, (
            f"command failed: {' '.join(cmd)}\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )
