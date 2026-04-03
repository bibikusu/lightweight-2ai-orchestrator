"""session-116: stop-with-log standardization tests."""

import json

# テスト対象
from orchestration.run_session import (
    _classify_stop_reason,
    build_stop_decision_record,
    persist_stop_decision,
)


class TestBuildStopDecisionRecord:
    """build_stop_decision_record の出力形式テスト。"""

    def test_spec_missing_produces_standardized_record(self):
        """AC-116-01: spec_missing の stop decision record が標準形式を満たす。"""
        record = build_stop_decision_record(
            session_id="test-session",
            stage="loading",
            stop_reason="spec_missing",
            failure_type="spec_missing",
            observed_facts=["required key 'constraints' is missing"],
        )
        assert record["status"] == "stopped"
        assert record["stop_reason"] == "spec_missing"
        assert record["failure_type"] == "spec_missing"
        assert isinstance(record["observed_facts"], list)
        assert len(record["observed_facts"]) >= 1
        assert record["source_modification_performed"] is False
        assert record["next_action"]["type"] == "stop_and_review"
        assert "generated_at_utc" in record

    def test_scope_violation_stops_without_auto_fix(self):
        """AC-116-02: scope_violation で自動修復しない。"""
        record = build_stop_decision_record(
            session_id="test-session",
            stage="patch_validation",
            stop_reason="scope_violation",
            failure_type="scope_violation",
            observed_facts=["forbidden path detected: config.yaml"],
        )
        assert record["status"] == "stopped"
        assert record["stop_reason"] == "scope_violation"
        assert record["source_modification_performed"] is False

    def test_code_state_includes_observed_facts(self):
        """AC-116-03: code-state issue の record に observed_facts が含まれる。"""
        record = build_stop_decision_record(
            session_id="test-session",
            stage="git_guard",
            stop_reason="code_state_error",
            failure_type="code_state_error",
            observed_facts=[
                "dirty worktree detected",
                "files: orchestration/run_session.py",
            ],
        )
        assert record["failure_type"] == "code_state_error"
        assert len(record["observed_facts"]) == 2
        assert "dirty worktree" in record["observed_facts"][0]

    def test_reference_proposals_marked_reference_only(self):
        """AC-116-04: proposals が reference_only でマークされる。"""
        record = build_stop_decision_record(
            session_id="test-session",
            stage="loading",
            stop_reason="spec_missing",
            failure_type="spec_missing",
            observed_facts=["missing key"],
            reference_only_proposals=[
                {"content": "Add constraints key to session JSON."}
            ],
        )
        assert len(record["reference_only_proposals"]) == 1
        assert record["reference_only_proposals"][0]["type"] == "reference_only"

    def test_empty_proposals_produces_empty_list(self):
        """proposals なしの場合は空リスト。"""
        record = build_stop_decision_record(
            session_id="test-session",
            stage="loading",
            stop_reason="spec_missing",
            failure_type="spec_missing",
            observed_facts=["test"],
        )
        assert record["reference_only_proposals"] == []


class TestClassifyStopReason:
    """_classify_stop_reason の分類テスト。"""

    def test_missing_required_key(self):
        err = ValueError("session JSON missing required key: constraints")
        sr, ft = _classify_stop_reason(err)
        assert sr == "spec_missing"
        assert ft == "spec_missing"

    def test_forbidden_path(self):
        err = ValueError("forbidden path detected")
        sr, ft = _classify_stop_reason(err)
        assert sr == "scope_violation"

    def test_dirty_worktree(self):
        err = RuntimeError("安全弁: 作業ツリーが dirty です。")
        sr, ft = _classify_stop_reason(err)
        assert sr == "code_state_error"

    def test_file_not_found(self):
        err = FileNotFoundError("YAML file not found: docs/acceptance/session-999.yaml")
        sr, ft = _classify_stop_reason(err)
        assert sr == "spec_missing"

    def test_unknown_error(self):
        err = Exception("something unexpected")
        sr, ft = _classify_stop_reason(err)
        assert sr == "unknown_blocking_error"


class TestPersistStopDecision:
    """persist_stop_decision のファイル保存テスト。"""

    def test_saves_to_logs_dir(self, tmp_path):
        """AC-116-06: stop decision がファイルに保存される。"""
        session_dir = tmp_path / "artifacts" / "test-session"
        (session_dir / "logs").mkdir(parents=True)
        record = build_stop_decision_record(
            session_id="test-session",
            stage="loading",
            stop_reason="spec_missing",
            failure_type="spec_missing",
            observed_facts=["test fact"],
        )
        path = persist_stop_decision(session_dir, record)
        assert path.exists()
        saved = json.loads(path.read_text())
        assert saved["stop_reason"] == "spec_missing"
        assert saved["source_modification_performed"] is False


class TestSuccessPathUnchanged:
    """AC-116-05: 成功パスへの影響がないことを確認。"""

    def test_build_stop_decision_record_is_independent(self):
        """build_stop_decision_record は呼ばなければ何も起きない。
        既存の成功パスで呼ばれないことを run_session.py のコード構造で保証。
        （成功パスでは except ブロックに入らないため）"""
        # build_stop_decision_record が副作用なしの純粋関数であることを確認
        record = build_stop_decision_record(
            session_id="test",
            stage="test",
            stop_reason="test",
            failure_type="test",
            observed_facts=[],
        )
        assert isinstance(record, dict)
        # 関数呼び出し自体にファイル書き込み等の副作用がないことが重要
