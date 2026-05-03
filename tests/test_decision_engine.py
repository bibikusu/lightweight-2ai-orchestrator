"""
AC-169-01〜04 対応テスト: Decision Engine (session-169 仕様)
"""

import json
import sys
from pathlib import Path

import pytest  # noqa: E402

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from orchestration.decision.engine import SCORING_RULES, select_session  # noqa: E402


# ---------------------------------------------------------------------------
# AC-169-01: 入力 schema (goal: str, candidate_sessions: list[object])
# ---------------------------------------------------------------------------


def test_session_169_defines_input_schema():
    """session-169.json の constraints.input_schema に goal: str と candidate_sessions: list[object] が存在する。"""
    session_json = ROOT_DIR / "docs" / "sessions" / "session-169.json"
    data = json.loads(session_json.read_text(encoding="utf-8"))
    schema = data["constraints"]["input_schema"]
    assert schema["goal"] == "str"
    assert schema["candidate_sessions"] == "list[object]"


# ---------------------------------------------------------------------------
# AC-169-02: 出力 schema (selected_session_id: str, score_detail: list[object])
# ---------------------------------------------------------------------------


def test_session_169_defines_output_schema():
    """session-169.json の constraints.output_schema に selected_session_id: str と score_detail: list[object] が存在する。"""
    session_json = ROOT_DIR / "docs" / "sessions" / "session-169.json"
    data = json.loads(session_json.read_text(encoding="utf-8"))
    schema = data["constraints"]["output_schema"]
    assert schema["selected_session_id"] == "str"
    assert schema["score_detail"] == "list[object]"


# ---------------------------------------------------------------------------
# AC-169-03: スコアリングルール固定 (+3 goal_direct / +2 blocker_resolution / +1 next_step)
# ---------------------------------------------------------------------------


def test_session_169_defines_fixed_scoring_rules():
    """session-169.json の constraints.scoring_rules に +3/+2/+1 の 3 件が存在する。"""
    session_json = ROOT_DIR / "docs" / "sessions" / "session-169.json"
    data = json.loads(session_json.read_text(encoding="utf-8"))
    rules = data["constraints"]["scoring_rules"]
    assert "+3 goal_direct" in rules
    assert "+2 blocker_resolution" in rules
    assert "+1 next_step" in rules
    assert len(rules) == 3


# ---------------------------------------------------------------------------
# AC-169-04: selector / run_session.py 変更禁止
# ---------------------------------------------------------------------------


def test_session_169_forbids_selector_and_run_session_changes():
    """session-169.json の constraints.forbidden_changes に selector と run_session.py が含まれる。"""
    session_json = ROOT_DIR / "docs" / "sessions" / "session-169.json"
    data = json.loads(session_json.read_text(encoding="utf-8"))
    forbidden = data["constraints"]["forbidden_changes"]
    assert any("selector" in f for f in forbidden)
    assert any("run_session.py" in f for f in forbidden)


# ---------------------------------------------------------------------------
# エンジン動作テスト
# ---------------------------------------------------------------------------


def test_select_session_returns_highest_score():
    """goal_direct タグを持つ candidate が選ばれる。"""
    result = select_session(
        goal="improve test coverage",
        candidate_sessions=[
            {"session_id": "session-A", "tags": ["goal_direct"]},
            {"session_id": "session-B", "tags": ["next_step"]},
        ],
    )
    assert result["selected_session_id"] == "session-A"


def test_select_session_score_detail_structure():
    """score_detail が session_id / score / matched_rules を含む。"""
    result = select_session(
        goal="fix blocker",
        candidate_sessions=[
            {"session_id": "session-X", "tags": ["blocker_resolution"]},
        ],
    )
    detail = result["score_detail"][0]
    assert detail["session_id"] == "session-X"
    assert detail["score"] == 2
    assert "blocker_resolution" in detail["matched_rules"]


def test_select_session_multiple_tags_accumulate():
    """複数タグが一致すると加算される。"""
    result = select_session(
        goal="multi",
        candidate_sessions=[
            {"session_id": "session-M", "tags": ["goal_direct", "next_step"]},
        ],
    )
    detail = result["score_detail"][0]
    assert detail["score"] == 4  # 3 + 1


def test_select_session_tie_uses_input_order():
    """同点では入力順で先の candidate が選ばれる。"""
    result = select_session(
        goal="tie test",
        candidate_sessions=[
            {"session_id": "session-first", "tags": []},
            {"session_id": "session-second", "tags": []},
        ],
    )
    assert result["selected_session_id"] == "session-first"


def test_select_session_no_tags_score_zero():
    """タグなし candidate のスコアは 0。"""
    result = select_session(
        goal="any goal",
        candidate_sessions=[
            {"session_id": "session-Z", "tags": []},
        ],
    )
    assert result["score_detail"][0]["score"] == 0
    assert result["score_detail"][0]["matched_rules"] == []


def test_select_session_empty_candidates_raises():
    """candidate_sessions が空なら ValueError。"""
    with pytest.raises(ValueError, match="candidate_sessions"):
        select_session(goal="some goal", candidate_sessions=[])


def test_select_session_empty_goal_raises():
    """goal が空なら ValueError。"""
    with pytest.raises(ValueError, match="goal"):
        select_session(
            goal="",
            candidate_sessions=[{"session_id": "session-A", "tags": []}],
        )


def test_select_session_whitespace_goal_raises():
    """goal が空白のみでも ValueError。"""
    with pytest.raises(ValueError, match="goal"):
        select_session(
            goal="   ",
            candidate_sessions=[{"session_id": "session-A", "tags": []}],
        )


def test_scoring_rules_are_fixed():
    """SCORING_RULES が仕様通りの 3 件固定。"""
    rules_dict = dict(SCORING_RULES)
    assert rules_dict["goal_direct"] == 3
    assert rules_dict["blocker_resolution"] == 2
    assert rules_dict["next_step"] == 1
    assert len(SCORING_RULES) == 3


def test_select_session_output_keys():
    """出力に selected_session_id と score_detail が含まれる。"""
    result = select_session(
        goal="check output",
        candidate_sessions=[{"session_id": "session-K", "tags": ["goal_direct"]}],
    )
    assert "selected_session_id" in result
    assert "score_detail" in result
