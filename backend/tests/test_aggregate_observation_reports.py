# -*- coding: utf-8 -*-
"""session-119: artifacts report 集計スクリプトの単体テスト。"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[2]


def _aggregate_module():
    path = ROOT_DIR / "scripts" / "aggregate_observation_reports.py"
    spec = importlib.util.spec_from_file_location("aggregate_observation_reports", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


agg = _aggregate_module()


def _write_report(
    base: Path,
    dir_name: str,
    *,
    session_id: str,
    status: str,
    failure_type: object,
    completion_status: str,
    changed_files: list | None = None,
) -> Path:
    d = base / dir_name
    d.mkdir(parents=True, exist_ok=True)
    payload = {
        "session_id": session_id,
        "status": status,
        "failure_type": failure_type,
        "completion_status": completion_status,
        "changed_files": changed_files if changed_files is not None else [],
    }
    (d / "report.json").write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )
    return d


def _prime_retry(session_dir: Path, n: int) -> None:
    rdir = session_dir / "responses"
    rdir.mkdir(parents=True, exist_ok=True)
    (rdir / "retry_state.json").write_text(
        json.dumps({"retry_count": n}, ensure_ascii=False),
        encoding="utf-8",
    )


def test_aggregate_reports_computes_success_rate_and_failure_distribution(tmp_path: Path) -> None:
    """AC-119-01: 成功率と failure_type 分布。"""
    art = tmp_path / "artifacts"
    _write_report(
        art,
        "session-a",
        session_id="session-a",
        status="success",
        failure_type=None,
        completion_status="review_required",
    )
    _write_report(
        art,
        "session-b",
        session_id="session-b",
        status="failed",
        failure_type="test_failure",
        completion_status="retry_required",
    )
    _write_report(
        art,
        "session-c",
        session_id="session-c",
        status="success",
        failure_type=None,
        completion_status="review_required",
        changed_files=["a.py"],
    )
    # report なしのディレクトリ（スキャンにだけ載る）
    (art / "session-empty").mkdir(parents=True, exist_ok=True)

    doc = agg.build_dashboard_document(art)
    assert doc["sessions_scanned"] == 4
    assert doc["sessions_with_report"] == 3
    assert doc["success_count"] == 2
    assert doc["failed_count"] == 1
    assert doc["success_rate"] == pytest.approx(2.0 / 3.0)
    dist = doc["failure_type_distribution"]
    assert dist.get("__success__") == 2
    assert dist.get("test_failure") == 1


def test_aggregate_reports_computes_retry_stats(tmp_path: Path) -> None:
    """AC-119-02: retry_state.json がある場合の retry 統計。"""
    art = tmp_path / "artifacts"
    d1 = _write_report(
        art,
        "s1",
        session_id="s1",
        status="success",
        failure_type=None,
        completion_status="review_required",
    )
    _prime_retry(d1, 2)
    _write_report(
        art,
        "s2",
        session_id="s2",
        status="success",
        failure_type=None,
        completion_status="review_required",
    )
    d3 = _write_report(
        art,
        "s3",
        session_id="s3",
        status="failed",
        failure_type="lint_failure",
        completion_status="stopped",
    )
    _prime_retry(d3, 1)

    doc = agg.build_dashboard_document(art)
    rs = doc["retry_stats"]
    assert rs["sessions_with_retry_state_file"] == 2
    assert rs["total_retry_count"] == 3
    assert rs["avg_retry_count"] == pytest.approx(1.0)
    assert rs["max_retry_count"] == 2
    assert rs["retry_histogram"] == {"0": 1, "1": 1, "2": 1}


def test_aggregate_reports_writes_markdown_summary(tmp_path: Path) -> None:
    """AC-119-03: Markdown に summary と session 行がある。"""
    art = tmp_path / "artifacts"
    d = _write_report(
        art,
        "sx",
        session_id="sx",
        status="success",
        failure_type=None,
        completion_status="review_required",
        changed_files=[],
    )
    _prime_retry(d, 0)

    doc = agg.build_dashboard_document(art)
    md = agg.render_markdown(doc)
    assert "## Summary" in md
    assert "### failure_type_distribution" in md
    assert "### retry_stats" in md
    assert "### changed_files_stats" in md
    assert "## Sessions" in md
    assert "| session_id |" in md
    assert "sx" in md

    out = tmp_path / "out"
    agg.write_dashboard(doc, out, json_name="x.json", md_name="x.md")
    assert (out / "x.md").is_file()
    assert (out / "x.json").is_file()


def test_aggregate_reports_passes_validation_suite() -> None:
    """AC-119-04: 追加後も標準4コマンド相当が通る（CI の .venv 前提）。

    注: 本テスト内の pytest は自身を除外する（再帰 subprocess 防止）。
    """
    venv_bin = ROOT_DIR / ".venv" / "bin"
    ruff_exe = venv_bin / "ruff"
    pytest_exe = venv_bin / "pytest"
    mypy_exe = venv_bin / "python"
    if not ruff_exe.is_file() or not pytest_exe.is_file() or not mypy_exe.is_file():
        pytest.skip("ローカルは python -m venv .venv && pip install -r requirements.txt 済みを推奨")

    checks = [
        [str(ruff_exe), "check", str(ROOT_DIR)],
        [
            str(pytest_exe),
            str(ROOT_DIR / "backend" / "tests"),
            "-q",
            "-k",
            "not test_aggregate_reports_passes_validation_suite",
        ],
        [
            str(mypy_exe),
            "-m",
            "mypy",
            "--explicit-package-bases",
            "orchestration",
            "--ignore-missing-imports",
        ],
        [
            str(mypy_exe),
            "-m",
            "compileall",
            "-q",
            "-f",
            str(ROOT_DIR / "orchestration"),
            str(ROOT_DIR / "backend"),
        ],
    ]
    with tempfile.TemporaryDirectory(prefix="compileall_pyc_") as pyc_prefix:
        env = {
            **os.environ,
            "PYTHONPATH": str(ROOT_DIR),
            "PYTHONPYCACHEPREFIX": pyc_prefix,
        }
        for cmd in checks:
            proc = subprocess.run(
                cmd,
                cwd=ROOT_DIR,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            assert proc.returncode == 0, (cmd, proc.stdout, proc.stderr)