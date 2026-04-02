"""AC-89-01〜04: implementation prompt quality hardening テスト。"""
from orchestration.run_session import (
    build_implementation_prompts,
    SessionContext,
)


# ---------------------------------------------------------------------------
# テスト用ヘルパー
# ---------------------------------------------------------------------------
def _make_ctx(session_id: str = "session-89") -> SessionContext:
    return SessionContext(
        session_id=session_id,
        session_data={
            "session_id": session_id,
            "phase_id": "phase3",
            "title": "prompt hardening test",
            "goal": "test prompts",
            "scope": [],
            "out_of_scope": [],
            "constraints": [],
            "acceptance_ref": "docs/acceptance/session-89.yaml",
            "allowed_changes": ["orchestration/run_session.py"],
        },
        acceptance_data={"raw_yaml": "", "parsed": {}},
        master_instruction="",
        global_rules="",
        roadmap_text="",
        runtime_config={},
    )


def _build(retry_instruction=None):
    """build_implementation_prompts のショートカット。"""
    ctx = _make_ctx()
    system, user = build_implementation_prompts(
        prepared_spec={"objective": "implement feature"},
        ctx=ctx,
        retry_instruction=retry_instruction,
    )
    return system, user


# ---------------------------------------------------------------------------
# AC-89-01: implementation prompt に unified diff 必須の制約が含まれる
# ---------------------------------------------------------------------------
class TestImplementationPromptRequiresUnifiedDiff:
    def test_system_prompt_mentions_unified_diff(self):
        """AC-89-01: system prompt に 'unified diff' の記述がある。"""
        system, _ = _build()
        assert "unified diff" in system

    def test_system_prompt_mentions_diff_git_format(self):
        """AC-89-01: system prompt に diff --git ヘッダー形式の記述がある。"""
        system, _ = _build()
        assert "diff --git" in system

    def test_user_prompt_specifies_proposed_patch_as_unified_diff(self):
        """AC-89-01: user prompt の proposed_patch 説明に unified diff が言及される。"""
        _, user = _build()
        assert "unified diff" in user

    def test_system_prompt_mentions_hunk_header(self):
        """AC-89-01: @@ ハンクヘッダー形式が system prompt に含まれる。"""
        system, _ = _build()
        assert "@@" in system


# ---------------------------------------------------------------------------
# AC-89-02: implementation prompt に patch_status の有効値が明示される
# ---------------------------------------------------------------------------
class TestImplementationPromptListsValidPatchStatusValues:
    def test_system_prompt_lists_applied(self):
        """AC-89-02: 有効値 'applied' が system prompt に含まれる。"""
        system, _ = _build()
        assert "applied" in system

    def test_system_prompt_lists_not_applicable(self):
        """AC-89-02: 有効値 'not_applicable' が system prompt に含まれる。"""
        system, _ = _build()
        assert "not_applicable" in system

    def test_system_prompt_lists_dry_run(self):
        """AC-89-02: 有効値 'dry_run' が system prompt に含まれる。"""
        system, _ = _build()
        assert "dry_run" in system

    def test_system_prompt_lists_partial(self):
        """AC-89-02: 有効値 'partial' が system prompt に含まれる。"""
        system, _ = _build()
        assert "partial" in system

    def test_system_prompt_forbids_ready(self):
        """AC-89-02: 'ready' は無効値として system prompt に明示される。"""
        system, _ = _build()
        assert "ready" in system  # 禁止値として記述されていること

    def test_user_prompt_specifies_patch_status_valid_values(self):
        """AC-89-02: user prompt の patch_status 行に有効値リストが含まれる。"""
        _, user = _build()
        assert "applied" in user
        assert "not_applicable" in user


# ---------------------------------------------------------------------------
# AC-89-03: retry_instruction の fix_instructions が implementation prompt に反映される
# ---------------------------------------------------------------------------
class TestRetryFixInstructionsAreInjectedIntoImplementationPrompt:
    def test_fix_instructions_appear_in_user_prompt(self):
        """AC-89-03: retry_instruction の fix_instructions が user prompt に展開される。"""
        retry = {
            "failure_type": "test_failure",
            "cause_summary": "assert error",
            "fix_instructions": ["fix the assertion in test_foo", "update the expected value"],
            "do_not_change": ["production/"],
        }
        _, user = _build(retry_instruction=retry)
        assert "fix the assertion in test_foo" in user
        assert "update the expected value" in user

    def test_fix_instructions_block_label_appears(self):
        """AC-89-03: fix_instructions ブロックのラベルが user prompt に含まれる。"""
        retry = {
            "fix_instructions": ["do this fix"],
            "do_not_change": [],
        }
        _, user = _build(retry_instruction=retry)
        assert "fix_instructions" in user

    def test_no_fix_instructions_does_not_add_empty_block(self):
        """AC-89-03: fix_instructions が空なら余分なブロックは追加されない。"""
        retry = {
            "fix_instructions": [],
            "do_not_change": ["production/"],
        }
        _, user = _build(retry_instruction=retry)
        # 空の fix_instructions block は含まれないこと
        assert "[fix_instructions to apply]" not in user

    def test_without_retry_instruction_no_fix_block(self):
        """AC-89-03: retry_instruction がなければ fix_instructions ブロックは存在しない。"""
        _, user = _build()
        assert "[fix_instructions to apply]" not in user


# ---------------------------------------------------------------------------
# AC-89-04: retry_instruction の do_not_change が implementation prompt に反映される
# ---------------------------------------------------------------------------
class TestRetryDoNotChangeIsInjectedIntoImplementationPrompt:
    def test_do_not_change_appears_in_user_prompt(self):
        """AC-89-04: retry_instruction の do_not_change が user prompt に展開される。"""
        retry = {
            "fix_instructions": ["fix something"],
            "do_not_change": ["production/config.py", "database/migrations/"],
        }
        _, user = _build(retry_instruction=retry)
        assert "production/config.py" in user
        assert "database/migrations/" in user

    def test_do_not_change_block_label_appears(self):
        """AC-89-04: do_not_change ブロックのラベルが user prompt に含まれる。"""
        retry = {
            "fix_instructions": ["fix something"],
            "do_not_change": ["production/"],
        }
        _, user = _build(retry_instruction=retry)
        assert "do_not_change" in user

    def test_no_do_not_change_does_not_add_empty_block(self):
        """AC-89-04: do_not_change が空なら余分なブロックは追加されない。"""
        retry = {
            "fix_instructions": ["do this fix"],
            "do_not_change": [],
        }
        _, user = _build(retry_instruction=retry)
        assert "[do_not_change (must not touch these)]" not in user

    def test_without_retry_instruction_no_dnc_block(self):
        """AC-89-04: retry_instruction がなければ do_not_change ブロックは存在しない。"""
        _, user = _build()
        assert "[do_not_change (must not touch these)]" not in user
