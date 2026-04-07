# -*- coding: utf-8 -*-
"""session-18: --batch 順次実行と batch_summary.json（AC-18-01〜04）。"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

import orchestration.run_session as rs


@pytest.fixture
def batch_artifacts_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """batch_summary などを tmp 配下へ隔離する。"""
    art = tmp_path / "artifacts"
    monkeypatch.setattr(rs, "ARTIFACTS_DIR", art)
    monkeypatch.chdir(rs.ROOT_DIR)
    return art


def test_batch_runs_multiple_sessions(
    batch_artifacts_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-18-01: --batch で複数 session が順に実行される。"""
    called: list[str] = []

    def fake_impl(args: object) -> int:
        sid = getattr(args, "session_id", "")
        called.append(str(sid))
        return 0

    monkeypatch.setattr(sys, "argv", ["rs", "--batch", "session-a, session-b ,session-c"])
    monkeypatch.setattr(rs, "validate_before_run", lambda: None)
    monkeypatch.setattr(rs, "_utc_timestamp_compact", lambda: "TESTTS")
    monkeypatch.setattr(rs, "_run_single_session_impl", fake_impl)

    rc = rs.main()
    assert rc == 0
    assert called == ["session-a", "session-b", "session-c"]


def test_batch_stops_on_failure(
    batch_artifacts_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-18-02: 途中失敗後は実行せず skipped とする。"""
    called: list[str] = []

    def fake_impl(args: object) -> int:
        sid = getattr(args, "session_id", "")
        called.append(str(sid))
        return 1 if sid == "session-b" else 0

    monkeypatch.setattr(sys, "argv", ["rs", "--batch", "session-a,session-b,session-c"])
    monkeypatch.setattr(rs, "validate_before_run", lambda: None)
    monkeypatch.setattr(rs, "_utc_timestamp_compact", lambda: "FAILTS")
    monkeypatch.setattr(rs, "_run_single_session_impl", fake_impl)

    rc = rs.main()
    assert rc == 1
    assert called == ["session-a", "session-b"]

    summary_path = batch_artifacts_root / "batch-FAILTS" / "batch_summary.json"
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    assert data["skipped"] == ["session-c"]
    assert data["failed"] == ["session-b"]


def test_batch_summary_output(
    batch_artifacts_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-18-03: batch_summary.json に executed / failed / skipped が記録される。"""
    monkeypatch.setattr(sys, "argv", ["rs", "--batch", "s1,s2"])
    monkeypatch.setattr(rs, "validate_before_run", lambda: None)
    monkeypatch.setattr(rs, "_utc_timestamp_compact", lambda: "SUMTS")
    monkeypatch.setattr(rs, "_run_single_session_impl", lambda _a: 0)

    assert rs.main() == 0

    summary_path = batch_artifacts_root / "batch-SUMTS" / "batch_summary.json"
    assert summary_path.is_file()
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    for key in ("executed", "failed", "skipped"):
        assert key in data
    assert data["executed"] == ["s1", "s2"]
    assert data["failed"] == []
    assert data["skipped"] == []
    assert data["overall_exit_code"] == 0


def test_single_run_unchanged(batch_artifacts_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-18-04: --batch なしは従来どおり単体フロー（_run_single_session_impl 1回）。"""
    called: list[str] = []

    def fake_impl(args: object) -> int:
        called.append(getattr(args, "session_id", ""))
        assert getattr(args, "batch", None) is None
        return 0

    monkeypatch.setattr(sys, "argv", ["rs", "--session-id", "session-only"])
    monkeypatch.setattr(rs, "_run_single_session_impl", fake_impl)

    with patch.object(rs, "_run_batch", wraps=rs._run_batch) as mock_batch:
        rc = rs.main()
        assert rc == 0
        mock_batch.assert_not_called()

    assert called == ["session-only"]
