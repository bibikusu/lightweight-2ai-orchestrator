from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

from orchestration.queue.engine import QueueEngine
from orchestration.queue.state import QueueItem, QueueState
from orchestration.queue.store import QueueStore

REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_min_registry(path: Path, project_id: str, deploy_risk: str) -> None:
    path.write_text(
        json.dumps(
            {
                "version": "t",
                "projects": [
                    {
                        "project_id": project_id,
                        "deploy_risk": deploy_risk,
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _write_min_policy(path: Path) -> None:
    path.write_text("version: test\n", encoding="utf-8")


def test_queue_state_enum_defined() -> None:
    assert {s.value for s in QueueState} == {
        "pending",
        "ready",
        "running",
        "blocked_human",
        "retry_waiting",
        "completed",
        "failed",
    }


def test_queue_store_roundtrip_json(tmp_path: Path) -> None:
    p = tmp_path / "queue_state.json"
    s1 = QueueStore(p)
    now = "2026-04-19T00:00:00Z"
    item = QueueItem(
        id="q1",
        session_id="session-x",
        project_id="P1",
        state=QueueState.PENDING,
        deploy_risk="low",
        created_at=now,
        updated_at=now,
    )
    s1.upsert(item)
    s2 = QueueStore(p)
    loaded = s2.load()
    assert len(loaded) == 1
    assert loaded[0].id == item.id
    assert loaded[0].state == QueueState.PENDING


def test_queue_engine_invokes_run_session_via_subprocess(tmp_path: Path) -> None:
    reg = tmp_path / "registry.json"
    pol = tmp_path / "policy.yaml"
    _write_min_registry(reg, "P_low", "low")
    _write_min_policy(pol)
    store = QueueStore(tmp_path / "queue_state.json")
    eng = QueueEngine(store, reg, pol)
    eng.enqueue("session-invoke", "P_low")
    eng.dispatch_ready()
    cp_ok = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="", stderr=""
    )
    with patch("orchestration.queue.engine.subprocess.run", return_value=cp_ok) as m:
        eng.run_next()
        m.assert_called_once()
        argv = m.call_args[0][0]
        assert argv == [
            "python",
            "orchestration/run_session.py",
            "--session-id",
            "session-invoke",
            "--project",
            "P_low",
        ]


def test_queue_engine_routes_states_by_result(tmp_path: Path) -> None:
    cp0 = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    cp1 = subprocess.CompletedProcess(
        args=[],
        returncode=1,
        stdout='{"failure_type": "test_failure"}\n',
        stderr="",
    )
    cp2 = subprocess.CompletedProcess(
        args=[],
        returncode=1,
        stdout='{"failure_type": "scope_violation"}\n',
        stderr="",
    )
    cases: list[tuple[str, subprocess.CompletedProcess, QueueState]] = [
        ("s_ok", cp0, QueueState.COMPLETED),
        ("s_retry", cp1, QueueState.RETRY_WAITING),
        ("s_scope", cp2, QueueState.BLOCKED_HUMAN),
    ]
    for sid, cp, want in cases:
        sub = tmp_path / sid
        sub.mkdir()
        reg = sub / "registry.json"
        pol = sub / "policy.yaml"
        _write_min_registry(reg, "P_low", "low")
        _write_min_policy(pol)
        store = QueueStore(sub / "queue_state.json")
        eng = QueueEngine(store, reg, pol)
        eng.enqueue(sid, "P_low")
        eng.dispatch_ready()
        with patch("orchestration.queue.engine.subprocess.run", return_value=cp):
            eng.run_next()
        assert store.load()[0].state == want


def test_queue_engine_blocks_human_gate_conditions(tmp_path: Path) -> None:
    reg = tmp_path / "registry.json"
    pol = tmp_path / "policy.yaml"
    _write_min_policy(pol)
    store = QueueStore(tmp_path / "queue_state.json")

    _write_min_registry(reg, "P_crit", "critical")
    eng = QueueEngine(store, reg, pol)
    crit_item = QueueItem(
        id="crit1",
        session_id="s_crit",
        project_id="P_crit",
        state=QueueState.RUNNING,
        deploy_risk="critical",
        created_at="2026-04-19T00:00:00Z",
        updated_at="2026-04-19T00:00:00Z",
    )
    store.save([crit_item])
    r1 = eng.route_after_run(crit_item, 1, "test_failure")
    assert r1.state == QueueState.BLOCKED_HUMAN

    _write_min_registry(reg, "P_low", "low")
    eng2 = QueueEngine(store, reg, pol)
    low_scope = QueueItem(
        id="low_s",
        session_id="s_ls",
        project_id="P_low",
        state=QueueState.RUNNING,
        deploy_risk="low",
        created_at="2026-04-19T00:00:00Z",
        updated_at="2026-04-19T00:00:00Z",
    )
    store.save([low_scope])
    r2 = eng2.route_after_run(low_scope, 1, "scope_violation")
    assert r2.state == QueueState.BLOCKED_HUMAN

    low_reg = QueueItem(
        id="low_r",
        session_id="s_lr",
        project_id="P_low",
        state=QueueState.RUNNING,
        deploy_risk="low",
        created_at="2026-04-19T00:00:00Z",
        updated_at="2026-04-19T00:00:00Z",
    )
    store.save([low_reg])
    r3 = eng2.route_after_run(low_reg, 1, "regression")
    assert r3.state == QueueState.BLOCKED_HUMAN


def test_session_137_does_not_modify_run_session_or_policy_files() -> None:
    proc = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "origin/main",
            "--",
            "orchestration/run_session.py",
            "docs/config/project_registry.json",
            "docs/config/queue_policy.yaml",
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        check=False,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == ""
