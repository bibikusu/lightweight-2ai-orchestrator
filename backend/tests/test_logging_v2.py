# -*- coding: utf-8 -*-
"""session-105: ログ構造化（既存強化）の回帰テスト。"""

from __future__ import annotations

import json
from pathlib import Path

from orchestration.run_session import _emit_structured_log, log_stage_event, log_stage_progress, save_error_snapshot


def test_structured_log(capsys):
    _emit_structured_log(
        stage="unit",
        session_id="session-105",
        message="hello",
        branch="test-branch",
    )
    out = capsys.readouterr().out.strip().splitlines()
    assert out, "structured log が出力されていない"
    payload = json.loads(out[-1])
    assert payload["stage"] == "unit"
    assert payload["session_id"] == "session-105"
    assert payload["message"] == "hello"
    assert payload["branch"] == "test-branch"
    assert isinstance(payload["timestamp"], str) and payload["timestamp"]


def test_stage_log(capsys):
    log_stage_event(session_id="session-105", stage="prepared_spec", event="start", branch="br")
    log_stage_event(session_id="session-105", stage="prepared_spec", event="end", branch="br")
    lines = [ln for ln in capsys.readouterr().out.strip().splitlines() if ln.strip()]
    assert len(lines) >= 2
    p1 = json.loads(lines[-2])
    p2 = json.loads(lines[-1])
    assert p1["stage"] == "prepared_spec"
    assert p2["stage"] == "prepared_spec"
    assert p1["message"] == "stage_start"
    assert p2["message"] == "stage_end"


def test_snapshot(tmp_path: Path):
    session_dir = tmp_path / "artifacts" / "session-105"
    session_dir.mkdir(parents=True)
    err = RuntimeError("boom")
    saved = save_error_snapshot(
        session_dir=session_dir,
        stage="implementation",
        session_id="session-105",
        error=err,
        branch="br",
    )
    assert saved is not None
    assert saved.exists(), "error_snapshot.json が保存されていない"
    payload = json.loads(saved.read_text(encoding="utf-8"))
    assert payload["session_id"] == "session-105"
    assert payload["stage"] == "implementation"
    assert payload["error_type"] == "RuntimeError"


def test_no_regression(capsys):
    # 既存の [INFO] ログ形式を壊さず、直後に JSON が1行追加されること（追加のみ）
    log_stage_progress("session-105", "checks", "detail")
    lines = [ln for ln in capsys.readouterr().out.splitlines() if ln.strip()]
    assert len(lines) >= 2
    assert lines[-2].startswith("[INFO] stage=checks session_id=session-105"), lines[-2]
    json.loads(lines[-1])
