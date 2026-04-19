from __future__ import annotations

import json
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

import yaml

from orchestration.queue.state import QueueItem, QueueState
from orchestration.queue.store import QueueStore

_RETRY_FAILURE_TYPES = frozenset(
    {"test_failure", "type_mismatch", "build_error", "import_error"}
)
_HUMAN_GATE_FAILURE_TYPES = frozenset({"scope_violation", "regression", "spec_missing"})


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_failure_type_from_text(stdout: str, stderr: str) -> str | None:
    text = f"{stdout or ''}\n{stderr or ''}".strip()
    if not text:
        return None
    for line in reversed(text.splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict) and obj.get("failure_type") is not None:
                return str(obj["failure_type"])
        except json.JSONDecodeError:
            continue
    try:
        obj = json.loads(text)
        if isinstance(obj, dict) and obj.get("failure_type") is not None:
            return str(obj["failure_type"])
    except json.JSONDecodeError:
        pass
    return None


def _failure_type_from_completed(proc: subprocess.CompletedProcess[str]) -> str | None:
    if proc.returncode == 0:
        return None
    return _parse_failure_type_from_text(proc.stdout or "", proc.stderr or "")


class QueueEngine:
    """Minimal queue runner: subprocess-only delegation to run_session.py."""

    def __init__(
        self,
        store: QueueStore,
        registry_path: Path | str,
        policy_path: Path | str,
        max_parallel: int = 1,
    ) -> None:
        self._store = store
        self._registry_path = Path(registry_path)
        self._policy_path = Path(policy_path)
        self._max_parallel = max(1, int(max_parallel))
        self._repo_root = Path(__file__).resolve().parents[2]

    def _load_deploy_risk(self, project_id: str) -> str:
        raw = json.loads(self._registry_path.read_text(encoding="utf-8"))
        projects = raw.get("projects")
        if not isinstance(projects, list):
            raise ValueError("registry invalid: missing projects")
        for p in projects:
            if isinstance(p, dict) and str(p.get("project_id")) == project_id:
                risk = p.get("deploy_risk")
                if risk is not None:
                    return str(risk)
                break
        raise KeyError(f"project_id not in registry: {project_id!r}")

    def enqueue(self, session_id: str, project_id: str) -> QueueItem:
        policy_root = yaml.safe_load(self._policy_path.read_text(encoding="utf-8"))
        if not isinstance(policy_root, dict):
            raise ValueError("queue_policy.yaml root must be a mapping")
        deploy_risk = self._load_deploy_risk(project_id)
        now = _iso_now()
        item = QueueItem(
            id=str(uuid.uuid4()),
            session_id=session_id,
            project_id=project_id,
            state=QueueState.PENDING,
            deploy_risk=deploy_risk,
            created_at=now,
            updated_at=now,
        )
        items = self._store.load()
        items.append(item)
        self._store.save(items)
        return item

    def dispatch_ready(self) -> list[QueueItem]:
        """PENDING を policy 判定し READY または BLOCKED_HUMAN へ、RETRY_WAITING を READY へ。"""
        items = self._store.load()
        moved: list[QueueItem] = []
        now = _iso_now()
        for item in items:
            if item.state == QueueState.PENDING:
                if item.deploy_risk == "critical":
                    item.state = QueueState.BLOCKED_HUMAN
                    item.updated_at = now
                    moved.append(item)
                else:
                    item.state = QueueState.READY
                    item.updated_at = now
                    moved.append(item)
            elif item.state == QueueState.RETRY_WAITING:
                item.state = QueueState.READY
                item.updated_at = now
                moved.append(item)
        if moved:
            self._store.save(items)
        return moved

    def run_next(self) -> QueueItem | None:
        items = self._store.load()
        running_n = sum(1 for i in items if i.state == QueueState.RUNNING)
        if running_n >= self._max_parallel:
            return None
        ready_sorted = sorted(
            (i for i in items if i.state == QueueState.READY),
            key=lambda x: (x.created_at, x.id),
        )
        if not ready_sorted:
            return None
        item = ready_sorted[0]
        now = _iso_now()
        item.state = QueueState.RUNNING
        item.updated_at = now
        self._store.upsert(item)

        proc = subprocess.run(
            [
                "python",
                "orchestration/run_session.py",
                "--session-id",
                item.session_id,
                "--project",
                item.project_id,
            ],
            cwd=self._repo_root,
            capture_output=True,
            text=True,
        )
        ft = _failure_type_from_completed(proc)
        return self.route_after_run(item, proc.returncode, ft)

    def route_after_run(
        self,
        item: QueueItem,
        exit_code: int,
        failure_type: str | None,
    ) -> QueueItem:
        now = _iso_now()
        item.failure_type = failure_type

        if item.deploy_risk == "critical":
            item.state = QueueState.BLOCKED_HUMAN
            item.updated_at = now
            self._store.upsert(item)
            return item

        if exit_code == 0:
            item.state = QueueState.COMPLETED
            item.updated_at = now
            self._store.upsert(item)
            return item

        if failure_type in _HUMAN_GATE_FAILURE_TYPES:
            item.state = QueueState.BLOCKED_HUMAN
            item.updated_at = now
            self._store.upsert(item)
            return item

        if failure_type in _RETRY_FAILURE_TYPES:
            if item.retry_count < item.max_retry:
                item.retry_count += 1
                item.state = QueueState.RETRY_WAITING
                item.updated_at = now
                self._store.upsert(item)
                return item
            item.state = QueueState.FAILED
            item.updated_at = now
            self._store.upsert(item)
            return item

        item.state = QueueState.FAILED
        item.updated_at = now
        self._store.upsert(item)
        return item
