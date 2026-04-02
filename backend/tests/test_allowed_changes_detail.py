"""AC-82-01〜04: allowed_changes_detail enforcement hardening テスト。"""
import pytest
from typing import Optional

from orchestration.run_session import (
    validate_allowed_changes_detail_enforcement,
    validate_changed_files_before_patch,
)

# ---------------------------------------------------------------------------
# テスト用定数
# ---------------------------------------------------------------------------
_DETAIL_LIST = [
    "orchestration/run_session.py: オーケストレーション本体",
    "backend/tests/*: テストファイル全般",
    "docs/sessions/session-82.json: セッション定義",
]


# ---------------------------------------------------------------------------
# AC-82-01: allowed_changes_detail に違反する changed_files は拒否される
# ---------------------------------------------------------------------------
class TestAllowedChangesDetailViolationFails:
    def test_unknown_file_raises_value_error(self):
        """AC-82-01: detail に含まれないファイルは ValueError。"""
        with pytest.raises(ValueError, match="allowed_changes_detail に含まれていません"):
            validate_allowed_changes_detail_enforcement(
                changed_files=["some/unknown/file.py"],
                allowed_changes_detail=_DETAIL_LIST,
            )

    def test_multiple_files_with_one_violation_raises(self):
        """AC-82-01: 複数ファイルのうち1つでも違反があれば ValueError。"""
        with pytest.raises(ValueError, match="allowed_changes_detail に含まれていません"):
            validate_allowed_changes_detail_enforcement(
                changed_files=[
                    "orchestration/run_session.py",
                    "intruder/evil.py",  # 違反
                ],
                allowed_changes_detail=_DETAIL_LIST,
            )


# ---------------------------------------------------------------------------
# AC-82-02: 明示的に許可された changed_files は通過する
# ---------------------------------------------------------------------------
class TestExplicitlyAllowedFilesPassValidation:
    def test_exact_match_passes(self):
        """AC-82-02: 完全一致パスは通過する。"""
        validate_allowed_changes_detail_enforcement(
            changed_files=["orchestration/run_session.py"],
            allowed_changes_detail=_DETAIL_LIST,
        )

    def test_wildcard_directory_match_passes(self):
        """AC-82-02: ワイルドカード (backend/tests/*) 配下のファイルは通過する。"""
        validate_allowed_changes_detail_enforcement(
            changed_files=["backend/tests/test_foo.py"],
            allowed_changes_detail=_DETAIL_LIST,
        )

    def test_empty_changed_files_passes(self):
        """AC-82-02: changed_files が空なら常に通過する。"""
        validate_allowed_changes_detail_enforcement(
            changed_files=[],
            allowed_changes_detail=_DETAIL_LIST,
        )

    def test_empty_detail_list_skips_check(self):
        """AC-82-02: allowed_changes_detail が空リストなら検証をスキップする。"""
        # 何も raise されないことを確認
        validate_allowed_changes_detail_enforcement(
            changed_files=["any/file.py"],
            allowed_changes_detail=[],
        )


# ---------------------------------------------------------------------------
# AC-82-03: 既存の validate_patch_files の動作は保持される
# ---------------------------------------------------------------------------
class TestScopeHardeningPreservesExistingBehavior:
    """validate_changed_files_before_patch の基本動作が壊れていないことを確認する。"""

    def _make_impl_result(self, files: list) -> dict:
        return {"changed_files": files}

    def _make_prepared_spec(self, allowed: Optional[list] = None) -> dict:
        spec: dict = {}
        if allowed is not None:
            spec["allowed_changes"] = allowed
        return spec

    def test_no_changed_files_passes(self):
        """AC-82-03: changed_files が空なら既存チェックは通過する。"""
        validate_changed_files_before_patch(
            impl_result={"changed_files": []},
            prepared_spec=self._make_prepared_spec(),
            session_data={},
            max_changed_files=10,
        )

    def test_allowed_file_passes_existing_check(self):
        """AC-82-03: allowed_changes に含まれるファイルは既存チェックを通過する。"""
        validate_changed_files_before_patch(
            impl_result={"changed_files": ["orchestration/run_session.py"]},
            prepared_spec=self._make_prepared_spec(["orchestration/run_session.py"]),
            session_data={},
            max_changed_files=10,
        )


# ---------------------------------------------------------------------------
# AC-82-04: allowed_changes_detail がある場合のみ詳細検証が走る
# ---------------------------------------------------------------------------
class TestPostPatchScopeVerificationCondition:
    def test_detail_check_runs_only_when_key_present(self):
        """AC-82-04: session_data に allowed_changes_detail がなければ詳細チェックは走らない。"""
        # allowed_changes_detail なし → 違反ファイルでも通過すること
        validate_changed_files_before_patch(
            impl_result={"changed_files": ["any/uncovered/file.py"]},
            prepared_spec={"allowed_changes": ["any/uncovered/file.py"]},
            session_data={},  # allowed_changes_detail なし
            max_changed_files=10,
        )

    def test_detail_check_runs_when_key_present_and_rejects_violation(self):
        """AC-82-04: allowed_changes_detail がある場合は詳細チェックが走り違反を拒否する。"""
        with pytest.raises(ValueError, match="allowed_changes_detail に含まれていません"):
            validate_changed_files_before_patch(
                impl_result={"changed_files": ["intruder/evil.py"]},
                prepared_spec={"allowed_changes": []},
                session_data={
                    "allowed_changes_detail": [
                        "orchestration/run_session.py: 本体のみ",
                    ]
                },
                max_changed_files=10,
            )
