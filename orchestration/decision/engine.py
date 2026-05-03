"""Decision Engine: stateless 純粋判定関数 (session-169 仕様)。

入力:
    goal: str
    candidate_sessions: list[dict]

出力:
    selected_session_id: str
    score_detail: list[dict]

スコアリングルール:
    +3 goal_direct
    +2 blocker_resolution
    +1 next_step

candidate.tags に該当タグがあれば加点。highest_score を 1 件選択。
同点は入力順で先。candidate_sessions が空 / goal が空は ValueError。
"""

from __future__ import annotations

from typing import Any

SCORING_RULES: list[tuple[str, int]] = [
    ("goal_direct", 3),
    ("blocker_resolution", 2),
    ("next_step", 1),
]


def select_session(
    goal: str,
    candidate_sessions: list[dict[str, Any]],
) -> dict[str, Any]:
    """candidate_sessions から goal に最も近い 1 件を選択して返す。

    Returns:
        {
            "selected_session_id": str,
            "score_detail": list[{"session_id": str, "score": int, "matched_rules": list[str]}]
        }

    Raises:
        ValueError: goal が空 / candidate_sessions が空
    """
    if not goal or not goal.strip():
        raise ValueError("goal must not be empty")
    if not candidate_sessions:
        raise ValueError("candidate_sessions must not be empty")

    score_detail: list[dict[str, Any]] = []

    for candidate in candidate_sessions:
        tags: list[str] = candidate.get("tags") or []
        matched_rules: list[str] = []
        score = 0
        for rule_name, rule_score in SCORING_RULES:
            if rule_name in tags:
                matched_rules.append(rule_name)
                score += rule_score
        score_detail.append(
            {
                "session_id": candidate["session_id"],
                "score": score,
                "matched_rules": matched_rules,
            }
        )

    best = max(score_detail, key=lambda x: x["score"])
    return {
        "selected_session_id": best["session_id"],
        "score_detail": score_detail,
    }
