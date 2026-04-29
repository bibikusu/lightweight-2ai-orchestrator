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
        "metadata",
    }
    assert "decision_steps" not in loaded
    assert "decision_trace" not in loaded
    assert loaded["candidate_sessions"] == ["session-high", "session-low"]
    assert loaded["selected_session_id"] == "session-high"
    assert loaded["metadata"]["timestamp"] == timestamp


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
