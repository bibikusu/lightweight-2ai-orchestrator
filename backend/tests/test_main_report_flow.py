# -*- coding: utf-8 -*-

import json
import sys

import pytest


def test_main_saves_report_in_expected_format(monkeypatch, tmp_path):
    """AC-03: main（dry-run）経由で .md と .json が期待形式で保存される"""
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
    assert "changed_files" in data
    assert "acceptance_results" in data
