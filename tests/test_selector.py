from __future__ import annotations

import json
import re
from pathlib import Path


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


def _sessions() -> list[dict[str, object]]:
    return [
        {
            "session_id": "session-low",
            "project_id": "P_LOW",
            "priority_rank_value": 10,
        },
        {
            "session_id": "session-high",
            "project_id": "P_HIGH",
            "priority_rank_value": 30,
        },
    ]


def test_selector_module_exists() -> None:
    from orchestration.selector import core, loader, writer

    assert core is not None
    assert loader is not None
    assert writer is not None


def test_candidate_generation(tmp_path: Path) -> None:
    from orchestration.selector import core, loader

    assert core.generate_candidates([]) == []

    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    for session in _sessions():
        path = sessions_dir / f"{session['session_id']}.json"
        path.write_text(json.dumps(session), encoding="utf-8")

    loaded = loader.load_session_definitions(sessions_dir / "*.json")
    assert core.generate_candidates(loaded) == ["session-high", "session-low"]


def test_single_selection() -> None:
    from orchestration.selector import core

    selected = core.select(_policy(), _registry(), _sessions())

    assert isinstance(selected, str)
    assert selected == "session-high"


def test_artifact_output(tmp_path: Path) -> None:
    from orchestration.selector import core, writer

    timestamp = "2026-04-29T15:30:45.123Z"
    selector_output = core.build_selector_output(
        _policy(),
        _registry(),
        _sessions(),
        timestamp,
    )
    output_path = writer.write(selector_output, tmp_path / "artifacts/selector")
    loaded = json.loads(output_path.read_text(encoding="utf-8"))

    assert output_path.exists()
    assert re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-\d{3}Z\.json",
        output_path.name,
    )
    assert set(loaded) == {
        "candidate_sessions",
        "selected_session_id",
        "selection_reason",
        "execution_mode",
        "metadata",
    }
    assert "decision_steps" not in loaded
    assert "decision_trace" not in loaded
    assert loaded["candidate_sessions"] == ["session-high", "session-low"]
    assert loaded["selected_session_id"] == "session-high"
    assert loaded["metadata"]["timestamp"] == timestamp
    assert loaded["metadata"]["skipped_sessions"] == []


def test_no_queue_state_touch(tmp_path: Path) -> None:
    from orchestration.selector import core, writer

    queue_dir = tmp_path / "orchestration/queue"
    queue_dir.mkdir(parents=True)
    queue_state_path = queue_dir / "queue_state.json"
    assert not queue_state_path.exists()

    selector_output = core.build_selector_output(
        _policy(),
        _registry(),
        _sessions(),
        "2026-04-29T15:30:45.123Z",
    )
    writer.write(selector_output, tmp_path / "artifacts/selector")

    assert not queue_state_path.exists()


def test_deterministic() -> None:
    from orchestration.selector import core

    first = core.build_selector_output(
        _policy(),
        _registry(),
        _sessions(),
        "2026-04-29T15:30:45.123Z",
    )
    second = core.build_selector_output(
        _policy(),
        _registry(),
        _sessions(),
        "2026-04-29T15:30:45.123Z",
    )

    assert first["candidate_sessions"] == second["candidate_sessions"]
    assert first["selected_session_id"] == second["selected_session_id"]


def test_skipped_sessions_recorded(tmp_path: Path) -> None:
    from orchestration.selector import core, loader

    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    for session in _sessions():
        path = sessions_dir / f"{session['session_id']}.json"
        path.write_text(json.dumps(session), encoding="utf-8")
    broken_path = sessions_dir / "session-broken.json"
    broken_path.write_text('{"session_id": "session-broken",', encoding="utf-8")

    sessions, skipped_sessions = loader.load_session_definitions_with_skipped(
        sessions_dir / "*.json"
    )
    selector_output = core.build_selector_output(
        _policy(),
        _registry(),
        sessions,
        "2026-04-29T15:30:45.123Z",
        skipped_sessions=skipped_sessions,
    )

    assert selector_output["candidate_sessions"] == ["session-high", "session-low"]
    assert selector_output["selected_session_id"] == "session-high"
    assert selector_output["metadata"]["skipped_sessions"] == [
        {
            "path": str(broken_path),
            "reason": "json_parse_error",
        }
    ]
    assert "session-broken" not in selector_output["candidate_sessions"]


def test_skipped_sessions_empty_when_all_valid(tmp_path: Path) -> None:
    from orchestration.selector import core, loader

    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    for session in _sessions():
        path = sessions_dir / f"{session['session_id']}.json"
        path.write_text(json.dumps(session), encoding="utf-8")

    sessions, skipped_sessions = loader.load_session_definitions_with_skipped(
        sessions_dir / "*.json"
    )
    selector_output = core.build_selector_output(
        _policy(),
        _registry(),
        sessions,
        "2026-04-29T15:30:45.123Z",
        skipped_sessions=skipped_sessions,
    )

    assert "skipped_sessions" in selector_output["metadata"]
    assert selector_output["metadata"]["skipped_sessions"] == []


# --- execution_mode テスト群 (session-162) ---


def test_selector_output_contains_execution_mode() -> None:
    """build_selector_output() の返り値に execution_mode キーが存在する。"""
    from orchestration.selector import core

    result = core.build_selector_output(
        _policy(),
        _registry(),
        _sessions(),
        "2026-05-01T00:00:00.000Z",
    )
    assert "execution_mode" in result


def test_execution_mode_from_session_json() -> None:
    """session.json に execution_mode が明示されている場合、その値が採用される。"""
    from orchestration.selector import core

    sessions = [
        {
            "session_id": "session-a",
            "project_id": "P_LOW",
            "priority_rank_value": 10,
            "execution_mode": "full_stack",
        },
    ]
    result = core.build_selector_output(_policy(), _registry(), sessions, "ts")
    assert result["execution_mode"] == "full_stack"


def test_execution_mode_from_project_default() -> None:
    """session.json に execution_mode がない場合、project_registry の default_execution_mode が使われる。"""
    from orchestration.selector import core

    registry = {
        "projects": [
            {
                "project_id": "P_DEFAULT",
                "deploy_risk": "low",
                "default_execution_mode": "fast_path",
            },
        ],
    }
    sessions = [
        {
            "session_id": "session-b",
            "project_id": "P_DEFAULT",
            "priority_rank_value": 5,
        },
    ]
    result = core.build_selector_output(_policy(), registry, sessions, "ts")
    assert result["execution_mode"] == "fast_path"


def test_execution_mode_none_when_not_defined() -> None:
    """session.json にも project_registry にも execution_mode がない場合、None になる。"""
    from orchestration.selector import core

    sessions = [
        {
            "session_id": "session-c",
            "project_id": "P_LOW",
            "priority_rank_value": 5,
        },
    ]
    result = core.build_selector_output(_policy(), _registry(), sessions, "ts")
    assert result["execution_mode"] is None


def test_existing_output_keys_not_broken() -> None:
    """既存キー candidate_sessions / selected_session_id / selection_reason / metadata が維持される。"""
    from orchestration.selector import core

    result = core.build_selector_output(
        _policy(),
        _registry(),
        _sessions(),
        "2026-05-01T00:00:00.000Z",
    )
    assert "candidate_sessions" in result
    assert "selected_session_id" in result
    assert "selection_reason" in result
    assert "metadata" in result
    assert isinstance(result["candidate_sessions"], list)
    assert isinstance(result["selected_session_id"], str)
    assert isinstance(result["selection_reason"], str)
    assert isinstance(result["metadata"], dict)
