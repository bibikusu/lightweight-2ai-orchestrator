from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class QueueConfig:
    registry_path: Path
    policy_path: Path


@dataclass
class SessionEntry:
    session_id: str
    project_id: str


@dataclass
class ScheduledPlan:
    id: str  # "daily" / "weekly" 等
    enabled: bool
    hour: int
    minute: int
    weekday: int | None  # None = 毎日 / 1-7 = 特定曜日
    sessions: list[SessionEntry]


class SchedulerPlanLoader:
    def __init__(self, path: Path = Path("docs/config/scheduler_plans.yaml")) -> None:
        self._path = path

    def _resolve_path(self, raw: str) -> Path:
        p = Path(raw)
        if p.is_absolute():
            return p
        return _REPO_ROOT / p

    def load(self) -> tuple[QueueConfig, list[ScheduledPlan]]:
        data = yaml.safe_load(self._path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("scheduler_plans.yaml root must be a mapping")

        qc = data.get("queue_config")
        if not isinstance(qc, dict):
            raise ValueError("scheduler_plans.yaml missing queue_config")
        reg = qc.get("registry_path")
        pol = qc.get("policy_path")
        if not isinstance(reg, str) or not isinstance(pol, str):
            raise ValueError("queue_config.registry_path and policy_path must be strings")
        queue_config = QueueConfig(
            registry_path=self._resolve_path(reg),
            policy_path=self._resolve_path(pol),
        )

        raw_plans = data.get("plans")
        if not isinstance(raw_plans, list):
            raise ValueError("scheduler_plans.yaml missing plans list")

        plans: list[ScheduledPlan] = []
        for entry in raw_plans:
            if not isinstance(entry, dict):
                continue
            pid = entry.get("id")
            if not isinstance(pid, str):
                raise ValueError("plan id must be a string")
            enabled = bool(entry.get("enabled", True))
            hour = int(entry["hour"])
            minute = int(entry["minute"])
            wd = entry.get("weekday")
            weekday: int | None
            if wd is None:
                weekday = None
            else:
                weekday = int(wd)
                if not 1 <= weekday <= 7:
                    raise ValueError(f"plan {pid}: weekday must be 1-7 or null")

            sess_raw = entry.get("sessions")
            if not isinstance(sess_raw, list):
                raise ValueError(f"plan {pid}: sessions must be a list")
            sessions: list[SessionEntry] = []
            for s in sess_raw:
                if not isinstance(s, dict):
                    continue
                sid = s.get("session_id")
                proj = s.get("project_id")
                if not isinstance(sid, str) or not isinstance(proj, str):
                    raise ValueError(f"plan {pid}: session_id and project_id must be strings")
                sessions.append(SessionEntry(session_id=sid, project_id=proj))

            plans.append(
                ScheduledPlan(
                    id=pid,
                    enabled=enabled,
                    hour=hour,
                    minute=minute,
                    weekday=weekday,
                    sessions=sessions,
                )
            )

        return queue_config, plans
