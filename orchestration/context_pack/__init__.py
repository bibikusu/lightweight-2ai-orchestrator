"""Compact context pack generator for orchestrated handoff.

Public API:
    - build_compact_context_pack(session_id, repo_root) -> dict
    - write_compact_context_pack(pack, output_dir) -> pathlib.Path
"""

from orchestration.context_pack.core import build_compact_context_pack
from orchestration.context_pack.writer import write_compact_context_pack

__all__ = [
    "build_compact_context_pack",
    "write_compact_context_pack",
]
