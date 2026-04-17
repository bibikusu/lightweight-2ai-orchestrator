# -*- coding: utf-8 -*-
"""session-121: M02 sequential executor テスト。"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from orchestration.run_plan import main as run_plan_main


ROOT_DIR = Path(__file__).resolve().parents[2]


def test_run_plan_executes_explicit_list_sessions_in_order(monkeypatch: pytest.MonkeyPatch) -> None:
    import orchestration.run_plan as run_plan_module

    order: list[str] = []

    def _fake_invoke(session_id: str) -> int:
        order.append(session_id)
        return 0

    def _fake_report(_session_id: str) -> dict:
        return {"status": "success", "changed_files": [], "checks": {"success": True}}

    monkeypatch.setattr(run_plan_module, "invoke_session_executor", _fake_invoke)
    monkeypatch.setattr(run_plan_module, "load_session_report_minimum", _fake_report)
    plan_data = {
        "session_source": {"type": "explicit_list", "session_ids": ["session-120", "session-121"]},
        "stop_policy": "stop_on_fail",
    }

    rc, _ = run_plan_module.execute_sessions(plan_data, "plan-01")
    assert rc == 0
    assert order == ["session-120", "session-121"]


def test_run_plan_uses_subprocess_to_invoke_session_executor(monkeypatch: pytest.MonkeyPatch) -> None:
    import orchestration.run_plan as run_plan_module

    calls: list[list[str]] = []

    def _fake_run(cmd, cwd=None, check=False):  # type: ignore[no-untyped-def]
        calls.append(cmd)
        assert cwd == ROOT_DIR
        assert check is False
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(run_plan_module.subprocess, "run", _fake_run)
    rc = run_plan_module.invoke_session_executor("session-120")
    assert rc == 0
    assert calls
    assert calls[0][2:] == ["--session-id", "session-120"]


def test_run_plan_stops_on_first_failed_session_when_stop_on_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import orchestration.run_plan as run_plan_module

    order: list[str] = []

    def _fake_invoke(session_id: str) -> int:
        order.append(session_id)
        return 1 if session_id == "session-121" else 0

    def _fake_report(session_id: str) -> dict:
        status = "failed" if session_id == "session-121" else "success"
        return {"status": status, "changed_files": [], "checks": {"success": status == "success"}}

    monkeypatch.setattr(run_plan_module, "invoke_session_executor", _fake_invoke)
    monkeypatch.setattr(run_plan_module, "load_session_report_minimum", _fake_report)
    plan_data = {
        "session_source": {
            "type": "explicit_list",
            "session_ids": ["session-120", "session-121", "session-122"],
        },
        "stop_policy": "stop_on_fail",
    }

    rc, report_path = run_plan_module.execute_sessions(plan_data, "plan-01")
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert rc == 1
    assert order == ["session-120", "session-121"]
    assert payload["stopped"] is True
    assert payload["stopped_on"] == "session-121"


def test_run_plan_generates_minimal_aggregate_report_on_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import orchestration.run_plan as run_plan_module

    monkeypatch.setattr(run_plan_module, "invoke_session_executor", lambda _sid: 0)
    monkeypatch.setattr(
        run_plan_module,
        "load_session_report_minimum",
        lambda _sid: {"status": "success", "changed_files": ["a.py"], "checks": {"success": True}},
    )
    plan_data = {
        "session_source": {"type": "explicit_list", "session_ids": ["session-120", "session-121"]},
        "stop_policy": "stop_on_fail",
    }
    rc, report_path = run_plan_module.execute_sessions(plan_data, "plan-01")
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert rc == 0
    assert payload["plan_id"] == "plan-01"
    assert payload["executed_sessions"] == 2
    assert payload["failed_sessions"] == 0


def test_aggregate_report_contains_minimum_session_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    import orchestration.run_plan as run_plan_module

    monkeypatch.setattr(run_plan_module, "invoke_session_executor", lambda _sid: 0)
    monkeypatch.setattr(
        run_plan_module,
        "load_session_report_minimum",
        lambda _sid: {"status": "success", "changed_files": ["x.py"], "checks": {"success": True}},
    )
    plan_data = {
        "session_source": {"type": "explicit_list", "session_ids": ["session-120"]},
        "stop_policy": "stop_on_fail",
    }
    _, report_path = run_plan_module.execute_sessions(plan_data, "plan-01")
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    session = payload["sessions"][0]
    assert set(["status", "changed_files", "checks"]).issubset(session.keys())


def test_run_plan_m02_does_not_implement_resume_or_checkpoint() -> None:
    import orchestration.run_plan as run_plan_module

    text = Path(run_plan_module.__file__).read_text(encoding="utf-8")
    assert "checkpoint" not in text
    assert "resume" not in text


def test_m02_does_not_modify_retry_logic() -> None:
    run_session_path = ROOT_DIR / "orchestration" / "run_session.py"
    text = run_session_path.read_text(encoding="utf-8")
    assert "def build_retry_prompts(" in text
    assert "def call_chatgpt_for_retry_instruction(" in text
    assert "retry_instruction.json" in text


def test_existing_checks_pass_for_m02(monkeypatch: pytest.MonkeyPatch) -> None:
    import orchestration.run_plan as run_plan_module

    def _fake_load(_path):  # type: ignore[no-untyped-def]
        return {
            "plan_id": "plan-01",
            "execution_mode": "run_existing_sessions",
            "session_source": {"type": "explicit_list", "session_ids": ["session-120", "session-121"]},
            "backlog_ref": "docs/backlogs/backlog-01.yaml",
            "stop_policy": "stop_on_fail",
        }

    monkeypatch.setattr(run_plan_module, "load_and_validate_plan", _fake_load)
    monkeypatch.setattr(run_plan_module, "invoke_session_executor", lambda _sid: 0)
    monkeypatch.setattr(
        run_plan_module,
        "load_session_report_minimum",
        lambda _sid: {"status": "success", "changed_files": [], "checks": {"success": True}},
    )

    commands = [
        ["run_plan.py", "--dry-run"],
        ["run_plan.py", "--plan-id", "plan-01", "--dry-run"],
        ["run_plan.py", "--plan-id", "plan-01", "--execute"],
        ["run_plan.py", "--plan-id", "plan-01", "--execute"],
    ]
    for argv in commands:
        monkeypatch.setattr(sys, "argv", argv)
        assert run_plan_main() == 0


def test_run_plan_without_execute_flag_keeps_m01_compatibility(monkeypatch: pytest.MonkeyPatch) -> None:
    import orchestration.run_plan as run_plan_module

    called = False

    def _fake_load(_path):  # type: ignore[no-untyped-def]
        return {
            "plan_id": "plan-01",
            "execution_mode": "run_existing_sessions",
            "session_source": {"type": "explicit_list", "session_ids": ["session-120"]},
            "backlog_ref": "docs/backlogs/backlog-01.yaml",
            "stop_policy": "stop_on_fail",
        }

    def _forbidden_execute(*_args, **_kwargs):  # pragma: no cover
        nonlocal called
        called = True
        raise AssertionError("without --execute should not start sequential executor")

    monkeypatch.setattr(run_plan_module, "load_and_validate_plan", _fake_load)
    monkeypatch.setattr(run_plan_module, "execute_sessions", _forbidden_execute)
    monkeypatch.setattr(sys, "argv", ["run_plan.py", "--plan-id", "plan-01"])
    assert run_plan_main() == 0
    assert called is False
