"""tests/test_auto_runner.py: orchestration/auto_runner.py の単体テスト。"""
import json
from typing import Optional
from unittest.mock import MagicMock, call, patch

import pytest

from orchestration.auto_runner import run_auto_runner

SELECTOR_CMD = ["python3", "dummy_selector.py"]
QUEUE_CFG = "docs/config/queue_policy.yaml"


def _make_proc(returncode: int = 0, stdout: str = "") -> MagicMock:
    proc = MagicMock()
    proc.returncode = returncode
    proc.stdout = stdout
    return proc


def _selector_output(session_id: Optional[str]) -> str:
    return json.dumps({"selected_session_id": session_id})


# ────────────────────────────────────────
# 必須 4 件
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
# 推奨 3 件
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
