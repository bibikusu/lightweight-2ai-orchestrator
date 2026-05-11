"""Handoff validator for compact context pack.

Public API:
    - validate_handoff(context_pack_path, session_json_path, acceptance_yaml_path) -> ValidationResult
    - ValidationResult (frozen dataclass)
"""

from orchestration.handoff_validator.core import validate_handoff
from orchestration.handoff_validator.result import ValidationResult

__all__ = [
    "validate_handoff",
    "ValidationResult",
]
