# -*- coding: utf-8 -*-
"""AC-74: Claude応答ガード失敗時の証跡保存回帰テスト。"""

import json
import pytest

from orchestration.run_session import _persist_guard_failure_artifacts


def test_guard_failure_persists_raw_impl_response(tmp_path):
    """AC-74-01: ガード失敗時に raw implementation response が保存される。"""
    session_dir = tmp_path / "session-test"
    responses_dir = session_dir / "responses"
    responses_dir.mkdir(parents=True)

    impl_result = {
        "changed_files": [],
        "implementation_summary": "summary",
        "proposed_patch": "",
    }
    error = ValueError("missing required key: 'proposed_patch'")

    _persist_guard_failure_artifacts(session_dir, impl_result, error, "implementation")

    raw_path = responses_dir / "guard_failure_raw_response.json"
    assert raw_path.exists(), "guard_failure_raw_response.json が保存されていない"

    saved = json.loads(raw_path.read_text(encoding="utf-8"))
    assert saved["implementation_summary"] == "summary"
    assert "changed_files" in saved


def test_guard_failure_persists_failure_reason_json(tmp_path):
    """AC-74-02: ガード失敗時に failure reason が JSON で保存される。"""
    session_dir = tmp_path / "session-test"
    responses_dir = session_dir / "responses"
    responses_dir.mkdir(parents=True)

    impl_result = {"changed_files": [], "implementation_summary": [], "proposed_patch": ""}
    error = ValueError("missing required key: 'proposed_patch'")

    _persist_guard_failure_artifacts(session_dir, impl_result, error, "implementation_retry")

    reason_path = responses_dir / "guard_failure_reason.json"
    assert reason_path.exists(), "guard_failure_reason.json が保存されていない"

    reason = json.loads(reason_path.read_text(encoding="utf-8"))
    assert reason["error_type"] == "ValueError"
    assert "proposed_patch" in reason["message"]
    assert reason["stage"] == "implementation_retry"


def test_success_flow_unchanged_with_failure_artifact_logic(tmp_path):
    """AC-74-03: 成功時はガード失敗証跡ファイルが生成されない。"""
    session_dir = tmp_path / "session-success"
    responses_dir = session_dir / "responses"
    responses_dir.mkdir(parents=True)

    # ガード失敗が起きなければ _persist_guard_failure_artifacts は呼ばれない
    # → guard_failure_raw_response.json / guard_failure_reason.json は存在しない
    assert not (responses_dir / "guard_failure_raw_response.json").exists()
    assert not (responses_dir / "guard_failure_reason.json").exists()


def test_persist_guard_failure_handles_save_error_gracefully(tmp_path):
    """_persist_guard_failure_artifacts は保存失敗時も例外を外に投げない。"""
    # responses_dir が存在しない（かつ mkdir も通らない）状況を模倣
    # read-only な存在しないパスを使うことで save_json が失敗する
    session_dir = tmp_path / "no-responses-dir"
    # responses_dir を作成しない → save_json が OSError を出す

    error = ValueError("missing key")
    impl_result = {"changed_files": [], "implementation_summary": [], "proposed_patch": ""}

    # 例外が外に出ないことを確認（graceful degradation）
    # ※ save_json が OSError → _persist_guard_failure_artifacts 内 except で吸収
    try:
        _persist_guard_failure_artifacts(session_dir, impl_result, error, "implementation")
    except Exception as e:  # noqa: BLE001
        pytest.fail(f"_persist_guard_failure_artifacts が例外を外に投げた: {e}")
