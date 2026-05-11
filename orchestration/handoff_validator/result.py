"""ValidationResult dataclass for handoff validator."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ValidationResult:
    schema_version: str = "handoff_validator.v1"
    passed: bool = False
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
