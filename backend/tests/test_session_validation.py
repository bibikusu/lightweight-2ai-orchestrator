"""AC-81-01〜05: session.json / acceptance.yaml の input guard テスト。"""
import pytest
from pathlib import Path
from orchestration.run_session import (
    validate_session_required_keys,
    resolve_acceptance_path,
    validate_session_id_consistency,
    run_preflight_validation,
    ROOT_DIR,
    DOCS_DIR,
)

# ---------------------------------------------------------------------------
# テスト用定数
# ---------------------------------------------------------------------------
_VALID_SESSION: dict = {
    "session_id": "session-81",
    "phase_id": "phase-1",
    "title": "input guard",
    "goal": "fail fast on bad input",
    "scope": ["validation"],
    "out_of_scope": ["deployment"],
    "constraints": ["no side effects"],
    "acceptance_ref": "docs/acceptance/session-81.yaml",
}

_VALID_ACCEPTANCE: dict = {"session_id": "session-81"}


# ---------------------------------------------------------------------------
# AC-81-01: 必須キーがすべて揃っていれば例外なし
# ---------------------------------------------------------------------------
class TestValidateSessionRequiredKeys:
    def test_all_keys_present_no_error(self):
        """AC-81-01: 必須キーが全部あれば ValueError が起きない。"""
        validate_session_required_keys(_VALID_SESSION)  # 例外なし

    def test_missing_key_raises_value_error(self):
        """AC-81-01: 必須キーが欠落すると ValueError が起きる。"""
        for key in ["session_id", "phase_id", "title", "goal", "scope",
                    "out_of_scope", "constraints", "acceptance_ref"]:
            broken = {k: v for k, v in _VALID_SESSION.items() if k != key}
            with pytest.raises(ValueError, match=f"missing required key: {key}"):
                validate_session_required_keys(broken)


# ---------------------------------------------------------------------------
# AC-81-02: acceptance_ref のパス解決
# ---------------------------------------------------------------------------
class TestResolveAcceptancePath:
    def test_docs_prefix_resolves_to_root(self):
        """AC-81-02: docs/ 始まりは ROOT_DIR 基準で解決される。"""
        ref = "docs/acceptance/session-81.yaml"
        result = resolve_acceptance_path(ref, ROOT_DIR, DOCS_DIR)
        assert result == ROOT_DIR / ref

    def test_no_prefix_resolves_to_docs(self):
        """AC-81-02: docs/ なしは DOCS_DIR 基準で解決される。"""
        ref = "acceptance/session-81.yaml"
        result = resolve_acceptance_path(ref, ROOT_DIR, DOCS_DIR)
        assert result == DOCS_DIR / ref

    def test_whitespace_stripped(self):
        """AC-81-02: 前後の空白は除去される。"""
        ref = "  docs/acceptance/session-81.yaml  "
        result = resolve_acceptance_path(ref, ROOT_DIR, DOCS_DIR)
        assert result == ROOT_DIR / "docs/acceptance/session-81.yaml"


# ---------------------------------------------------------------------------
# AC-81-03: session_id 一致チェック
# ---------------------------------------------------------------------------
class TestValidateSessionIdConsistency:
    def test_matching_ids_no_error(self):
        """AC-81-03: session_id が一致すれば例外なし。"""
        validate_session_id_consistency(
            {"session_id": "session-81"},
            {"session_id": "session-81"},
        )

    def test_mismatch_raises_value_error(self):
        """AC-81-03: session_id が不一致なら ValueError。"""
        with pytest.raises(ValueError, match="session_id mismatch"):
            validate_session_id_consistency(
                {"session_id": "session-81"},
                {"session_id": "session-99"},
            )

    def test_missing_acceptance_id_raises(self):
        """AC-81-03: acceptance.yaml に session_id がなければ不一致扱い。"""
        with pytest.raises(ValueError, match="session_id mismatch"):
            validate_session_id_consistency(
                {"session_id": "session-81"},
                {},
            )


# ---------------------------------------------------------------------------
# AC-81-04: run_preflight_validation — 正常系
# ---------------------------------------------------------------------------
class TestRunPreflightValidationSuccess:
    def test_valid_inputs_no_error(self, tmp_path: Path):
        """AC-81-04: 正常な入力ではすべてのチェックが通る。"""
        # acceptance ファイルを tmp_path に作成
        acceptance_file = tmp_path / "session-81.yaml"
        acceptance_file.write_text("session_id: session-81\n", encoding="utf-8")

        run_preflight_validation(
            session_data=_VALID_SESSION,
            acceptance_parsed=_VALID_ACCEPTANCE,
            acceptance_ref=str(acceptance_file),  # 絶対パス（docs/ なし）
            root_dir=tmp_path,
            docs_dir=tmp_path,
        )


# ---------------------------------------------------------------------------
# AC-81-05: run_preflight_validation — 異常系
# ---------------------------------------------------------------------------
class TestRunPreflightValidationFailure:
    def test_missing_key_raises(self, tmp_path: Path):
        """AC-81-05: 必須キー欠落で ValueError。"""
        broken = {k: v for k, v in _VALID_SESSION.items() if k != "goal"}
        with pytest.raises(ValueError, match="missing required key: goal"):
            run_preflight_validation(
                session_data=broken,
                acceptance_parsed=_VALID_ACCEPTANCE,
                acceptance_ref="session-81.yaml",
                root_dir=tmp_path,
                docs_dir=tmp_path,
            )

    def test_file_not_found_raises(self, tmp_path: Path):
        """AC-81-05: acceptance ファイルが存在しなければ FileNotFoundError。"""
        with pytest.raises(FileNotFoundError, match="acceptance file not found"):
            run_preflight_validation(
                session_data=_VALID_SESSION,
                acceptance_parsed=_VALID_ACCEPTANCE,
                acceptance_ref="nonexistent.yaml",
                root_dir=tmp_path,
                docs_dir=tmp_path,
            )

    def test_session_id_mismatch_raises(self, tmp_path: Path):
        """AC-81-05: session_id 不一致で ValueError。"""
        acceptance_file = tmp_path / "session-81.yaml"
        acceptance_file.write_text("session_id: session-99\n", encoding="utf-8")

        with pytest.raises(ValueError, match="session_id mismatch"):
            run_preflight_validation(
                session_data=_VALID_SESSION,
                acceptance_parsed={"session_id": "session-99"},
                acceptance_ref=str(acceptance_file),
                root_dir=tmp_path,
                docs_dir=tmp_path,
            )
