from __future__ import annotations

import json
from pathlib import Path

import pytest


def _sessions() -> list[dict[str, object]]:
    return [
        {
            "session_id": "session-alpha",
            "project_id": "P_LOW",
            "priority_rank_value": 10,
        },
        {
            "session_id": "session-beta",
            "project_id": "P_HIGH",
            "priority_rank_value": 30,
        },
    ]


def _policy() -> dict[str, object]:
    return {
        "queues": {
            "daytime": {
                "priority_order": ["critical", "high", "medium", "low"],
            },
        },
        "project_priority": {
            "risk_to_priority": {
                "critical": "critical",
                "high": "high",
                "medium": "medium",
                "low": "low",
            },
        },
    }


def _registry() -> dict[str, object]:
    return {
        "projects": [
            {"project_id": "P_LOW", "deploy_risk": "low"},
            {"project_id": "P_HIGH", "deploy_risk": "high"},
        ],
    }


def _setup_dir(
    tmp_path: Path,
    sessions: list[dict[str, object]] | None = None,
) -> tuple[Path, Path, Path]:
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    for session in sessions or _sessions():
        p = sessions_dir / f"{session['session_id']}.json"
        p.write_text(json.dumps(session), encoding="utf-8")

    registry_path = tmp_path / "project_registry.json"
    registry_path.write_text(json.dumps(_registry()), encoding="utf-8")

    policy_path = tmp_path / "queue_policy.yaml"
    policy_path.write_text(
        "queues:\n  daytime:\n    priority_order: [critical, high, medium, low]\n"
        "project_priority:\n  risk_to_priority:\n    critical: critical\n"
        "    high: high\n    medium: medium\n    low: low\n",
        encoding="utf-8",
    )
    return sessions_dir, registry_path, policy_path


def test_no_dry_run_exits_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """--dry-run なしで exit 2 かつ stderr にメッセージが出る（AC-156b-08）。"""
    from orchestration.select_next import main

    sessions_dir, registry_path, policy_path = _setup_dir(tmp_path)
    exit_code = main(
        [
            "--sessions-dir", str(sessions_dir),
            "--registry", str(registry_path),
            "--policy", str(policy_path),
        ]
    )

    assert exit_code == 2
    captured = capsys.readouterr()
    assert "--dry-run is required in current scope (session-156b)" in captured.err


def test_dry_run_exits_0(tmp_path: Path) -> None:
    """--dry-run で exit 0（AC-156b-01）。"""
    from orchestration.select_next import main

    sessions_dir, registry_path, policy_path = _setup_dir(tmp_path)
    exit_code = main(
        [
            "--dry-run",
            "--sessions-dir", str(sessions_dir),
            "--registry", str(registry_path),
            "--policy", str(policy_path),
        ]
    )

    assert exit_code == 0


