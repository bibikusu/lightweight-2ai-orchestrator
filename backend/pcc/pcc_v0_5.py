from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_MODULE_DIR = Path(__file__).parent
_REPO_ROOT = _MODULE_DIR.parent.parent
_DEFAULT_PROJECTS_DIR = _REPO_ROOT / "docs" / "projects"
_SESSIONS_DIR = _REPO_ROOT / "docs" / "sessions"

# pcc_display_contract.md Section 6 の宣言順（API/UI の並びの正）
PCC_EIGHT_SLOT_KEYS: Tuple[str, ...] = (
    "current_session",
    "next_action",
    "blocker",
    "waiting_human",
    "queue_status",
    "recent_failures",
    "dependency_state",
    "judge_state",
)

_OPERATIONAL_STATUS_VALUES = frozenset(
    {"READY", "BLOCKED", "WAITING_HUMAN", "RUNNING", "DONE", "UNKNOWN"}
)

# active は blockers の有無で分岐するため別処理
_STATUS_MAP: Dict[str, str] = {
    "idle": "READY",
    "paused": "WAITING_HUMAN",
    "done": "DONE",
}

_HUMAN_WAITING_FOR = frozenset({"human_cherry_pick", "human_external_input"})


def _resolved_session_id(state: Dict) -> Optional[str]:
    """state.json から docs/sessions/<id>.json を引く候補 session_id を決定的に選ぶ。"""
    for key in ("current_session_id", "last_session", "latest_session"):
        raw = state.get(key)
        if isinstance(raw, str):
            sid = raw.strip()
            if sid.startswith("session-"):
                return sid
    return None


def _read_json_file(path: Path) -> Optional[Dict]:
    """read-only: 存在しない・壊れた JSON は None。"""
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


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


def derive_pcc_eight_slots(state: Dict, card: Dict) -> Dict[str, str]:
    """
    pcc_display_contract.md Section 6 の8スロットを state / card / session JSON から read-only で導出する。
    戻り値のキー順は PCC_EIGHT_SLOT_KEYS と一致させる（dict 挿入順）。
    """
    sid = _resolved_session_id(state)
    session_doc: Optional[Dict] = None
    if sid:
        session_doc = _read_json_file(_SESSIONS_DIR / f"{sid}.json")

    # 1 current_session
    if sid and session_doc is not None:
        current_session = sid
    else:
        current_session = "not_applicable"

    # 2 next_action（プロジェクト state 正本）
    raw_next = state.get("next_action")
    if isinstance(raw_next, str) and raw_next.strip():
        next_action = raw_next.strip()
    else:
        next_action = "not_applicable"

    # 3 blocker（blockers 宣言順）
    blockers_raw = state.get("blockers")
    if isinstance(blockers_raw, list) and blockers_raw:
        norm: List[str] = []
        for item in blockers_raw:
            if isinstance(item, str) and item.strip():
                norm.append(item.strip())
        blocker = " | ".join(norm) if norm else "not_applicable"
    else:
        blocker = "not_applicable"

    # 4 waiting_human（契約に沿った決定論）
    wf = state.get("waiting_for")
    st = state.get("status")
    human = False
    if isinstance(wf, str) and wf in _HUMAN_WAITING_FOR:
        human = True
    elif st == "waiting" and isinstance(wf, str) and wf in _HUMAN_WAITING_FOR:
        human = True
    elif st == "paused":
        human = True
    waiting_human = "true" if human else "false"

    # 5 queue_status（queue_state.json snapshot のみ。live queue を正にしない）
    qs = card.get("queue_summary")
    if qs in (None, "", "not_configured"):
        queue_status = "not_applicable"
    else:
        queue_status = str(qs)

    # 6 recent_failures（last_error）
    le = state.get("last_error")
    if isinstance(le, str) and le.strip():
        recent_failures = le.strip()
    else:
        recent_failures = "not_applicable"

    # 7 dependency_state（宣言順: current_phase → current_session_id → status → waiting_for → blockers）
    dep_parts: List[str] = []
    for key in ("current_phase", "current_session_id", "status", "waiting_for", "blockers"):
        if key not in state:
            continue
        val = state[key]
        dep_parts.append(f"{key}={val!r}")
    dependency_state = " | ".join(dep_parts) if dep_parts else "not_applicable"

    # 8 judge_state（session JSON の failure_type）
    if session_doc is not None:
        ft = session_doc.get("failure_type")
        if isinstance(ft, str) and ft.strip():
            judge_state = ft.strip()
        else:
            judge_state = "not_applicable"
    else:
        judge_state = "not_applicable"

    return {
        "current_session": current_session,
        "next_action": next_action,
        "blocker": blocker,
        "waiting_human": waiting_human,
        "queue_status": queue_status,
        "recent_failures": recent_failures,
        "dependency_state": dependency_state,
        "judge_state": judge_state,
    }


def enrich_cards(
    cards: List[Dict],
    projects_dir: Optional[Path] = None,
) -> None:
    """card リストに v0.5 フィールドおよび Section 6 の8スロットをインプレースで付与する。読み取り専用。"""
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

        slots = derive_pcc_eight_slots(state, card)
        for k in PCC_EIGHT_SLOT_KEYS:
            card[k] = slots[k]
