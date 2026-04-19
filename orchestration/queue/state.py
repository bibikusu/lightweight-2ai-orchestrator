from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class QueueState(Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    BLOCKED_HUMAN = "blocked_human"
    RETRY_WAITING = "retry_waiting"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class QueueItem:
    id: str
    session_id: str
    project_id: str
    state: QueueState
    deploy_risk: str
    created_at: str
    updated_at: str
    retry_count: int = 0
    max_retry: int = 1
    failure_type: str | None = None
