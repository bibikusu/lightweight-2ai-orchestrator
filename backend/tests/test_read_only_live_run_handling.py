# -*- coding: utf-8 -*-
"""session-77: read-only live-run outcome の正規化（allowed_changes==[] のみ）。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

import orchestration.run_session as run_session


def _minimal_ctx(*, session_id: str = "session-readonly-test", allowed_changes: List[str]) -> run_session.SessionContext:
    return run_session.SessionContext(
        session_id=session_id,
        session_data={
            "session_id": session_id,
            "phase_id": "p0",
            "title": "t",
            "goal": "g",
            "allowed_changes": allowed_changes,
        },
        acceptance_data={"parsed": {"acceptance": []}, "raw_yaml": ""},
        master_instruction="",
        global_rules="",
        roadmap_text="",
        runtime_config={"commands": {"test": "", "lint": "", "typecheck": "", "build": ""}},
    )


def _read_only_impl_result(*, proposed_patch: Any = None) -> Dict[str, Any]:
    return {
        "session_id": "session-readonly-test",
        "changed_files": [],
        "implementation_summary": ["read-only verification"],
        "patch_status": "not_applicable",
        "risks": [],
        "open_issues": [],
        "proposed_patch": proposed_patch,
    }


def test_read_only_live_run_not_marked_as_patch_apply_failure(tmp_path: Path) -> None:
    ctx = _minimal_ctx(allowed_changes=[])
    impl = _read_only_impl_result(proposed_patch=None)
    checks = run_session._apply_patch_validate_and_run_local_checks(
        session_dir=tmp_path,
        ctx=ctx,
        impl_result=impl,
        prepared_spec={"allowed_changes": []},
        max_changed_files=5,
        skip_build=True,
        session_id=ctx.session_id,
    )
    assert checks.get("success") is True
    assert checks.get("patch_apply_failed") is not True
    pa = checks.get("patch_apply") or {}
    assert pa.get("status") != "failed"


def test_read_only_live_run_does_not_trigger_retry(tmp_path: Path) -> None:
    ctx = _minimal_ctx(allowed_changes=[])
    impl = _read_only_impl_result(proposed_patch="")
    checks = run_session._apply_patch_validate_and_run_local_checks(
        session_dir=tmp_path,
        ctx=ctx,
        impl_result=impl,
        prepared_spec={"allowed_changes": []},
        max_changed_files=5,
        skip_build=True,
        session_id=ctx.session_id,
    )
    assert checks.get("success") is True
    canonical = run_session.resolve_canonical_failure_type(checks)
    assert canonical.get("failure_type") == "no_failure"


def test_read_only_live_run_reports_consistent_non_failed_status(tmp_path: Path) -> None:
    ctx = _minimal_ctx(allowed_changes=[])
    impl = _read_only_impl_result(proposed_patch=None)
    checks = run_session._build_check_results_for_read_only_live_run()

    run_session.persist_session_reports(
        session_dir=tmp_path,
        ctx=ctx,
        prepared_spec={"objective": "read-only"},
        impl_result=impl,
        checks=checks,
        status="success",
        dry_run=False,
        started_at="2026-04-02T00:00:00+00:00",
        finished_at="2026-04-02T00:00:01+00:00",
        retry_instruction=None,
        error_message=None,
        retry_control={
            "retry_count": 0,
            "max_retries": 1,
            "retry_stopped_same_cause": False,
            "retry_stopped_max_retries": False,
        },
    )

    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert report["status"] == "success"

    session_report = json.loads((tmp_path / "reports" / "session_report.json").read_text(encoding="utf-8"))
    assert session_report["status"] == "success"


class _DummyCompletedProcess:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_normal_code_fix_sessions_still_require_patch_apply(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: List[int] = []

    def _git_run(args: List[str], *, check: bool = False) -> _DummyCompletedProcess:
        if args[:2] == ["diff", "--name-only"]:
            return _DummyCompletedProcess(returncode=0, stdout="", stderr="")
        return _DummyCompletedProcess(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(run_session, "_git_run", _git_run, raising=True)

    _real_apply = run_session.apply_proposed_patch_and_capture_artifacts

    def _spy(session_dir: Path, impl_result: Dict[str, Any], *, session_id: Any = None) -> Dict[str, Any]:
        calls.append(1)
        return _real_apply(session_dir, impl_result, session_id=session_id)

    monkeypatch.setattr(run_session, "apply_proposed_patch_and_capture_artifacts", _spy)

    def _fake_run_local_checks(ctx: run_session.SessionContext, skip_build: bool = False) -> Dict[str, Any]:
        sk: Dict[str, Any] = {
            "status": "skipped",
            "command": "",
            "returncode": None,
            "stdout": "",
            "stderr": "",
        }
        return {
            "test": dict(sk),
            "lint": dict(sk),
            "typecheck": dict(sk),
            "build": dict(sk),
            "success": True,
        }

    monkeypatch.setattr(run_session, "run_local_checks", _fake_run_local_checks)

    ctx = _minimal_ctx(allowed_changes=["orchestration/run_session.py"])
    impl = _read_only_impl_result(proposed_patch=None)

    run_session._apply_patch_validate_and_run_local_checks(
        session_dir=tmp_path,
        ctx=ctx,
        impl_result=dict(impl),
        prepared_spec={"allowed_changes": ["orchestration/run_session.py"]},
        max_changed_files=5,
        skip_build=True,
        session_id=ctx.session_id,
    )
    assert calls == [1]
