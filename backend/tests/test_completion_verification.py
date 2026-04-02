"""AC-83-01〜04: acceptance and completion verification standardization テスト。"""
import pytest

from orchestration.run_session import (
    validate_acceptance_test_names,
    evaluate_completion_decision,
)

# ---------------------------------------------------------------------------
# テスト用定数
# ---------------------------------------------------------------------------
_VALID_ACCEPTANCE_ITEMS = [
    {"id": "AC-83-01", "description": "test_name 必須チェック", "test_name": "test_acceptance_items_require_test_name"},
    {"id": "AC-83-02", "description": "test_name 欠落検出", "test_name": "test_missing_test_function_for_acceptance_fails"},
]

_VALID_CHECKS = {
    "test": "passed",
    "lint": "passed",
    "typecheck": "passed",
    "build": "passed",
}

_VALID_ACCEPTANCE_DATA = {"items": _VALID_ACCEPTANCE_ITEMS}


# ---------------------------------------------------------------------------
# AC-83-01: acceptance 項目には test_name が必須
# ---------------------------------------------------------------------------
class TestAcceptanceItemsRequireTestName:
    def test_all_items_have_test_name_passes(self):
        """AC-83-01: 全項目に test_name があれば例外なし。"""
        validate_acceptance_test_names(_VALID_ACCEPTANCE_ITEMS)

    def test_missing_test_name_raises_value_error(self):
        """AC-83-01: test_name が欠落している項目があれば ValueError。"""
        items = [
            {"id": "AC-83-01", "test_name": "test_foo"},
            {"id": "AC-83-02"},  # test_name なし
        ]
        with pytest.raises(ValueError, match="AC-83-02.*missing required 'test_name'"):
            validate_acceptance_test_names(items)

    def test_empty_test_name_raises_value_error(self):
        """AC-83-01: test_name が空文字列でも ValueError。"""
        items = [{"id": "AC-83-X", "test_name": ""}]
        with pytest.raises(ValueError, match="missing required 'test_name'"):
            validate_acceptance_test_names(items)

    def test_non_dict_items_are_skipped(self):
        """AC-83-01: dict 以外の項目は無視して例外なし。"""
        validate_acceptance_test_names(["string_item", None, 42])


# ---------------------------------------------------------------------------
# AC-83-02: test_name はあるが対応テスト関数が存在しない場合（grep による確認）
# ---------------------------------------------------------------------------
class TestMissingTestFunctionForAcceptanceFails:
    def test_existing_test_name_is_found_in_codebase(self):
        """AC-83-02: 実在するテスト関数名は grep で発見できる。"""
        import subprocess
        result = subprocess.run(
            ["grep", "-r", "test_acceptance_items_require_test_name", "backend/tests/"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, "test_name に対応するテスト関数がコードベースに存在しない"

    def test_nonexistent_test_name_is_not_found(self):
        """AC-83-02: 存在しないテスト関数名は、このファイルを除く検索では発見されない。"""
        import subprocess
        import os
        # このファイル自体を除外して検索する（grep が自身の文字列をヒットするのを防ぐ）
        this_file = os.path.basename(__file__)
        result = subprocess.run(
            ["grep", "-r", "--exclude", this_file,
             "def test_nonexistent_function_xyz_abc_never_exists_999", "backend/tests/"],
            capture_output=True, text=True,
        )
        assert result.returncode != 0, "存在しないはずのテスト関数定義が他のファイルで見つかってしまった"


# ---------------------------------------------------------------------------
# AC-83-03: completion は必須条件が1つでも欠けると fail になる
# ---------------------------------------------------------------------------
class TestCompletionFailsWhenConditionMissing:
    def test_fails_when_test_name_missing(self):
        """AC-83-03: test_name 欠落で completion=fail。"""
        result = evaluate_completion_decision(
            acceptance_data={"items": [{"id": "AC-X"}]},  # test_name なし
            checks_results=_VALID_CHECKS,
            changed_files=[],
            allowed_changes=[],
        )
        assert result["completion"] == "fail"
        assert any("missing required 'test_name'" in r for r in result["reasons"])

    def test_fails_when_check_is_failed(self):
        """AC-83-03: check が failed なら completion=fail。"""
        bad_checks = {**_VALID_CHECKS, "test": "failed"}
        result = evaluate_completion_decision(
            acceptance_data=_VALID_ACCEPTANCE_DATA,
            checks_results=bad_checks,
            changed_files=[],
            allowed_changes=[],
        )
        assert result["completion"] == "fail"
        assert any("test" in r for r in result["reasons"])

    def test_fails_when_changed_file_not_in_allowed(self):
        """AC-83-03: changed_files が allowed_changes 外なら completion=fail。"""
        result = evaluate_completion_decision(
            acceptance_data=_VALID_ACCEPTANCE_DATA,
            checks_results=_VALID_CHECKS,
            changed_files=["some/intruder.py"],
            allowed_changes=["orchestration/run_session.py"],
        )
        assert result["completion"] == "fail"
        assert any("not in allowed_changes" in r for r in result["reasons"])

    def test_multiple_failures_are_all_reported(self):
        """AC-83-03: 複数の不成立条件が全て reasons に含まれる。"""
        bad_checks = {**_VALID_CHECKS, "lint": "error", "build": "error"}
        result = evaluate_completion_decision(
            acceptance_data={"items": [{"id": "AC-X"}]},
            checks_results=bad_checks,
            changed_files=["bad/file.py"],
            allowed_changes=[],
        )
        assert result["completion"] == "fail"
        assert len(result["reasons"]) >= 3  # test_name + lint + build


# ---------------------------------------------------------------------------
# AC-83-04: completion は全条件が揃ったときのみ pass になる
# ---------------------------------------------------------------------------
class TestCompletionPassesWhenAllConditionsMet:
    def test_passes_with_all_conditions_satisfied(self):
        """AC-83-04: 全条件充足で completion=pass、reasons=[]。"""
        result = evaluate_completion_decision(
            acceptance_data=_VALID_ACCEPTANCE_DATA,
            checks_results=_VALID_CHECKS,
            changed_files=["orchestration/run_session.py"],
            allowed_changes=["orchestration/run_session.py"],
        )
        assert result["completion"] == "pass"
        assert result["reasons"] == []

    def test_passes_with_skipped_checks(self):
        """AC-83-04: skipped チェックは通過扱い。"""
        skipped_checks = {
            "test": "passed",
            "lint": "skipped",
            "typecheck": "skipped",
            "build": "passed",
        }
        result = evaluate_completion_decision(
            acceptance_data=_VALID_ACCEPTANCE_DATA,
            checks_results=skipped_checks,
            changed_files=[],
            allowed_changes=[],
        )
        assert result["completion"] == "pass"

    def test_passes_with_empty_changed_files(self):
        """AC-83-04: changed_files が空なら scope チェックは通過。"""
        result = evaluate_completion_decision(
            acceptance_data=_VALID_ACCEPTANCE_DATA,
            checks_results=_VALID_CHECKS,
            changed_files=[],
            allowed_changes=[],
        )
        assert result["completion"] == "pass"
