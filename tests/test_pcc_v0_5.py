"""PCC v0.5 受入テスト AC-180-01〜10。"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Dict, List

from backend.pcc.pcc_v0_5 import derive_operational_fields, enrich_cards

_REPO_ROOT = Path(__file__).parent.parent
_BACKEND_PCC = _REPO_ROOT / "backend" / "pcc"
_PROJECTS_DIR = _REPO_ROOT / "docs" / "projects"

_VALID_OPERATIONAL_STATUS = frozenset(
    {"READY", "BLOCKED", "WAITING_HUMAN", "RUNNING", "DONE", "UNKNOWN"}
)

_FORBIDDEN_IMPORTS = ["requests", "httpx", "anthropic", "openai", "mcp", "queue"]


# ─────────────────────────────────────────────
# テスト用ヘルパー
# ─────────────────────────────────────────────

def _make_cards_via_enrich(
    states: Dict[str, Dict],
    tmp_path: Path,
) -> List[Dict]:
    """テスト用: 指定した state を持つ registry を構築して aggregate_projects() + enrich_cards() を呼ぶ。"""
    from backend.pcc.pcc_v0 import aggregate_projects

    registry_dir = tmp_path / "docs" / "config"
    registry_dir.mkdir(parents=True)
    projects_dir = tmp_path / "docs" / "projects"
    projects_dir.mkdir(parents=True)

    projects_list = []
    for pid, state in states.items():
        projects_list.append({"project_id": pid, "repo_path": "/nonexistent"})
        proj_dir = projects_dir / pid
        proj_dir.mkdir(parents=True)
        (proj_dir / "state.json").write_text(
            json.dumps(state, ensure_ascii=False), encoding="utf-8"
        )

    registry_path = registry_dir / "project_registry.json"
    registry_path.write_text(
        json.dumps({"projects": projects_list}, ensure_ascii=False), encoding="utf-8"
    )

    cards = aggregate_projects(
        registry_path=registry_path,
        projects_dir=projects_dir,
        queue_state_path=tmp_path / "nonexistent_queue.json",
    )
    enrich_cards(cards, projects_dir=projects_dir)
    return cards


# ─────────────────────────────────────────────
# AC-180-01: enrich_cards が3フィールドを付与する
# ─────────────────────────────────────────────


def test_pcc_v0_5_card_has_three_new_fields(tmp_path: Path) -> None:
    states = {"A01": {"status": "active", "blockers": [], "next_action": "do something"}}
    cards = _make_cards_via_enrich(states, tmp_path)
    assert len(cards) == 1
    card = cards[0]
    assert "operational_status" in card, "operational_status missing"
    assert "next_action" in card, "next_action missing"
    assert "blocker_summary" in card, "blocker_summary missing"


# ─────────────────────────────────────────────
# AC-180-02: operational_status は 6値 enum のみ
# ─────────────────────────────────────────────


def test_pcc_v0_5_operational_status_valid_enum() -> None:
    statuses = ["active", "paused", "idle", "done", "running", "completed", "failed", "", None]
    for s in statuses:
        state: Dict = {"status": s, "blockers": []} if s is not None else {"blockers": []}
        result = derive_operational_fields(state)
        op = result["operational_status"]
        assert op in _VALID_OPERATIONAL_STATUS, (
            f"Invalid operational_status '{op}' for status={s!r}"
        )


# ─────────────────────────────────────────────
# AC-180-03: next_action は str または null
# ─────────────────────────────────────────────


def test_pcc_v0_5_next_action_type() -> None:
    cases = [
        {"status": "active", "blockers": [], "next_action": "do something"},
        {"status": "active", "blockers": [], "next_action": None},
        {"status": "active", "blockers": []},
        {"status": "active", "blockers": [], "next_action": ""},
    ]
    for state in cases:
        result = derive_operational_fields(state)
        val = result["next_action"]
        assert val is None or isinstance(val, str), (
            f"next_action must be str or null, got {type(val)}"
        )


# ─────────────────────────────────────────────
# AC-180-04: blocker_summary は str または null
# ─────────────────────────────────────────────


def test_pcc_v0_5_blocker_summary_type() -> None:
    cases = [
        {"status": "active", "blockers": []},
        {"status": "active", "blockers": ["blocker one"]},
        {"status": "active", "blockers": ["b1", "b2"]},
        {"status": "active", "blockers": "not-a-list"},
    ]
    for state in cases:
        result = derive_operational_fields(state)
        val = result["blocker_summary"]
        assert val is None or isinstance(val, str), (
            f"blocker_summary must be str or null, got {type(val)}"
        )


# ─────────────────────────────────────────────
# AC-180-05: active + no blockers → RUNNING (not READY)
# ─────────────────────────────────────────────


def test_pcc_v0_5_active_no_blockers_is_running() -> None:
    state = {"status": "active", "blockers": []}
    result = derive_operational_fields(state)
    assert result["operational_status"] == "RUNNING", (
        f"Expected RUNNING, got {result['operational_status']}"
    )
    assert result["blocker_summary"] is None


# ─────────────────────────────────────────────
# AC-180-06: active + blockers 非空 → BLOCKED
# ─────────────────────────────────────────────


def test_pcc_v0_5_active_with_blockers_is_blocked() -> None:
    blocker_text = "BACKLOG-001: some issue"
    state = {"status": "active", "blockers": [blocker_text, "second"]}
    result = derive_operational_fields(state)
    assert result["operational_status"] == "BLOCKED"
    assert result["blocker_summary"] is not None
    assert result["blocker_summary"].startswith("(2) ")
    assert blocker_text in result["blocker_summary"]


# ─────────────────────────────────────────────
# AC-180-07: paused → WAITING_HUMAN
# ─────────────────────────────────────────────


def test_pcc_v0_5_paused_is_waiting_human() -> None:
    result = derive_operational_fields({"status": "paused", "blockers": []})
    assert result["operational_status"] == "WAITING_HUMAN"


# ─────────────────────────────────────────────
# AC-180-07b: idle → READY
# ─────────────────────────────────────────────


def test_pcc_v0_5_idle_is_ready() -> None:
    result = derive_operational_fields({"status": "idle", "blockers": []})
    assert result["operational_status"] == "READY", (
        f"Expected READY for status=idle, got {result['operational_status']}"
    )


# ─────────────────────────────────────────────
# AC-180-07c: 仕様外の status は全て UNKNOWN
# ─────────────────────────────────────────────


def test_pcc_v0_5_non_spec_status_is_unknown() -> None:
    for bad_status in ["running", "completed", "failed", "unknown_val", "", None]:
        state: Dict = (
            {"status": bad_status, "blockers": []}
            if bad_status is not None
            else {"blockers": []}
        )
        result = derive_operational_fields(state)
        assert result["operational_status"] == "UNKNOWN", (
            f"Expected UNKNOWN for status={bad_status!r}, got {result['operational_status']}"
        )


# ─────────────────────────────────────────────
# AC-180-08: forbidden import が新規導入されていない
# ─────────────────────────────────────────────


def test_pcc_v0_5_no_new_forbidden_imports() -> None:
    pattern = re.compile(
        r"^\s*(?:import|from)\s+(" + "|".join(_FORBIDDEN_IMPORTS) + r")\b",
        re.MULTILINE,
    )
    for py_file in _BACKEND_PCC.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        matches = pattern.findall(text)
        assert not matches, (
            f"Forbidden import found in {py_file.relative_to(_REPO_ROOT)}: {matches}"
        )


# ─────────────────────────────────────────────
# AC-180-09: write 系処理が新規導入されていない
# ─────────────────────────────────────────────


def test_pcc_v0_5_no_new_write_ops() -> None:
    write_pattern = re.compile(
        r"open\s*\([^)]*['\"]w['\"]|open\s*\([^)]*['\"]a['\"]"
        r"|Path.*\.write_text|Path.*\.write_bytes|shutil\.copy",
        re.MULTILINE,
    )
    for py_file in _BACKEND_PCC.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        matches = write_pattern.findall(text)
        assert not matches, (
            f"Write operation found in {py_file.relative_to(_REPO_ROOT)}: {matches}"
        )


# ─────────────────────────────────────────────
# AC-180-10: pcc_v0.py が origin/main から diff=0
# ─────────────────────────────────────────────


def test_pcc_v0_5_pcc_v0_py_unchanged_from_origin_main() -> None:
    result = subprocess.run(
        ["git", "diff", "origin/main", "--", "backend/pcc/pcc_v0.py"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, f"git diff failed: {result.stderr}"
    assert result.stdout.strip() == "", (
        "ABSOLUTE FORBIDDEN: backend/pcc/pcc_v0.py has diff from origin/main:\n"
        + result.stdout[:500]
    )
