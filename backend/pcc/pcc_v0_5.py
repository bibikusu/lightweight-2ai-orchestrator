from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

_MODULE_DIR = Path(__file__).parent
_REPO_ROOT = _MODULE_DIR.parent.parent
_DEFAULT_PROJECTS_DIR = _REPO_ROOT / "docs" / "projects"

_OPERATIONAL_STATUS_VALUES = frozenset(
    {"READY", "BLOCKED", "WAITING_HUMAN", "RUNNING", "DONE", "UNKNOWN"}
)

# active は blockers の有無で分岐するため別処理
_STATUS_MAP: Dict[str, str] = {
    "idle":   "READY",
    "paused": "WAITING_HUMAN",
    "done":   "DONE",
}


def derive_operational_fields(state: Dict) -> Dict:
    """state.json から operational_status / next_action / blocker_summary を導出する。読み取り専用。"""
    raw_status = state.get("status")
    blockers_raw = state.get("blockers")
    blockers: List[str] = blockers_raw if isinstance(blockers_raw, list) else []

    if raw_status == "active":
        operational_status = "BLOCKED" if blockers else "RUNNING"
    elif isinstance(raw_status, str) and raw_status in _STATUS_MAP:
        operational_status = _STATUS_MAP[raw_status]
    else:
        operational_status = "UNKNOWN"

    raw_next = state.get("next_action")
    next_action: Optional[str] = (
        raw_next if isinstance(raw_next, str) and raw_next.strip() else None
    )

    if blockers:
        blocker_summary: Optional[str] = f"({len(blockers)}) {blockers[0]}"
    else:
        blocker_summary = None

    return {
        "operational_status": operational_status,
        "next_action": next_action,
        "blocker_summary": blocker_summary,
    }


def enrich_cards(
    cards: List[Dict],
    projects_dir: Optional[Path] = None,
) -> None:
    """card リストに operational_status / next_action / blocker_summary をインプレースで付与する。読み取り専用。"""
    proj_dir = projects_dir if projects_dir is not None else _DEFAULT_PROJECTS_DIR

    for card in cards:
        project_id = card.get("project_id", "")
        state: Dict = {}
        if project_id:
            state_path = proj_dir / str(project_id) / "state.json"
            if state_path.exists():
                try:
                    state = json.loads(state_path.read_text(encoding="utf-8"))
                except Exception:
                    state = {}

        op = derive_operational_fields(state)
        card["operational_status"] = op["operational_status"]
        card["next_action"] = op["next_action"]
        card["blocker_summary"] = op["blocker_summary"]
