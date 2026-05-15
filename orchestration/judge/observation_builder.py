# -*- coding: utf-8 -*-
"""
judge_observation artifact ビルダー。

docs/contracts/judge_observation_contract.md に準拠した
observation artifact を filesystem に出力する。
LLM 呼び出し・GO/HOLD/FAIL 確定・worker self-approval は一切行わない。
final_decision_boundary は "commander_only" 固定。
"""

import datetime
import json
import os
from typing import Any, Dict, List, Optional

# worker_report の必須キー（docs/specs/worker_report_contract.md Section 3 準拠）
_WORKER_REPORT_REQUIRED_KEYS: List[str] = [
    "session_id",
    "acceptance_ref",
    "status_proposal",
    "changed_files",
    "verification_summary",
    "evidence_refs",
    "blocker_summary",
]

# PCC 8 フィールド（pcc_display_contract.md Section 6 の宣言順で固定）
_PCC_DISPLAY_FIELD_ORDER: List[str] = [
    "current_session",
    "next_action",
    "blocker",
    "waiting_human",
    "queue_status",
    "recent_failures",
    "dependency_state",
    "judge_state",
]


def _build_pcc_display_fields(worker_report: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """worker_report から PCC 8 フィールドを導出する（read-only・推測補完なし）。"""
    session_id: str = worker_report["session_id"]

    blocker_raw = worker_report.get("blocker_summary")
    blocker: Optional[str] = blocker_raw if isinstance(blocker_raw, str) else None

    # judge は未実行のため judge_state は not_applicable
    return {
        "current_session": session_id,
        "next_action": None,
        "blocker": blocker,
        "waiting_human": None,
        "queue_status": "not_applicable",
        "recent_failures": None,
        "dependency_state": None,
        "judge_state": "not_applicable",
    }


def build_judge_observation(
    worker_report: Dict[str, Any],
    output_path: str,
) -> Dict[str, Any]:
    """
    worker_report artifact を入力として judge_observation artifact を生成し保存する。

    - LLM 呼び出しを行わない
    - GO / HOLD / FAIL を確定しない
    - worker self-approval を行わない
    - final_decision_boundary は "commander_only" 固定

    Args:
        worker_report: worker が提出した report の dict（7 キー必須）
        output_path: observation artifact を書き出す JSON ファイルパス

    Returns:
        保存した artifact の dict（5 フィールド）

    Raises:
        ValueError: worker_report が dict でない、または必須キー欠落
    """
    if not isinstance(worker_report, dict):
        raise ValueError(
            f"worker_report は dict でなければならない。受け取った型: {type(worker_report).__name__}"
        )

    missing = set(_WORKER_REPORT_REQUIRED_KEYS) - worker_report.keys()
    if missing:
        raise ValueError(
            f"worker_report に必須キーが不足している: {sorted(missing)}"
        )

    session_id: str = str(worker_report["session_id"])
    observed_at: str = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    # judge_recommendation_ref: judge 未実行のため None（forward reference）
    judge_recommendation_ref: Optional[str] = None

    artifact: Dict[str, Any] = {
        "worker_report_ref": f"artifacts/worker_reports/{session_id}.json",
        "judge_recommendation_ref": judge_recommendation_ref,
        "observation_metadata": {
            "session_id": session_id,
            "acceptance_ref": worker_report["acceptance_ref"],
            "observed_at": observed_at,
        },
        "pcc_display_fields": _build_pcc_display_fields(worker_report),
        "final_decision_boundary": "commander_only",
    }

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(artifact, fh, ensure_ascii=False, indent=2)

    return artifact
