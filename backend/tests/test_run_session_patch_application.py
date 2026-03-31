from pathlib import Path
from typing import Any, Dict, List
import json

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
        if args[:3] == ["ls-files", "--others", "--exclude-standard"]:
            return _DummyCompletedProcess(
                returncode=0,
                stdout="new_file.py\n",
                stderr="",
            )
        if args[0] == "apply":
            return _DummyCompletedProcess(returncode=0, stdout="", stderr="")
        # その他のサブコマンドは成功扱い・出力なし
        return _DummyCompletedProcess(returncode=0, stdout="", stderr="")

    return _git_run


def test_apply_implementation_result_updates_changed_files_from_git_diff(tmp_path: Path, monkeypatch) -> None:
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

    # git apply / git diff --name-only / git ls-files が呼ばれていることを確認
    apply_called = any(call[0] == "apply" for call in calls)
    diff_called = any(call[:2] == ["diff", "--name-only"] for call in calls)
    ls_files_called = any(
        call[:3] == ["ls-files", "--others", "--exclude-standard"] for call in calls
    )
    assert apply_called
    assert diff_called
    assert ls_files_called


def test_apply_implementation_result_detects_untracked_files_after_apply(
    tmp_path: Path, monkeypatch
) -> None:
    def _git_run(args: List[str], *, check: bool = False) -> _DummyCompletedProcess:
        if args[0] == "apply":
            return _DummyCompletedProcess(returncode=0, stdout="", stderr="")
        if args[:2] == ["diff", "--name-only"]:
            return _DummyCompletedProcess(returncode=0, stdout="", stderr="")
        if args[:3] == ["ls-files", "--others", "--exclude-standard"]:
            return _DummyCompletedProcess(
                returncode=0,
                stdout="new_file.py\nnot_in_patch.txt\n",
                stderr="",
            )
        return _DummyCompletedProcess(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(run_session, "_git_run", _git_run, raising=True)

    session_dir = tmp_path
    impl_result: Dict[str, Any] = {
        "proposed_patch": "diff --git a/new_file.py b/new_file.py\n+++ b/new_file.py\n",
        "changed_files": [],
    }

    info = run_session.apply_proposed_patch_and_capture_artifacts(session_dir, impl_result)
    assert info["changed_files"] == ["new_file.py"]


def test_apply_implementation_result_reflects_untracked_files_in_report_success_path(
    tmp_path: Path, monkeypatch
) -> None:
    def _git_run(args: List[str], *, check: bool = False) -> _DummyCompletedProcess:
        if args[:2] == ["rev-parse", "--git-dir"]:
            return _DummyCompletedProcess(returncode=0, stdout=".git\n", stderr="")
        if args[:3] == ["rev-parse", "--abbrev-ref", "HEAD"]:
            return _DummyCompletedProcess(returncode=0, stdout="sandbox/session-60\n", stderr="")
        if args[:2] == ["rev-parse", "HEAD"]:
            return _DummyCompletedProcess(returncode=0, stdout="abc123\n", stderr="")
        if args[0] == "apply":
            return _DummyCompletedProcess(returncode=0, stdout="", stderr="")
        if args[:2] == ["diff", "--name-only"]:
            return _DummyCompletedProcess(returncode=0, stdout="", stderr="")
        if args[:3] == ["ls-files", "--others", "--exclude-standard"]:
            return _DummyCompletedProcess(returncode=0, stdout="new_file.py\n", stderr="")
        return _DummyCompletedProcess(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(run_session, "_git_run", _git_run, raising=True)

    patch_info = run_session.apply_proposed_patch_and_capture_artifacts(
        tmp_path,
        {
            "proposed_patch": "diff --git a/new_file.py b/new_file.py\n+++ b/new_file.py\n",
            "changed_files": [],
            "risks": [],
            "open_issues": [],
            "implementation_summary": [],
        },
    )

    ctx = run_session.SessionContext(
        session_id="session-60",
        session_data={"phase_id": "p1", "title": "t", "goal": "g"},
        acceptance_data={"parsed": {"acceptance": []}, "raw_yaml": ""},
        master_instruction="",
        global_rules="",
        roadmap_text="",
        runtime_config={},
    )
    impl_result = {
        "changed_files": patch_info["changed_files"],
        "risks": [],
        "open_issues": [],
        "implementation_summary": [],
    }
    checks = {
        "test": {"status": "passed"},
        "lint": {"status": "passed"},
        "typecheck": {"status": "passed"},
        "build": {"status": "passed"},
        "success": True,
        "test_function_results": {},
    }

    run_session.persist_session_reports(
        session_dir=tmp_path,
        ctx=ctx,
        prepared_spec={"objective": "obj"},
        impl_result=impl_result,
        checks=checks,
        status="success",
        dry_run=False,
        started_at="2026-03-31T00:00:00+00:00",
        finished_at="2026-03-31T00:00:01+00:00",
    )

    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert report["status"] == "success"
    assert report["changed_files"] == ["new_file.py"]


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
