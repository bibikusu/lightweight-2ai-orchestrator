# -*- coding: utf-8 -*-

import json
import sys

import pytest


def test_success_flow_writes_normalized_session_report(monkeypatch, tmp_path):
    """AC-09-04: 成功フローで正規化済み session_report.json が出力される"""
    import orchestration.run_session as rs

    monkeypatch.setattr(rs, "ARTIFACTS_DIR", tmp_path / "artifacts")
    monkeypatch.setattr(sys, "argv", ["run_session.py", "--dry-run", "--session-id", "session-01"])

    code = rs.main()
    assert code == 0

    reports = tmp_path / "artifacts" / "session-01" / "reports"
    md_path = reports / "session_report.md"
    json_path = reports / "session_report.json"

    assert md_path.is_file()
    assert json_path.is_file()

    md_text = md_path.read_text(encoding="utf-8")
    assert md_text.startswith("# Session Report:")
    with pytest.raises(json.JSONDecodeError):
        json.loads(md_text)

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["session_id"] == "session-01"
    assert data["status"] == "success"
    assert data["completion"] in ("review_required", "retry_required", "stopped")
    for key in (
        "changed_files",
        "test_result",
        "lint_result",
        "typecheck_result",
        "build_result",
        "acceptance_results",
        "risks",
        "open_issues",
        "diff_summary",
    ):
        assert key in data
