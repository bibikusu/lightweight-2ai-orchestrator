"""AC-84-01〜04: failure classification and retry dedup unification テスト。"""
import pytest

from orchestration.run_session import (
    FAILURE_TYPE_PRIORITY_ORDER,
    VALID_FAILURE_TYPES,
    validate_failure_type,
    normalize_failure_type_by_priority,
    retry_loop,
)


# ---------------------------------------------------------------------------
# AC-84-01: 未知の failure_type は reject される
# ---------------------------------------------------------------------------
class TestFailureTypeRejectsUnknownValue:
    def test_known_type_passes(self):
        """AC-84-01: 定義済み failure_type は ValidationError を起こさない。"""
        for ft in VALID_FAILURE_TYPES:
            result = validate_failure_type(ft)
            assert result == ft

    def test_unknown_type_raises_value_error(self):
        """AC-84-01: 未定義の failure_type は ValueError。"""
        with pytest.raises(ValueError, match="Unknown failure_type"):
            validate_failure_type("completely_unknown_type")

    def test_empty_string_raises_value_error(self):
        """AC-84-01: 空文字列は ValueError。"""
        with pytest.raises(ValueError, match="Unknown failure_type"):
            validate_failure_type("")

    def test_error_message_includes_valid_list(self):
        """AC-84-01: エラーメッセージに有効な型リストが含まれる。"""
        with pytest.raises(ValueError, match="Valid:"):
            validate_failure_type("bad_type")


# ---------------------------------------------------------------------------
# AC-84-02: failure_type は priority 順で正規化される
# ---------------------------------------------------------------------------
class TestFailureTypeNormalizedToHighestPriority:
    def test_highest_priority_wins(self):
        """AC-84-02: patch_apply_failure は全 failure_type の最高優先度。"""
        result = normalize_failure_type_by_priority([
            "test_failure",
            "patch_apply_failure",
            "scope_violation",
        ])
        assert result == "patch_apply_failure"

    def test_single_candidate_is_returned(self):
        """AC-84-02: 候補が1つなら無条件でそれを返す。"""
        assert normalize_failure_type_by_priority(["build_error"]) == "build_error"

    def test_empty_candidates_returns_spec_missing(self):
        """AC-84-02: 候補が空なら 'spec_missing' を返す。"""
        assert normalize_failure_type_by_priority([]) == "spec_missing"

    def test_unknown_types_fall_to_lowest_priority(self):
        """AC-84-02: 未知の型は最低優先度扱いとなり、既知型に負ける。"""
        result = normalize_failure_type_by_priority(["unknown_type", "build_error"])
        assert result == "build_error"

    def test_priority_order_is_consistent_with_priority_list(self):
        """AC-84-02: FAILURE_TYPE_PRIORITY_ORDER の先頭が常に最高優先度。"""
        # 順序リストの全ペアで優先度が正しいことを確認する
        for i in range(len(FAILURE_TYPE_PRIORITY_ORDER) - 1):
            high = FAILURE_TYPE_PRIORITY_ORDER[i]
            low = FAILURE_TYPE_PRIORITY_ORDER[i + 1]
            assert normalize_failure_type_by_priority([high, low]) == high


# ---------------------------------------------------------------------------
# AC-84-03: 同一原因の retry は停止する
# ---------------------------------------------------------------------------
class TestRetryStopsOnSameCause:
    def test_same_failure_type_and_summary_stops_retry(self):
        """AC-84-03: failure_type と cause_summary が同一なら retry を停止する。"""
        history = [{"failure_type": "test_failure", "cause_summary": "assert error"}]
        result = retry_loop(
            retry_history=history,
            failure={"failure_type": "test_failure", "cause_summary": "assert error"},
            retry_count=1,
            max_retries=3,
        )
        assert result["should_retry"] is False

    def test_same_cause_stops_regardless_of_retry_count(self):
        """AC-84-03: retry_count が上限未満でも同一原因なら停止する。"""
        history = [{"failure_type": "build_error", "cause_summary": "syntax error"}]
        result = retry_loop(
            retry_history=history,
            failure={"failure_type": "build_error", "cause_summary": "syntax error"},
            retry_count=0,
            max_retries=5,
        )
        assert result["should_retry"] is False


# ---------------------------------------------------------------------------
# AC-84-04: 異なる原因は上限内なら retry を継続する
# ---------------------------------------------------------------------------
class TestRetryContinuesForDistinctCause:
    def test_different_failure_type_allows_retry(self):
        """AC-84-04: history の末尾と failure_type が異なれば retry を継続する。"""
        # retry_loop は failure_type_repeated（末尾と同型）でも停止する仕様のため、
        # 異なる failure_type を組み合わせて継続ケースを確認する
        history = [{"failure_type": "build_error", "cause_summary": "compile error"}]
        result = retry_loop(
            retry_history=history,
            failure={"failure_type": "test_failure", "cause_summary": "assert error"},
            retry_count=1,
            max_retries=3,
        )
        assert result["should_retry"] is True

    def test_empty_history_allows_retry_within_limit(self):
        """AC-84-04: 履歴が空で上限未満なら retry を継続する。"""
        result = retry_loop(
            retry_history=[],
            failure={"failure_type": "test_failure", "cause_summary": "first error"},
            retry_count=0,
            max_retries=3,
        )
        assert result["should_retry"] is True

    def test_max_retries_reached_stops_retry(self):
        """AC-84-04: 上限に達したら異なる原因でも停止する。"""
        result = retry_loop(
            retry_history=[],
            failure={"failure_type": "test_failure", "cause_summary": "some error"},
            retry_count=3,
            max_retries=3,
        )
        assert result["should_retry"] is False
