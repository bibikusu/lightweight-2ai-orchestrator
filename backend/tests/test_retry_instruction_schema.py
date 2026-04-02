"""AC-85-01〜04: structured retry instruction quality improvement テスト。"""
import json
import pytest

from orchestration.run_session import (
    build_retry_instruction,
    validate_retry_instruction_schema,
    SessionContext,
)


# ---------------------------------------------------------------------------
# テスト用ヘルパー
# ---------------------------------------------------------------------------
def _make_ctx(session_id: str = "session-85") -> SessionContext:
    """テスト用の最小限 SessionContext を生成する。"""
    return SessionContext(
        session_id=session_id,
        session_data={
            "session_id": session_id,
            "phase_id": "phase-1",
            "title": "test session",
            "goal": "test goal",
            "scope": [],
            "out_of_scope": [],
            "constraints": [],
            "acceptance_ref": "docs/acceptance/session-85.yaml",
        },
        acceptance_data={"raw_yaml": "", "parsed": {}},
        master_instruction="",
        global_rules="",
        roadmap_text="",
        runtime_config={},
    )


def _make_failure(
    failure_type: str = "test_failure",
    cause_summary: str = "テスト失敗の原因",
) -> dict:
    return {"failure_type": failure_type, "cause_summary": cause_summary}


def _build(ctx=None, spec=None, failure=None):
    """build_retry_instruction のショートカット。"""
    return build_retry_instruction(
        ctx=ctx or _make_ctx(),
        prepared_spec=spec or {},
        failure=failure or _make_failure(),
    )


# ---------------------------------------------------------------------------
# AC-85-01: cause_summary が含まれる
# ---------------------------------------------------------------------------
class TestRetryInstructionIncludesCauseSummary:
    def test_cause_summary_is_present(self):
        """AC-85-01: cause_summary キーが存在する。"""
        result = _build()
        assert "cause_summary" in result

    def test_cause_summary_is_nonempty_string(self):
        """AC-85-01: cause_summary は空でない文字列。"""
        result = _build()
        assert isinstance(result["cause_summary"], str)
        assert result["cause_summary"].strip() != ""

    def test_cause_summary_reflects_failure(self):
        """AC-85-01: cause_summary は failure の cause_summary を引き継ぐ。"""
        failure = _make_failure(cause_summary="specific error message")
        result = _build(failure=failure)
        assert result["cause_summary"] == "specific error message"


# ---------------------------------------------------------------------------
# AC-85-02: fix_instructions が含まれる
# ---------------------------------------------------------------------------
class TestRetryInstructionIncludesFixInstructions:
    def test_fix_instructions_is_present(self):
        """AC-85-02: fix_instructions キーが存在する。"""
        result = _build()
        assert "fix_instructions" in result

    def test_fix_instructions_is_nonempty_list(self):
        """AC-85-02: fix_instructions は空でないリスト。"""
        result = _build()
        fi = result["fix_instructions"]
        assert isinstance(fi, list)
        assert len(fi) > 0

    def test_fix_instructions_contains_strings(self):
        """AC-85-02: fix_instructions の要素はすべて文字列。"""
        result = _build()
        assert all(isinstance(x, str) for x in result["fix_instructions"])


# ---------------------------------------------------------------------------
# AC-85-03: do_not_change が scope guard として含まれる
# ---------------------------------------------------------------------------
class TestRetryInstructionIncludesDoNotChangeScope:
    def test_do_not_change_is_present(self):
        """AC-85-03: do_not_change キーが存在する。"""
        result = _build()
        assert "do_not_change" in result

    def test_do_not_change_is_nonempty_list(self):
        """AC-85-03: do_not_change は空でないリスト。"""
        result = _build()
        dnc = result["do_not_change"]
        assert isinstance(dnc, list)
        assert len(dnc) > 0

    def test_do_not_change_reflects_forbidden_changes(self):
        """AC-85-03: forbidden_changes がある場合は do_not_change に反映される。"""
        spec = {"forbidden_changes": ["production/", "config/secrets.py"]}
        result = _build(spec=spec)
        assert "production/" in result["do_not_change"]

    def test_do_not_change_has_default_when_no_forbidden(self):
        """AC-85-03: forbidden_changes がない場合はデフォルト値が入る。"""
        result = _build(spec={})
        assert len(result["do_not_change"]) > 0


# ---------------------------------------------------------------------------
# AC-85-04: machine-readable JSON として保存できる
# ---------------------------------------------------------------------------
class TestRetryInstructionIsMachineReadableJson:
    def test_all_required_keys_present(self):
        """AC-85-04: 必須キーが全て存在する。"""
        result = _build()
        required = ["session_id", "failure_type", "priority",
                    "cause_summary", "fix_instructions", "do_not_change"]
        for key in required:
            assert key in result, f"必須キー {key!r} が存在しません"

    def test_serializable_to_json(self):
        """AC-85-04: JSON シリアライズが成功する（machine-readable）。"""
        result = _build()
        serialized = json.dumps(result, ensure_ascii=False)
        restored = json.loads(serialized)
        assert restored["session_id"] == result["session_id"]
        assert restored["failure_type"] == result["failure_type"]

    def test_priority_is_integer(self):
        """AC-85-04: priority は整数型。"""
        result = _build()
        assert isinstance(result["priority"], int)

    def test_schema_validator_passes_valid_instruction(self):
        """AC-85-04: validate_retry_instruction_schema は正常な instruction を通過させる。"""
        valid = {
            "session_id": "session-85",
            "failure_type": "test_failure",
            "priority": 6,
            "cause_summary": "some error",
            "fix_instructions": ["fix this"],
            "do_not_change": ["production/"],
        }
        validate_retry_instruction_schema(valid)  # 例外なし

    def test_schema_validator_rejects_empty_cause_summary(self):
        """AC-85-04: cause_summary が空なら ValueError。"""
        invalid = {
            "session_id": "session-85",
            "failure_type": "test_failure",
            "priority": 1,
            "cause_summary": "",
            "fix_instructions": ["fix"],
            "do_not_change": ["x"],
        }
        with pytest.raises(ValueError, match="cause_summary"):
            validate_retry_instruction_schema(invalid)

    def test_schema_validator_rejects_empty_fix_instructions(self):
        """AC-85-04: fix_instructions が空リストなら ValueError。"""
        invalid = {
            "session_id": "session-85",
            "failure_type": "test_failure",
            "priority": 1,
            "cause_summary": "error",
            "fix_instructions": [],
            "do_not_change": ["x"],
        }
        with pytest.raises(ValueError, match="fix_instructions"):
            validate_retry_instruction_schema(invalid)
