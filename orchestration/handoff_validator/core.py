"""Core validate_handoff function."""

from __future__ import annotations

import json
import pathlib

import yaml

from orchestration.handoff_validator.result import ValidationResult
from orchestration.handoff_validator.rules import (
    check_ac_cc_referential_integrity,
    check_required_keys,
    check_scope_invasion_fields,
)


def validate_handoff(
    context_pack_path: pathlib.Path,
    session_json_path: pathlib.Path,
    acceptance_yaml_path: pathlib.Path,
) -> ValidationResult:
    with open(context_pack_path, encoding="utf-8") as f:
        context_pack = json.load(f)
    with open(session_json_path, encoding="utf-8") as f:
        session_json = json.load(f)
    with open(acceptance_yaml_path, encoding="utf-8") as f:
        acceptance_yaml = yaml.safe_load(f)

    errors: list = []
    errors.extend(check_required_keys(context_pack))
    errors.extend(check_ac_cc_referential_integrity(session_json, acceptance_yaml))
    errors.extend(check_scope_invasion_fields(context_pack))

    warnings: list = list(context_pack.get("warnings", []))

    return ValidationResult(
        schema_version="handoff_validator.v1",
        passed=(len(errors) == 0),
        errors=errors,
        warnings=warnings,
    )
