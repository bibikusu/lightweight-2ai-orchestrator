"""Handoff pipeline integration package.

Public API:
    - build_then_validate(session_id, repo_root) -> HandoffPipelineResult
    - HandoffPipelineResult (frozen dataclass)
"""

from orchestration.integration.handoff_pipeline import HandoffPipelineResult, build_then_validate

__all__ = [
    "build_then_validate",
    "HandoffPipelineResult",
]
