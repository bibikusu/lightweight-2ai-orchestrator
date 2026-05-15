"""session-197: PCC 8スロット read-only 表示の受入テスト。"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

import pytest

from backend.pcc.pcc_v0 import aggregate_projects
from backend.pcc.pcc_v0_5 import PCC_EIGHT_SLOT_KEYS, derive_pcc_eight_slots, enrich_cards

_REPO_ROOT = Path(__file__).parent.parent
_SESSION_JSON = _REPO_ROOT / "docs" / "sessions" / "session-197.json"
_ACCEPT_YAML = _REPO_ROOT / "docs" / "acceptance" / "session-197.yaml"
_PCC_V0_5 = _REPO_ROOT / "backend" / "pcc" / "pcc_v0_5.py"


def _make_cards(
    states: Dict[str, Dict],
    tmp_path: Path,
    *,
    queue_summary: str = "not_configured",
    session_files: Dict[str, Dict] | None = None,
) -> List[Dict]:
    """registry + state.json を tmp に置き aggregate + enrich する。"""
    registry_dir = tmp_path / "docs" / "config"
    registry_dir.mkdir(parents=True, exist_ok=True)
    projects_dir = tmp_path / "docs" / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)

    if session_files:
        sess_dir = tmp_path / "docs" / "sessions"
        sess_dir.mkdir(parents=True, exist_ok=True)
        for fname, payload in session_files.items():
            (sess_dir / fname).write_text(
                json.dumps(payload, ensure_ascii=False), encoding="utf-8"
            )

    projects_list = []
    for pid, state in states.items():
        projects_list.append({"project_id": pid, "repo_path": "/nonexistent"})
        proj_dir = projects_dir / pid
        proj_dir.mkdir(parents=True, exist_ok=True)
        (proj_dir / "state.json").write_text(
            json.dumps(state, ensure_ascii=False), encoding="utf-8"
        )

    registry_path = registry_dir / "project_registry.json"
    registry_path.write_text(
        json.dumps({"projects": projects_list}, ensure_ascii=False), encoding="utf-8"
    )

    qpath = tmp_path / "docs" / "config" / "queue_state.json"
    qpath.parent.mkdir(parents=True, exist_ok=True)
    qpath.write_text(
        json.dumps({"summary": queue_summary}, ensure_ascii=False),
        encoding="utf-8",
    )

    cards = aggregate_projects(
        registry_path=registry_path,
        projects_dir=projects_dir,
        queue_state_path=qpath,
    )
    import backend.pcc.pcc_v0_5 as m

    prev_sessions = m._SESSIONS_DIR
    try:
        if session_files is not None:
            m._SESSIONS_DIR = tmp_path / "docs" / "sessions"
        enrich_cards(cards, projects_dir=projects_dir)
    finally:
        m._SESSIONS_DIR = prev_sessions

    return cards


def test_pcc_display_session_197_eight_slot_keys_ordered(tmp_path: Path) -> None:
    """AC-197-03: 各カードに Section 6 順の8キーが存在する。"""
    states = {
        "P1": {
            "status": "active",
            "blockers": [],
            "next_action": "次の作業",
            "last_session": "session-x-nonexistent",
        }
    }
    cards = _make_cards(states, tmp_path)
    card = cards[0]
    ordered = [k for k in PCC_EIGHT_SLOT_KEYS if k in card]
    assert ordered == list(PCC_EIGHT_SLOT_KEYS)


def test_pcc_display_session_197_projection_filesystem_only() -> None:
    """AC-197-04: 投影モジュールに write 系が含まれない（read-only）。"""
    src = _PCC_V0_5.read_text(encoding="utf-8")
    assert "write_text" not in src
    assert "write_bytes" not in src
    assert not re.search(r"\bopen\s*\([^)]*['\"]w['\"]", src)
    assert not re.search(r"\bopen\s*\([^)]*['\"]a['\"]", src)


def test_pcc_display_session_197_queue_status_snapshot_only(tmp_path: Path) -> None:
    """AC-197-05: queue_status は queue_state.json の snapshot のみ。"""
    states = {"P1": {"status": "idle", "blockers": []}}
    cards = _make_cards(states, tmp_path, queue_summary="night_batch_idle")
    assert cards[0]["queue_status"] == "night_batch_idle"

    cards2 = _make_cards(states, tmp_path, queue_summary="not_configured")
    assert cards2[0]["queue_status"] == "not_applicable"


def test_pcc_display_session_197_recent_failures_from_last_error(tmp_path: Path) -> None:
    """AC-197-06: recent_failures は last_error または not_applicable。"""
    states = {"P1": {"status": "idle", "blockers": [], "last_error": "  boom  "}}
    cards = _make_cards(states, tmp_path)
    assert cards[0]["recent_failures"] == "boom"

    states2 = {"P1": {"status": "idle", "blockers": []}}
    cards2 = _make_cards(states2, tmp_path)
    assert cards2[0]["recent_failures"] == "not_applicable"


def test_pcc_display_session_197_waiting_human_derivation(tmp_path: Path) -> None:
    """AC-197-07: waiting_human の決定論。"""
    s1 = {"P1": {"status": "paused", "blockers": []}}
    assert _make_cards(s1, tmp_path)[0]["waiting_human"] == "true"

    s2 = {"P1": {"status": "waiting", "blockers": [], "waiting_for": "human_cherry_pick"}}
    assert _make_cards(s2, tmp_path)[0]["waiting_human"] == "true"

    s3 = {"P1": {"status": "active", "blockers": [], "waiting_for": "cursor_implementation"}}
    assert _make_cards(s3, tmp_path)[0]["waiting_human"] == "false"


def test_pcc_display_session_197_dependency_state_bundle(tmp_path: Path) -> None:
    """AC-197-08: dependency_state は固定キー順で連結（ソートなし）。"""
    state = {
        "status": "running",
        "current_phase": "ph1",
        "current_session_id": "session-zz",
        "waiting_for": None,
        "blockers": ["a"],
    }
    d = derive_pcc_eight_slots(state, {"queue_summary": "not_configured"})
    ds = d["dependency_state"]
    assert ds.index("current_phase") < ds.index("current_session_id")
    assert ds.index("current_session_id") < ds.index("status")
    assert ds.index("status") < ds.index("waiting_for")
    assert ds.index("waiting_for") < ds.index("blockers")


def test_pcc_display_session_197_session_and_judge(tmp_path: Path) -> None:
    """session JSON がある場合 current_session / judge_state が読める。"""
    sid = "session-197-pre"
    payload = {"session_id": sid, "failure_type": "spec_missing"}
    states = {
        "P1": {
            "status": "idle",
            "blockers": [],
            "last_session": sid,
        }
    }
    cards = _make_cards(
        states,
        tmp_path,
        session_files={f"{sid}.json": payload},
    )
    assert cards[0]["current_session"] == sid
    assert cards[0]["judge_state"] == "spec_missing"


def test_session_197_json_has_all_14_keys() -> None:
    """AC-197-01"""
    d = json.loads(_SESSION_JSON.read_text(encoding="utf-8"))
    need = {
        "session_id",
        "phase_id",
        "title",
        "goal",
        "scope",
        "out_of_scope",
        "constraints",
        "acceptance_ref",
        "allowed_changes_detail",
        "forbidden_changes",
        "completion_criteria",
        "acceptance_criteria",
        "review_points",
        "failure_type",
    }
    assert need <= d.keys()


def test_session_197_yaml_session_id_matches() -> None:
    """AC-197-02"""
    import yaml

    d = yaml.safe_load(_ACCEPT_YAML.read_text(encoding="utf-8"))
    assert d.get("session_id") == "session-197"


def test_session_197_completion_criteria_types_canonical() -> None:
    """AC-197-10"""
    d = json.loads(_SESSION_JSON.read_text(encoding="utf-8"))
    ok = {
        "artifact",
        "document_rule",
        "non_regression",
        "side_effect_free",
        "state_transition_consistent",
    }
    types = {c.get("type") for c in d.get("completion_criteria", [])}
    assert types <= ok


def test_session_197_acceptance_criteria_shape() -> None:
    """AC-197-11"""
    d = json.loads(_SESSION_JSON.read_text(encoding="utf-8"))
    want = {"id", "description", "test_name"}
    for ac in d["acceptance_criteria"]:
        assert set(ac.keys()) == want


@pytest.mark.skip(reason="手動 AC-197-14: ブラウザで目視")
def test_pcc_display_session_197_browser_eight_slots() -> None:
    assert False


def test_session_197_diff_respects_allowed_changes() -> None:
    """AC-197-09: 可能な範囲で git diff のパスが許容集合に収まる（git なしは skip）。"""
    if not (_REPO_ROOT / ".git").is_dir():
        pytest.skip("git リポジトリ外")
    r = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if r.returncode != 0:
        pytest.skip("git diff 失敗")
    allowed = {
        "docs/sessions/session-197.json",
        "docs/acceptance/session-197.yaml",
        "backend/pcc/pcc_v0_5.py",
        "backend/pcc/pcc_v0.py",
        "backend/pcc/static/index.html",
        "backend/pcc/static/app.js",
        "backend/pcc/static/style.css",
        "tests/test_pcc_display_session_197.py",
    }
    paths = [p.strip() for p in r.stdout.splitlines() if p.strip()]
    if not paths:
        return
    bad = [p for p in paths if p not in allowed]
    assert not bad, bad


def test_pcc_v0_5_regression_passes() -> None:
    """AC-197-12"""
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests/test_pcc_v0_5.py"],
        cwd=_REPO_ROOT,
        timeout=120,
    )
    assert r.returncode == 0


def test_pcc_display_contract_unchanged() -> None:
    """AC-197-13"""
    if not (_REPO_ROOT / ".git").is_dir():
        pytest.skip("git なし")
    r = subprocess.run(
        ["git", "diff", "--exit-code", "--", "docs/specs/pcc_display_contract.md"],
        cwd=_REPO_ROOT,
    )
    assert r.returncode == 0
