from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_timestamp() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def safe_timestamp(timestamp: str) -> str:
    return timestamp.replace(":", "-").replace(".", "-")


def write(
    selector_output: dict[str, Any],
    artifact_dir: str | Path = "artifacts/selector",
    timestamp: str | None = None,
) -> Path:
    output_timestamp = timestamp or str(
        selector_output.get("metadata", {}).get("timestamp") or utc_timestamp()
    )
    output_dir = Path(artifact_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{safe_timestamp(output_timestamp)}.json"
    output_path.write_text(
        json.dumps(selector_output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return output_path
