"""preflight guard のテスト（AC-101-01〜04）。"""
from unittest.mock import patch, MagicMock

import pytest

from orchestration.run_session import preflight_cleanup, validate_before_run


# ---------------------------------------------------------------------------
# AC-101-01: 既知の残留ファイルを自動削除する
# ---------------------------------------------------------------------------
def test_preflight_cleans_known_residue(tmp_path, monkeypatch):
    """backend/tests/test_*.py の未追跡ファイルが削除される。"""
    monkeypatch.chdir(tmp_path)

    # 残留ファイルを模擬
    residue = tmp_path / "backend" / "tests" / "test_provider_usage.py"
    residue.parent.mkdir(parents=True)
    residue.write_text("# residue")

    # ROOT_DIR を tmp_path に差し替え
    import orchestration.run_session as rs
    monkeypatch.setattr(rs, "ROOT_DIR", tmp_path)

    # git status --porcelain の出力を模擬（未追跡ファイル）
    mock_proc = MagicMock(returncode=0, stdout="?? backend/tests/test_provider_usage.py\n", stderr="")
    with patch.object(rs, "_git_run", return_value=mock_proc):
        removed = preflight_cleanup()

    assert "backend/tests/test_provider_usage.py" in removed
    assert not residue.exists()


# ---------------------------------------------------------------------------
# AC-101-02: 未知の dirty worktree で停止し明確なエラーを出す
# ---------------------------------------------------------------------------
def test_preflight_stops_on_unknown_dirty():
    """追跡済みファイルの変更は自動削除せず RuntimeError を出す。"""
    import orchestration.run_session as rs

    mock_proc = MagicMock(returncode=0, stdout=" M orchestration/run_session.py\n", stderr="")
    with patch.object(rs, "_git_run", return_value=mock_proc):
        with pytest.raises(RuntimeError) as exc_info:
            validate_before_run()

    assert "Dirty worktree detected" in str(exc_info.value)
    assert "orchestration/run_session.py" in str(exc_info.value)


# ---------------------------------------------------------------------------
# AC-101-03: clean worktree では validate_before_run が正常完了する
# ---------------------------------------------------------------------------
def test_run_session_completes_when_clean():
    """clean worktree では validate_before_run が例外を出さない。"""
    import orchestration.run_session as rs

    mock_proc = MagicMock(returncode=0, stdout="", stderr="")
    with patch.object(rs, "_git_run", return_value=mock_proc):
        validate_before_run()  # 例外が出なければ合格


# ---------------------------------------------------------------------------
# AC-101-04: 既存テストに対してリグレッションがない
# ---------------------------------------------------------------------------
def test_no_regression():
    """preflight_cleanup が clean な worktree で空リストを返す。"""
    import orchestration.run_session as rs

    mock_proc = MagicMock(returncode=0, stdout="", stderr="")
    with patch.object(rs, "_git_run", return_value=mock_proc):
        removed = preflight_cleanup()

    assert removed == []
