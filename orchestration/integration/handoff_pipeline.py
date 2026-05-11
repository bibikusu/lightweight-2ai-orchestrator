"""Handoff pipeline: context_pack 生成と handoff 検証を統合する。"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass

from orchestration.context_pack import build_compact_context_pack, write_compact_context_pack
from orchestration.handoff_validator import ValidationResult, validate_handoff

_SCHEMA_VERSION = "handoff_pipeline.v1"


@dataclass(frozen=True)
class HandoffPipelineResult:
    schema_version: str
    context_pack_path: pathlib.Path
    validation_result: ValidationResult


def build_then_validate(session_id: str, repo_root: pathlib.Path) -> HandoffPipelineResult:
    # context_pack 生成（失敗時は例外を re-raise する）
    pack = build_compact_context_pack(session_id, repo_root)

    output_dir = repo_root / "artifacts" / session_id / "context"
    context_pack_path = write_compact_context_pack(pack, output_dir)

    session_json_path = repo_root / "docs" / "sessions" / f"{session_id}.json"
    acceptance_yaml_path = repo_root / "docs" / "acceptance" / f"{session_id}.yaml"

    validation_result = validate_handoff(context_pack_path, session_json_path, acceptance_yaml_path)

    return HandoffPipelineResult(
        schema_version=_SCHEMA_VERSION,
        context_pack_path=context_pack_path,
        validation_result=validation_result,
    )
