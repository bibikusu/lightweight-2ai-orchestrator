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
    assert "__success__" not in dist
    assert dist.get("test_failure") == 1
    assert sum(dist.values()) == doc["failed_count"]


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


def test_dashboard_status_counts_match_sessions_with_report(tmp_path: Path) -> None:
    """AC-13-01: レポートありセッション数と status 区分カウントの整合。"""
    art = tmp_path / "artifacts"
    _write_report(
        art,
        "s-ok",
        session_id="s-ok",
        status="success",
        failure_type=None,
        completion_status="review_required",
    )
    _write_report(
        art,
        "s-ng",
        session_id="s-ng",
        status="failed",
        failure_type="test_failure",
        completion_status="stopped",
    )
    _write_report(
        art,
        "s-other",
        session_id="s-other",
        status="timeout",
        failure_type=None,
        completion_status="__unknown__",
    )
    doc = agg.build_dashboard_document(art)
    assert (
        doc["sessions_with_report"]
        == doc["success_count"] + doc["failed_count"] + doc["other_status_count"]
    )


def test_failure_type_distribution_counts_failed_rows_only(tmp_path: Path) -> None:
    """AC-13-02: failure_type 分布は failed のみ（__success__ なし）。"""
    art = tmp_path / "artifacts"
    _write_report(
        art,
        "a",
        session_id="a",
        status="success",
        failure_type=None,
        completion_status="review_required",
    )
    _write_report(
        art,
        "b",
        session_id="b",
        status="failed",
        failure_type="lint_failure",
        completion_status="stopped",
    )
    doc = agg.build_dashboard_document(art)
    dist = doc["failure_type_distribution"]
    assert "__success__" not in dist
    assert dist == {"lint_failure": 1}


def test_failure_type_distribution_total_matches_failed_count(tmp_path: Path) -> None:
    """AC-13-03: failure_type 分布の合計が failed_count と一致。"""
    art = tmp_path / "artifacts"
    for i, ft in enumerate(["a", "b", None]):
        _write_report(
            art,
            f"f{i}",
            session_id=f"f{i}",
            status="failed",
            failure_type=ft,
            completion_status="stopped",
        )
    _write_report(
        art,
        "ok",
        session_id="ok",
        status="success",
        failure_type=None,
        completion_status="review_required",
    )
    doc = agg.build_dashboard_document(art)
    assert doc["failed_count"] == 3
    dist = doc["failure_type_distribution"]
    assert "__success__" not in dist
    assert dist.get("a") == 1
    assert dist.get("b") == 1
    assert dist.get("__missing_failure_type__") == 1
    assert sum(dist.values()) == 3


def test_failed_rows_with_empty_failure_type_are_not_bucketed_as_success(
    tmp_path: Path,
) -> None:
    """AC-13-04: failed かつ failure_type 欠損は __success__ に載せない。"""
    art = tmp_path / "artifacts"
    _write_report(
        art,
        "untyped",
        session_id="untyped",
        status="failed",
        failure_type=None,
        completion_status="stopped",
    )
    _write_report(
        art,
        "blank",
        session_id="blank",
        status="failed",
        failure_type="   ",
        completion_status="stopped",
    )
    doc = agg.build_dashboard_document(art)
    dist = doc["failure_type_distribution"]
    assert "__success__" not in dist
    assert dist.get("__missing_failure_type__") == 2


def test_dashboard_output_labels_match_aggregation_rule(tmp_path: Path) -> None:
    """AC-13-05: Markdown の failure_type 説明が集計ルールと矛盾しない。"""
    art = tmp_path / "artifacts"
    _write_report(
        art,
        "x",
        session_id="x",
        status="failed",
        failure_type="t",
        completion_status="stopped",
    )
    doc = agg.build_dashboard_document(art)
    md = agg.render_markdown(doc)
    assert "`status` が `failed`" in md
    assert "__missing_failure_type__" in md
    assert "`__success__` キーは使わない" in md
