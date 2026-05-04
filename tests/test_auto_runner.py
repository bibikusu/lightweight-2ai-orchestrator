"""tests/test_auto_runner.py: orchestration/auto_runner.py の単体テスト。"""
import json
import re
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, call, patch

import pytest

from orchestration.auto_runner import _call_run_session, run_auto_runner

SELECTOR_CMD = ["python3", "dummy_selector.py"]
QUEUE_CFG = "docs/config/queue_policy.yaml"
RUN_SESSION_BASE = [".venv/bin/python", "orchestration/run_session.py"]


def _make_proc(returncode: int = 0, stdout: str = "", stderr: str = "") -> MagicMock:
    proc = MagicMock()
    proc.returncode = returncode
    proc.stdout = stdout
    proc.stderr = stderr
    return proc


def _selector_output(session_id: Optional[str]) -> str:
    return json.dumps({"selected_session_id": session_id})


# ────────────────────────────────────────
# 既存 必須 4 件
# ────────────────────────────────────────


@patch("orchestration.auto_runner.subprocess.run")
def test_auto_runner_stops_at_max_iterations(mock_run: MagicMock) -> None:
    mock_run.return_value = _make_proc(stdout=_selector_output("session-119"))

    result = run_auto_runner(
        max_iterations=2,
        dry_run=False,
        selector_command=SELECTOR_CMD,
        queue_config_path=QUEUE_CFG,
    )

    assert result["stopped_reason"] == "max_iterations_reached"
    assert len(result["iterations"]) == 2


@patch("orchestration.auto_runner.subprocess.run")
def test_auto_runner_dry_run_does_not_execute_run_session(mock_run: MagicMock) -> None:
    mock_run.return_value = _make_proc(stdout=_selector_output("session-119"))

    result = run_auto_runner(
        max_iterations=5,
        dry_run=True,
        selector_command=SELECTOR_CMD,
        queue_config_path=QUEUE_CFG,
    )

    assert result["stopped_reason"] == "dry_run_completed"
    assert len(result["iterations"]) == 1
    # subprocess.run が 1 回だけ呼ばれ、selector_command のみ渡されている
    assert mock_run.call_count == 1
    assert mock_run.call_args == call(SELECTOR_CMD, capture_output=True, text=True)


@patch("orchestration.auto_runner.subprocess.run")
def test_auto_runner_returns_no_candidate_when_selector_has_no_selection(
    mock_run: MagicMock,
) -> None:
    mock_run.return_value = _make_proc(stdout=_selector_output(None))

    result = run_auto_runner(
        max_iterations=3,
        dry_run=False,
        selector_command=SELECTOR_CMD,
        queue_config_path=QUEUE_CFG,
    )

    assert result["stopped_reason"] == "no_candidate"
    assert len(result["iterations"]) == 0


@patch("orchestration.auto_runner.subprocess.run")
def test_auto_runner_records_selected_session_id(mock_run: MagicMock) -> None:
    mock_run.return_value = _make_proc(stdout=_selector_output("session-119"))

    result = run_auto_runner(
        max_iterations=1,
        dry_run=False,
        selector_command=SELECTOR_CMD,
        queue_config_path=QUEUE_CFG,
    )

    assert result["iterations"][0]["selected_session_id"] == "session-119"


# ────────────────────────────────────────
# 既存 推奨 3 件
# ────────────────────────────────────────


@patch("orchestration.auto_runner.subprocess.run")
def test_auto_runner_returns_failed_when_selector_subprocess_fails(
    mock_run: MagicMock,
) -> None:
    mock_run.return_value = _make_proc(returncode=1, stdout="")

    result = run_auto_runner(
        max_iterations=3,
        dry_run=False,
        selector_command=SELECTOR_CMD,
        queue_config_path=QUEUE_CFG,
    )

    assert result["stopped_reason"] == "failed"


@patch("orchestration.auto_runner.subprocess.run")
def test_auto_runner_returns_failed_when_selector_outputs_invalid_json(
    mock_run: MagicMock,
) -> None:
    mock_run.return_value = _make_proc(stdout="not-valid-json{{")

    result = run_auto_runner(
        max_iterations=3,
        dry_run=False,
        selector_command=SELECTOR_CMD,
        queue_config_path=QUEUE_CFG,
    )

    assert result["stopped_reason"] == "failed"


def test_auto_runner_rejects_non_positive_max_iterations() -> None:
    with pytest.raises(ValueError):
        run_auto_runner(
            max_iterations=0,
            dry_run=False,
            selector_command=SELECTOR_CMD,
            queue_config_path=QUEUE_CFG,
        )

    with pytest.raises(ValueError):
        run_auto_runner(
            max_iterations=-1,
            dry_run=False,
            selector_command=SELECTOR_CMD,
            queue_config_path=QUEUE_CFG,
        )


# ────────────────────────────────────────
# _call_run_session: command shape 検証
# ────────────────────────────────────────


@patch("orchestration.auto_runner.subprocess.run")
def test_call_run_session_uses_correct_base_command(mock_run: MagicMock, tmp_path: Path) -> None:
    mock_run.return_value = _make_proc(returncode=0)

    _call_run_session("session-test", log_dir=tmp_path)

    cmd = mock_run.call_args[0][0]
    assert cmd[:2] == RUN_SESSION_BASE
    assert "--session-id" in cmd
    assert "session-test" in cmd


