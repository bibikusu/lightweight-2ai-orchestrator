# -*- coding: utf-8 -*-
"""session-65: live-run failure の分類と report.json メタデータの検証。"""

from pathlib import Path
import json
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

import pytest

import orchestration.run_session as run_session


def test_patch_apply_failure_classification() -> None:
    """AC-65-01: git apply 未適用（実差分なし）を patch_apply_failure とする。"""
    cr: Dict[str, Any] = {
        "patch_apply": {
            "status": "failed",
            "stderr": "git apply 相当の処理後も実差分が得られませんでした",
        },
        "test": {"status": "skipped", "stderr": ""},
        "lint": {"status": "skipped", "stderr": ""},
        "typecheck": {"status": "skipped", "stderr": ""},
        "build": {"status": "skipped", "stderr": ""},
        "success": False,
        "patch_apply_failed": True,
    }
    out = run_session.resolve_canonical_failure_type(cr)
    assert out["failure_type"] == "patch_apply_failure"
    assert out["priority"] == 1
    cf = run_session.classify_failure(cr)
    assert cf["failure_type"] == "patch_apply_failure"


def test_generated_artifact_invalid_classification() -> None:
    """AC-65-02: pytest 出力の SyntaxError を generated_artifact_invalid とする。"""
    cr: Dict[str, Any] = {
        "test": {
            "status": "failed",
            "command": "pytest",
            "returncode": 2,
            "stderr": 'File "backend/foo.py", line 3\n    def x(\nSyntaxError: invalid syntax',
            "stdout": "",
        },
        "lint": {"status": "skipped"},
        "typecheck": {"status": "skipped"},
        "build": {"status": "skipped"},
        "success": False,
    }
    out = run_session.resolve_canonical_failure_type(cr)
    assert out["failure_type"] == "generated_artifact_invalid"
    assert out["priority"] == 2
    cf = run_session.classify_failure(cr)
    assert cf["failure_type"] == "generated_artifact_invalid"


def test_pytest_failure_classification() -> None:
    """AC-65-03: 純粋な assertion 失敗は test_failure のまま。"""
    cr: Dict[str, Any] = {
        "test": {
            "status": "failed",
            "command": "pytest",
            "returncode": 1,
            "stderr": "E   AssertionError: assert 1 == 2",
            "stdout": "",
        },
        "lint": {"status": "skipped"},
        "typecheck": {"status": "skipped"},
        "build": {"status": "skipped"},
        "success": False,
    }
    out = run_session.resolve_canonical_failure_type(cr)
    assert out["failure_type"] == "test_failure"
    assert out["priority"] == 4
    cf = run_session.classify_failure(cr)
    assert cf["failure_type"] == "test_failure"


def test_report_contains_failure_metadata(tmp_path: Path) -> None:
    """AC-65-04: report.json に failure_layer / stop_stage / retryable / cause_summary が含まれる。"""
    ctx = run_session.SessionContext(
        session_id="session-65",
        session_data={"phase_id": "p", "title": "t", "goal": "g"},
        acceptance_data={"parsed": {"acceptance": []}, "raw_yaml": ""},
        master_instruction="",
        global_rules="",
        roadmap_text="",
        runtime_config={},
    )
    checks: Dict[str, Any] = {
        "test": {
            "status": "failed",
            "stderr": "E   AssertionError: assert False",
            "stdout": "",
        },
        "lint": {"status": "skipped"},
        "typecheck": {"status": "skipped"},
        "build": {"status": "skipped"},
        "success": False,
    }
    run_session.persist_session_reports(
        session_dir=tmp_path,
        ctx=ctx,
        prepared_spec={"objective": "o"},
        impl_result={"changed_files": [], "risks": [], "open_issues": []},
        checks=checks,
        status="failed",
        dry_run=False,
        started_at="2026-04-01T00:00:00+00:00",
        finished_at="2026-04-01T00:00:01+00:00",
        retry_instruction=None,
        error_message=None,
        retry_control=None,
    )
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert report["failure_type"] == "test_failure"
    assert report["failure_layer"] == "specification"
    assert report["stop_stage"] == "checks"
    assert report["retryable"] is True
    assert isinstance(report.get("cause_summary"), str)
    assert len(report["cause_summary"]) > 0


def test_run_stops_after_patch_apply_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """AC-65-05: patch 未適用時にローカル checks（pytest）を実行しない。"""
    called: List[str] = []

    def _spy_run_local_checks(
        ctx: Any, skip_build: bool = False
    ) -> Dict[str, Any]:  # noqa: ARG001
        called.append("run_local_checks")
        return run_session.build_skipped_checks_result()

    def _fake_apply(
        session_dir: Path,
        impl_result: Dict[str, Any],
        *,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {
            "patch_path": session_dir / "patches" / "proposed.patch",
            "applied": False,
            "changed_files": [],
            "patch_apply_failed": True,
            "patch_apply_message": "stub: patch 未適用",
        }

    monkeypatch.setattr(run_session, "run_local_checks", _spy_run_local_checks)
    monkeypatch.setattr(
        run_session, "apply_proposed_patch_and_capture_artifacts", _fake_apply
    )

    impl: Dict[str, Any] = {
        "proposed_patch": "diff --git a/x.py b/x.py\n",
        "changed_files": [],
    }
    ctx = MagicMock()
    ctx.session_data = {}
    run_session._apply_patch_validate_and_run_local_checks(
        session_dir=tmp_path,
        ctx=ctx,
        impl_result=impl,
        prepared_spec={"allowed_changes": ["x.py"]},
        max_changed_files=5,
        skip_build=False,
        session_id="session-65",
    )
    assert "run_local_checks" not in called
