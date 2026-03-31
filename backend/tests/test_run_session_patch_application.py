from pathlib import Path
from typing import Any, Dict, List

import orchestration.run_session as run_session


class _DummyCompletedProcess:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _recording_git_run_factory(calls: List[List[str]]) -> Any:
    def _git_run(args: List[str], *, check: bool = False) -> _DummyCompletedProcess:
        # 呼び出し履歴を記録するだけの簡易スタブ
        calls.append(args)
        if args[:2] == ["diff", "--name-only"]:
            return _DummyCompletedProcess(
                returncode=0,
                stdout="foo.py\nbar/baz.txt\n",
                stderr="",
            )
        if args[0] == "apply":
            return _DummyCompletedProcess(returncode=0, stdout="", stderr="")
        # その他のサブコマンドは成功扱い・出力なし
        return _DummyCompletedProcess(returncode=0, stdout="", stderr="")

    return _git_run


def test_apply_proposed_patch_saves_file_and_uses_git_apply(tmp_path: Path, monkeypatch) -> None:
    calls: List[List[str]] = []
    monkeypatch.setattr(
        run_session,
        "_git_run",
        _recording_git_run_factory(calls),
        raising=True,
    )

    session_dir = tmp_path
    impl_result: Dict[str, Any] = {
        "proposed_patch": "diff --git a/foo.py b/foo.py\n",
        "changed_files": [],
    }

    info = run_session.apply_proposed_patch_and_capture_artifacts(session_dir, impl_result)

    patch_path = info["patch_path"]
    assert Path(patch_path).is_file()
    assert "diff --git" in Path(patch_path).read_text(encoding="utf-8")

    changed = info["changed_files"]
    assert sorted(changed) == ["bar/baz.txt", "foo.py"]

    # git apply と git diff --name-only が呼ばれていることを確認
    apply_called = any(call[0] == "apply" for call in calls)
    diff_called = any(call[:2] == ["diff", "--name-only"] for call in calls)
    assert apply_called
    assert diff_called


def test_apply_proposed_patch_handles_empty_patch(tmp_path: Path, monkeypatch) -> None:
    def _git_run(args: List[str], *, check: bool = False) -> _DummyCompletedProcess:
        # 空パッチの場合は git apply は呼ばれず、diff だけ呼ばれる
        if args[:2] == ["diff", "--name-only"]:
            return _DummyCompletedProcess(returncode=0, stdout="", stderr="")
        return _DummyCompletedProcess(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(run_session, "_git_run", _git_run, raising=True)

    session_dir = tmp_path
    impl_result: Dict[str, Any] = {
        "proposed_patch": "",
        "changed_files": ["should_be_ignored.py"],
    }

    info = run_session.apply_proposed_patch_and_capture_artifacts(session_dir, impl_result)

    # 空パッチでも artifacts/patches にファイルが保存される
    patch_path = info["patch_path"]
    assert Path(patch_path).is_file()

    # 実差分ゼロなので changed_files も空になる
    assert info["changed_files"] == []
