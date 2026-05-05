"""
session-171i AC-171I-01〜07 対応テスト: run_session.py CI結果連携
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))


def _make_args(**kwargs) -> argparse.Namespace:
    """テスト用 args を生成するヘルパー。"""
    defaults = {
        "session_id": "session-test-ci",
        "execution_mode": "full_stack",
        "resume": False,
        "dry_run": False,
        "skip_build": False,
        "max_retries": None,
        "project": None,
        "batch": None,
        "use_selector": False,
        "ci_status": "success",
        "ci_failed_jobs": "",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _run_ci_check(tmp_path: Path, ci_status: str, ci_failed_jobs: str = "") -> tuple:
    """_run_single_session_impl を ci_check 直前まで実行して SystemExit を捕捉する。"""
    from orchestration import run_session

    args = _make_args(
        session_id="session-test-ci",
        ci_status=ci_status,
        ci_failed_jobs=ci_failed_jobs,
    )

    with (
        patch.object(run_session, "ensure_artifact_dirs", return_value=tmp_path),
        patch.object(run_session, "enforce_run_session_duplicate_definition_preflight"),
    ):
        try:
            run_session._run_single_session_impl(args)
            return None, None  # SystemExit なし
        except SystemExit as e:
            return e.code, tmp_path / "logs" / "error_latest.json"


# ---------------------------------------------------------------------------
# AC-171I-01: ci_status 未指定 (default=success) のとき ci_check で停止しない
# ---------------------------------------------------------------------------

def test_ci_status_defaults_to_success(tmp_path):
    """ci_status 未指定時は success 扱いで ci_check を通過する。"""
    from orchestration import run_session

    args = _make_args(session_id="session-test-ci")
    # ci_status="success" がデフォルトであることを確認
    assert args.ci_status == "success"

    with (
        patch.object(run_session, "ensure_artifact_dirs", return_value=tmp_path),
        patch.object(run_session, "enforce_run_session_duplicate_definition_preflight"),
        patch.object(run_session, "load_session_context", side_effect=FileNotFoundError("stub")),
    ):
        try:
            run_session._run_single_session_impl(args)
        except SystemExit as e:
            # ci_check 由来の exit 1 でないことを確認（FileNotFoundError による停止は許容）
            assert e.code != 1 or not (tmp_path / "logs" / "error_latest.json").exists() or (
                json.loads((tmp_path / "logs" / "error_latest.json").read_text())["stage"] != "ci_check"
            )
        except Exception:
            pass  # ci_check 通過後の別例外は許容

    # ci_check による error_latest.json が存在しないことを確認
    error_file = tmp_path / "logs" / "error_latest.json"
    if error_file.exists():
        data = json.loads(error_file.read_text())
        assert data.get("stage") != "ci_check", "ci_status=success なのに ci_check で停止した"


# ---------------------------------------------------------------------------
# AC-171I-02: ci_status=success のとき ci_check を通過する
# ---------------------------------------------------------------------------

def test_ci_status_success_continues(tmp_path):
    """ci_status=success の場合、ci_check ステージで停止しない。"""
    from orchestration import run_session

    args = _make_args(ci_status="success")

    with (
        patch.object(run_session, "ensure_artifact_dirs", return_value=tmp_path),
        patch.object(run_session, "enforce_run_session_duplicate_definition_preflight"),
        patch.object(run_session, "load_session_context", side_effect=FileNotFoundError("stub")),
    ):
        try:
            run_session._run_single_session_impl(args)
        except (SystemExit, Exception):
            pass  # ci_check 通過後の別例外は許容

    error_file = tmp_path / "logs" / "error_latest.json"
    if error_file.exists():
        data = json.loads(error_file.read_text())
        assert data.get("stage") != "ci_check", "ci_status=success なのに ci_check で停止した"


# ---------------------------------------------------------------------------
# AC-171I-03: ci_status=failure のとき exit 1 で停止する
# ---------------------------------------------------------------------------

def test_ci_status_failure_exits_one(tmp_path):
    """ci_status=failure の場合、exit code 1 で停止する。"""
    exit_code, _ = _run_ci_check(tmp_path, ci_status="failure")
    assert exit_code == 1, f"expected exit 1, got {exit_code}"


# ---------------------------------------------------------------------------
# AC-171I-04: ci_status=failure のとき error_type = test_failure
# ---------------------------------------------------------------------------

def test_ci_failure_maps_to_test_failure(tmp_path):
    """ci_status=failure の場合、error_type は test_failure になる。"""
    exit_code, error_file = _run_ci_check(tmp_path, ci_status="failure")
    assert exit_code == 1
    assert error_file is not None and error_file.exists(), "error_latest.json が存在しない"
    data = json.loads(error_file.read_text())
    assert data["error_type"] == "test_failure", f"error_type={data.get('error_type')}"


# ---------------------------------------------------------------------------
# AC-171I-05: ci_status=failure のとき stage=ci_check が記録される
# ---------------------------------------------------------------------------

def test_ci_failure_writes_ci_check_error_log(tmp_path):
    """ci_status=failure の場合、error_latest.json の stage が ci_check になる。"""
    exit_code, error_file = _run_ci_check(tmp_path, ci_status="failure")
    assert exit_code == 1
    assert error_file is not None and error_file.exists()
    data = json.loads(error_file.read_text())
    assert data["stage"] == "ci_check", f"stage={data.get('stage')}"
    assert "CI failed" in data.get("message", ""), f"message={data.get('message')}"


# ---------------------------------------------------------------------------
# AC-171I-06: ci_failed_jobs が error_latest.json に記録される
# ---------------------------------------------------------------------------

def test_ci_failed_jobs_written_to_error_log(tmp_path):
    """ci_failed_jobs が error_latest.json に正しく記録される。"""
    exit_code, error_file = _run_ci_check(
        tmp_path, ci_status="failure", ci_failed_jobs="build,test-unit"
    )
    assert exit_code == 1
    assert error_file is not None and error_file.exists()
    data = json.loads(error_file.read_text())
    assert "ci_failed_jobs" in data, "ci_failed_jobs フィールドが存在しない"
    assert data["ci_failed_jobs"] == ["build", "test-unit"], (
        f"ci_failed_jobs={data.get('ci_failed_jobs')}"
    )


# ---------------------------------------------------------------------------
# AC-171I-07: 変更範囲は allowed_changes 2 件限定
# ---------------------------------------------------------------------------

def test_session_171i_scope_limited():
    """git diff --name-only origin/main..HEAD が allowed_changes 2 件のみを返す。"""
    result = subprocess.run(
        ["git", "diff", "--name-only", "origin/main..HEAD"],
        capture_output=True,
        text=True,
        cwd=str(ROOT_DIR),
    )
    changed = [f.strip() for f in result.stdout.splitlines() if f.strip()]
    allowed = {
        "orchestration/run_session.py",
        "tests/test_run_session_ci_integration.py",
    }
    extra = set(changed) - allowed
    assert not extra, f"allowed_changes 外のファイルが変更されている: {extra}"
    assert set(changed) == allowed, (
        f"expected exactly {allowed}, got {set(changed)}"
    )