def test_output_contains_required_keys(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """出力 JSON に必須 5 キーが含まれる（AC-156b-03）。"""
    from orchestration.select_next import main

    sessions_dir, registry_path, policy_path = _setup_dir(tmp_path)
    main(
        [
            "--dry-run",
            "--sessions-dir", str(sessions_dir),
            "--registry", str(registry_path),
            "--policy", str(policy_path),
        ]
    )

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    for key in ("candidate_sessions", "selected_session_id", "selection_reason", "execution_mode", "metadata"):
        assert key in output, f"missing key: {key}"


def test_output_is_valid_json(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """標準出力が JSON として parse できる（AC-156b-01）。"""
    from orchestration.select_next import main

    sessions_dir, registry_path, policy_path = _setup_dir(tmp_path)
    main(
        [
            "--dry-run",
            "--sessions-dir", str(sessions_dir),
            "--registry", str(registry_path),
            "--policy", str(policy_path),
        ]
    )

    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert isinstance(parsed, dict)


def test_metadata_contains_status_field_scan(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """metadata に status_field_scan が含まれ、4 キーが存在する。"""
    from orchestration.select_next import main

    sessions_dir, registry_path, policy_path = _setup_dir(tmp_path)
    main(
        [
            "--dry-run",
            "--sessions-dir", str(sessions_dir),
            "--registry", str(registry_path),
            "--policy", str(policy_path),
        ]
    )

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    scan = output["metadata"]["status_field_scan"]
    for key in ("total_sessions", "has_status", "no_status", "pending_count"):
        assert key in scan, f"missing scan key: {key}"
    assert scan["total_sessions"] == 2
    assert scan["has_status"] == 0
    assert scan["no_status"] == 2
    assert scan["pending_count"] == 0


def test_status_field_scan_with_pending(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """status == 'pending' が存在する場合に pending_count が正確に計算される。"""
    from orchestration.select_next import main

    sessions = [
        {"session_id": "session-x", "project_id": "P_LOW", "priority_rank_value": 5, "status": "pending"},
        {"session_id": "session-y", "project_id": "P_HIGH", "priority_rank_value": 10, "status": "done"},
        {"session_id": "session-z", "project_id": "P_LOW", "priority_rank_value": 1},
    ]
    sessions_dir, registry_path, policy_path = _setup_dir(tmp_path, sessions)
    main(
        [
            "--dry-run",
            "--sessions-dir", str(sessions_dir),
            "--registry", str(registry_path),
            "--policy", str(policy_path),
        ]
    )

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    scan = output["metadata"]["status_field_scan"]
    assert scan["total_sessions"] == 3
    assert scan["has_status"] == 2
    assert scan["no_status"] == 1
    assert scan["pending_count"] == 1


def test_skipped_sessions_recorded(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """invalid JSON が skipped_sessions に記録される（AC-156b-05）。"""
    from orchestration.select_next import main

    sessions_dir, registry_path, policy_path = _setup_dir(tmp_path)
    broken = sessions_dir / "session-broken.json"
    broken.write_text('{"session_id": "session-broken",', encoding="utf-8")

    main(
        [
            "--dry-run",
            "--sessions-dir", str(sessions_dir),
            "--registry", str(registry_path),
            "--policy", str(policy_path),
        ]
    )

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    skipped = output["metadata"]["skipped_sessions"]
    assert len(skipped) == 1
    assert skipped[0]["reason"] == "json_parse_error"
    assert "session-broken" not in output["candidate_sessions"]


def test_dry_run_no_side_effects(tmp_path: Path) -> None:
    """dry-run 実行後にセッションファイルが変更されない（AC-156b-02）。"""
    from orchestration.select_next import main

    sessions_dir, registry_path, policy_path = _setup_dir(tmp_path)
    session_file = sessions_dir / "session-alpha.json"
    mtime_before = session_file.stat().st_mtime

    main(
        [
            "--dry-run",
            "--sessions-dir", str(sessions_dir),
            "--registry", str(registry_path),
            "--policy", str(policy_path),
        ]
    )

    assert session_file.stat().st_mtime == mtime_before
    assert not (tmp_path / "artifacts").exists()


def test_candidates_include_all_sessions(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """案 C: status フィルタなし — 全 session が candidate に含まれる。"""
    from orchestration.select_next import main

    sessions = [
        {"session_id": "session-p", "project_id": "P_LOW", "priority_rank_value": 5, "status": "pending"},
        {"session_id": "session-d", "project_id": "P_HIGH", "priority_rank_value": 10, "status": "done"},
        {"session_id": "session-n", "project_id": "P_LOW", "priority_rank_value": 1},
    ]
    sessions_dir, registry_path, policy_path = _setup_dir(tmp_path, sessions)
    main(
        [
            "--dry-run",
            "--sessions-dir", str(sessions_dir),
            "--registry", str(registry_path),
            "--policy", str(policy_path),
        ]
    )

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    candidates = output["candidate_sessions"]
    assert "session-p" in candidates
    assert "session-d" in candidates
    assert "session-n" in candidates
