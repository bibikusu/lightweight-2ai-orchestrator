from __future__ import annotations

import json
from pathlib import Path

from orchestration.queue.state import QueueItem, QueueState


def _item_to_dict(item: QueueItem) -> dict:
    return {
        "id": item.id,
        "session_id": item.session_id,
        "project_id": item.project_id,
        "state": item.state.value,
        "deploy_risk": item.deploy_risk,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "retry_count": item.retry_count,
        "max_retry": item.max_retry,
        "failure_type": item.failure_type,
    }


def _dict_to_item(row: dict) -> QueueItem:
    return QueueItem(
        id=str(row["id"]),
        session_id=str(row["session_id"]),
        project_id=str(row["project_id"]),
        state=QueueState(str(row["state"])),
        deploy_risk=str(row["deploy_risk"]),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
        retry_count=int(row.get("retry_count", 0)),
        max_retry=int(row.get("max_retry", 1)),
        failure_type=row.get("failure_type"),
    )


class QueueStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path if path is not None else Path("orchestration/queue/queue_state.json")

    def load(self) -> list[QueueItem]:
        if not self.path.is_file():
            return []
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            return []
        return [_dict_to_item(x) for x in raw if isinstance(x, dict)]

    def save(self, items: list[QueueItem]) -> None:
        payload = [_item_to_dict(i) for i in items]
        data = json.dumps(payload, indent=2, ensure_ascii=False)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp_path.write_text(data, encoding="utf-8")
        tmp_path.replace(self.path)

    def upsert(self, item: QueueItem) -> None:
        items = self.load()
        for idx, cur in enumerate(items):
            if cur.id == item.id:
                items[idx] = item
                break
        else:
            items.append(item)
        self.save(items)

    def list_by_state(self, state: QueueState) -> list[QueueItem]:
        return [i for i in self.load() if i.state == state]
