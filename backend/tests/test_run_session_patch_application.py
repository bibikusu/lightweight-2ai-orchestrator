# -*- coding: utf-8 -*-

import subprocess

import orchestration.run_session as rs


def _cp(args: list[str], returncode: int = 0, stdout: str = "", stderr: str = ""):
    return subprocess.CompletedProcess(args=args, returncode=returncode, stdout=stdout, stderr=stderr)


def test_apply_implementation_result_writes_new_file(monkeypatch, tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    session_dir = tmp_path / "session-artifacts"
    impl_result = {
        "proposed_patch": (
            "diff --git a/backend/new_file.py b/backend/new_file.py\n"
            "new file mode 100644\n"
            "--- /dev/null\n"
            "+++ b/backend/new_file.py\n"
            "@@\n"
            "+print('ok')\n"
        )
    }

    def _git_run(args, check=False):
        if args[0] == "apply":
            p = repo_root / "backend" / "new_file.py"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("print('ok')\n", encoding="utf-8")
            return _cp(args)
        if args == ["diff"]:
            return _cp(args, stdout="diff --git a/backend/new_file.py b/backend/new_file.py\n")
        if args == ["diff", "--name-only"]:
            return _cp(args, stdout="backend/new_file.py\n")
        raise AssertionError(f"unexpected git args: {args}")

    monkeypatch.setattr(rs, "ROOT_DIR", repo_root)
    monkeypatch.setattr(rs, "_git_run", _git_run)

    meta = rs.apply_proposed_patch_and_capture_artifacts(
        session_id="session-58",
        session_dir=session_dir,
        impl_result=impl_result,
    )

    assert (repo_root / "backend" / "new_file.py").is_file()
    assert meta["patch_applied"] is True
    assert meta["git_apply_returncode"] == 0


def test_apply_implementation_result_saves_patch_artifact(monkeypatch, tmp_path):
    repo_root = tmp_path / "repo-root"
    repo_root.mkdir(parents=True, exist_ok=True)
    session_dir = tmp_path / "tmp" / "session-58"

    def _git_run(args, check=False):
        if args == ["diff"]:
            return _cp(args, stdout="")
        if args == ["diff", "--name-only"]:
            return _cp(args, stdout="")
        raise AssertionError(f"unexpected git args: {args}")

    monkeypatch.setattr(rs, "ROOT_DIR", repo_root)
    monkeypatch.setattr(rs, "_git_run", _git_run)

    meta = rs.apply_proposed_patch_and_capture_artifacts(
        session_id="session-58",
        session_dir=session_dir,
        impl_result={"proposed_patch": ""},
    )

    patch_path = session_dir / "patches" / "proposed_patch.diff"
    diff_path = session_dir / "patches" / "git_diff_after.diff"
    names_path = session_dir / "patches" / "git_diff_after_name_only.txt"
    assert patch_path.is_file()
    assert meta["patch_artifact"] == str(patch_path)
    assert meta["git_diff_after_artifact"] == str(diff_path)
    assert meta["git_diff_after_name_only_artifact"] == str(names_path)


def test_apply_implementation_result_updates_changed_files_from_git_diff(monkeypatch, tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    session_dir = tmp_path / "session"

    def _git_run(args, check=False):
        if args == ["diff"]:
            return _cp(args, stdout="diff --git a/a.py b/a.py\n")
        if args == ["diff", "--name-only"]:
            return _cp(args, stdout="a.py\nb.py\n")
        raise AssertionError(f"unexpected git args: {args}")

    monkeypatch.setattr(rs, "ROOT_DIR", repo_root)
    monkeypatch.setattr(rs, "_git_run", _git_run)

    rs.apply_proposed_patch_and_capture_artifacts(
        session_id="session-58",
        session_dir=session_dir,
        impl_result={"proposed_patch": ""},
    )

    names = (session_dir / "patches" / "git_diff_after_name_only.txt").read_text(
        encoding="utf-8"
    )
    assert [x for x in names.splitlines() if x] == ["a.py", "b.py"]


def test_apply_implementation_result_fails_when_written_file_missing(monkeypatch, tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    session_dir = tmp_path / "session"
    impl_result = {
        "proposed_patch": (
            "diff --git a/backend/missing.py b/backend/missing.py\n"
            "new file mode 100644\n"
            "--- /dev/null\n"
            "+++ b/backend/missing.py\n"
            "@@\n"
            "+print('missing')\n"
        )
    }

    def _git_run(args, check=False):
        if args[0] == "apply":
            return _cp(args)
        if args == ["diff"]:
            return _cp(args, stdout="")
        if args == ["diff", "--name-only"]:
            return _cp(args, stdout="")
        raise AssertionError(f"unexpected git args: {args}")

    monkeypatch.setattr(rs, "ROOT_DIR", repo_root)
    monkeypatch.setattr(rs, "_git_run", _git_run)

    try:
        rs.apply_proposed_patch_and_capture_artifacts(
            session_id="session-58",
            session_dir=session_dir,
            impl_result=impl_result,
        )
        raise AssertionError("FileNotFoundError が必要です")
    except FileNotFoundError:
        pass


def test_apply_implementation_result_respects_allowed_changes_only(monkeypatch, tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    session_dir = tmp_path / "session"
    impl_result = {
        "proposed_patch": "",
        "changed_files": ["orchestration/run_session.py"],
    }

    def _git_run(args, check=False):
        if args == ["diff"]:
            return _cp(args, stdout="diff --git a/docs/a.md b/docs/a.md\n")
        if args == ["diff", "--name-only"]:
            return _cp(args, stdout="docs/a.md\n")
        raise AssertionError(f"unexpected git args: {args}")

    monkeypatch.setattr(rs, "ROOT_DIR", repo_root)
    monkeypatch.setattr(rs, "_git_run", _git_run)

    rs.apply_proposed_patch_and_capture_artifacts(
        session_id="session-58",
        session_dir=session_dir,
        impl_result=impl_result,
    )

    assert impl_result["changed_files"] == ["orchestration/run_session.py"]