@patch("orchestration.auto_runner.subprocess.run")
def test_call_run_session_adds_dry_run_flag(mock_run: MagicMock, tmp_path: Path) -> None:
    mock_run.return_value = _make_proc(returncode=0)

    _call_run_session("session-test", dry_run=True, log_dir=tmp_path)

    cmd = mock_run.call_args[0][0]
    assert "--dry-run" in cmd


@patch("orchestration.auto_runner.subprocess.run")
def test_call_run_session_adds_project_flag(mock_run: MagicMock, tmp_path: Path) -> None:
    mock_run.return_value = _make_proc(returncode=0)

    _call_run_session("session-test", project="my-project", log_dir=tmp_path)

    cmd = mock_run.call_args[0][0]
    assert "--project" in cmd
    idx = cmd.index("--project")
    assert cmd[idx + 1] == "my-project"


@patch("orchestration.auto_runner.subprocess.run")
def test_call_run_session_adds_execution_mode_flag(mock_run: MagicMock, tmp_path: Path) -> None:
    mock_run.return_value = _make_proc(returncode=0)

    _call_run_session("session-test", execution_mode="fast_path", log_dir=tmp_path)

    cmd = mock_run.call_args[0][0]
    assert "--execution-mode" in cmd
    idx = cmd.index("--execution-mode")
    assert cmd[idx + 1] == "fast_path"


# ────────────────────────────────────────
# _call_run_session: stdout/stderr ログ保存
# ────────────────────────────────────────


@patch("orchestration.auto_runner.subprocess.run")
def test_call_run_session_saves_stdout_stderr_to_log_dir(
    mock_run: MagicMock, tmp_path: Path
) -> None:
    mock_run.return_value = _make_proc(returncode=0, stdout="hello stdout", stderr="hello stderr")

    _call_run_session("session-save-test", log_dir=tmp_path)

    assert (tmp_path / "session-save-test_stdout.txt").read_text() == "hello stdout"
    assert (tmp_path / "session-save-test_stderr.txt").read_text() == "hello stderr"


@patch("orchestration.auto_runner.subprocess.run")
def test_call_run_session_creates_log_dir_if_missing(
    mock_run: MagicMock, tmp_path: Path
) -> None:
    mock_run.return_value = _make_proc(returncode=0)
    nested = tmp_path / "a" / "b" / "c"

    _call_run_session("session-mkdir-test", log_dir=nested)

    assert nested.is_dir()


# ────────────────────────────────────────
# _call_run_session: returncode → status
# ────────────────────────────────────────


@patch("orchestration.auto_runner.subprocess.run")
def test_call_run_session_returns_success_on_returncode_0(
    mock_run: MagicMock, tmp_path: Path
) -> None:
    mock_run.return_value = _make_proc(returncode=0)

    result = _call_run_session("session-ok", log_dir=tmp_path)

    assert result["status"] == "success"
    assert result["returncode"] == 0


@patch("orchestration.auto_runner.subprocess.run")
def test_call_run_session_returns_failed_on_nonzero_returncode(
    mock_run: MagicMock, tmp_path: Path
) -> None:
    mock_run.return_value = _make_proc(returncode=2)

    result = _call_run_session("session-fail", log_dir=tmp_path)

    assert result["status"] == "failed"
    assert result["returncode"] == 2


# ────────────────────────────────────────
# run_auto_runner: run_session 統合検証
# ────────────────────────────────────────


@patch("orchestration.auto_runner.subprocess.run")
def test_run_auto_runner_calls_run_session_when_not_dry_run(
    mock_run: MagicMock, tmp_path: Path
) -> None:
    selector_proc = _make_proc(stdout=_selector_output("session-119"))
    run_session_proc = _make_proc(returncode=0)
    mock_run.side_effect = [selector_proc, run_session_proc]

    result = run_auto_runner(
        max_iterations=1,
        dry_run=False,
        selector_command=SELECTOR_CMD,
        queue_config_path=QUEUE_CFG,
        log_dir=tmp_path,
    )

    assert mock_run.call_count == 2
    run_session_cmd = mock_run.call_args_list[1][0][0]
    assert run_session_cmd[:2] == RUN_SESSION_BASE
    assert "--session-id" in run_session_cmd
    assert "session-119" in run_session_cmd
    assert result["iterations"][0]["queue_state"] == "completed"


@patch("orchestration.auto_runner.subprocess.run")
def test_run_auto_runner_run_session_failure_stops_loop(
    mock_run: MagicMock, tmp_path: Path
) -> None:
    selector_proc = _make_proc(stdout=_selector_output("session-119"))
    run_session_fail = _make_proc(returncode=1)
    mock_run.side_effect = [selector_proc, run_session_fail]

    result = run_auto_runner(
        max_iterations=5,
        dry_run=False,
        selector_command=SELECTOR_CMD,
        queue_config_path=QUEUE_CFG,
        log_dir=tmp_path,
    )

    assert result["stopped_reason"] == "failed"
    assert result["iterations"][0]["queue_state"] == "failed"


# ────────────────────────────────────────
# import 境界 ガード
# ────────────────────────────────────────


def test_auto_runner_does_not_import_run_session_module() -> None:
    src = Path("orchestration/auto_runner.py").read_text()
    forbidden_patterns = [
        r"from orchestration\.run_session",
        r"import orchestration\.run_session",
        r"from \.run_session",
    ]
    for pattern in forbidden_patterns:
        assert not re.search(pattern, src), f"forbidden import found: {pattern}"
