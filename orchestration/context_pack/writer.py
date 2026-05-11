"""Write compact context pack to output directory."""

import json
import pathlib


def write_compact_context_pack(pack: dict, output_dir: pathlib.Path) -> pathlib.Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "compact_context_pack.json"
    output_path.write_text(
        json.dumps(pack, ensure_ascii=False, indent=2, sort_keys=False),
        encoding="utf-8",
    )
    return output_path
