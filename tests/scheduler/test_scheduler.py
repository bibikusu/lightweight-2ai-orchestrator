from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

from orchestration.scheduler.cron_runner import CronRunner, JST
from orchestration.scheduler.plan_loader import (
    QueueConfig,
    ScheduledPlan,
    SessionEntry,
    SchedulerPlanLoader,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_min_registry(path: Path, project_id: str, deploy_risk: str) -> None:
    path.write_text(
        json.dumps(
            {
                "version": "t",
                "projects": [{"project_id": project_id, "deploy_risk": deploy_risk}],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _write_min_policy(path: Path) -> None:
    path.write_text("version: test\n", encoding="utf-8")


def _write_plans(tmp_path: Path, reg: Path, pol: Path) -> Path:
    plans_path = tmp_path / "scheduler_plans.yaml"
    plans_path.write_text(
        "\n".join(
            [
                "queue_config:",
                f"  registry_path: {reg.as_posix()}",
                f"  policy_path: {pol.as_posix()}",
                "plans:",
                "  - id: ticktest",
                "    enabled: true",
                "    hour: 12",
                "    minute: 0",
                "    weekday: null",
                "    sessions:",
                "      - session_id: session-a",
                "        project_id: P1",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return plans_path


def test_scheduler_plan_loader_reads_plans() -> None:
    loader = SchedulerPlanLoader(REPO_ROOT / "docs/config/scheduler_plans.yaml")
    qc, plans = loader.load()
    assert qc.registry_path == REPO_ROOT / "docs/config/project_registry.json"
    assert qc.policy_path == REPO_ROOT / "docs/config/queue_policy.yaml"
    ids = [p.id for p in plans]
    assert "daily" in ids and "weekly" in ids
    daily = next(p for p in plans if p.id == "daily")
    assert daily.weekday is None
    weekly = next(p for p in plans if p.id == "weekly")
    assert weekly.weekday == 1


def test_scheduler_enqueues_only_when_plan_matches(tmp_path: Path) -> None:
    reg = tmp_path / "registry.json"
    pol = tmp_path / "policy.yaml"
    _write_min_registry(reg, "P1", "low")
    _write_min_policy(pol)
    plans_file = _write_plans(tmp_path, reg, pol)
    store_path = tmp_path / "queue_state.json"

    cp_ok = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    with patch("orchestration.queue.engine.subprocess.run", return_value=cp_ok):
        loader = SchedulerPlanLoader(plans_file)
        from orchestration.queue.store import QueueStore

        runner = CronRunner(loader, queue_store=QueueStore(store_path))
        now = datetime(2026, 4, 19, 12, 0, 0, tzinfo=JST)
        ran = runner.tick(now)

    assert len(ran) >= 1
    items = json.loads(store_path.read_text(encoding="utf-8"))
    assert any(x.get("session_id") == "session-a" for x in items)


def test_scheduler_skips_when_plan_does_not_match(tmp_path: Path) -> None:
    reg = tmp_path / "registry.json"
    pol = tmp_path / "policy.yaml"
    _write_min_registry(reg, "P1", "low")
    _write_min_policy(pol)
    plans_file = _write_plans(tmp_path, reg, pol)
    store_path = tmp_path / "queue_state.json"

    loader = SchedulerPlanLoader(plans_file)
    from orchestration.queue.store import QueueStore

    runner = CronRunner(loader, queue_store=QueueStore(store_path))
    now = datetime(2026, 4, 19, 11, 0, 0, tzinfo=JST)
    runner.tick(now)

    assert not store_path.is_file() or store_path.read_text(encoding="utf-8").strip() == "[]"


def test_scheduler_invokes_queue_engine_methods(tmp_path: Path) -> None:
    mock_engine = MagicMock()
    mock_engine.run_next.side_effect = [None]

    from orchestration.queue.store import QueueStore

    qc = QueueConfig(registry_path=tmp_path / "r.json", policy_path=tmp_path / "p.yaml")
    plan = ScheduledPlan(
        id="p1",
        enabled=True,
        hour=8,
        minute=0,
        weekday=None,
        sessions=[SessionEntry(session_id="s1", project_id="P1")],
    )
    loader = MagicMock()
    loader.load.return_value = (qc, [plan])

    with patch("orchestration.scheduler.cron_runner.QueueEngine", return_value=mock_engine):
        runner = CronRunner(loader, queue_store=QueueStore(tmp_path / "queue_state.json"))
        now = datetime(2026, 4, 20, 8, 0, 0, tzinfo=ZoneInfo("Asia/Tokyo"))
        runner.tick(now)

    mock_engine.enqueue.assert_called_once_with("s1", "P1")
    mock_engine.dispatch_ready.assert_called_once()
    mock_engine.run_next.assert_called_once()


def test_scheduler_does_not_modify_queue_or_run_session() -> None:
    proc = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "origin/main",
            "--",
            "orchestration/run_session.py",
            "orchestration/queue/engine.py",
            "orchestration/queue/state.py",
            "orchestration/queue/store.py",
            "orchestration/queue/__init__.py",
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        check=False,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == ""
