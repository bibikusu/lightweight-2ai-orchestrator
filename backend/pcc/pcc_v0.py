from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

_MODULE_DIR = Path(__file__).parent
_REPO_ROOT = _MODULE_DIR.parent.parent

_DEFAULT_REGISTRY_PATH = _REPO_ROOT / "docs" / "config" / "project_registry.json"
_DEFAULT_PROJECTS_DIR = _REPO_ROOT / "docs" / "projects"
_DEFAULT_QUEUE_STATE_PATH = _REPO_ROOT / "docs" / "config" / "queue_state.json"

_GIT_STATUS_VALUES = {"clean", "dirty", "unmanaged", "detached", "unknown"}


def _get_git_info(repo_path: str) -> tuple:
    """repo_path の git 状態を調べ (git_status, branch, head) を返す。"""
    path = Path(repo_path)
    if not path.is_dir() or not (path / ".git").exists():
        return "unmanaged", "—", "—"
    try:
        sym_result = subprocess.run(
            ["git", "symbolic-ref", "--short", "HEAD"],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=5,
        )
        head_result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=5,
        )
        head = head_result.stdout.strip() if head_result.returncode == 0 else "—"

        if sym_result.returncode != 0:
            return "detached", "(detached)", head

        branch = sym_result.stdout.strip()

        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if status_result.returncode != 0:
            return "unknown", branch, head

        git_status = "dirty" if status_result.stdout.strip() else "clean"
        return git_status, branch, head
    except Exception:
        return "unknown", "—", "—"


def aggregate_projects(
    registry_path: Optional[Path] = None,
    projects_dir: Optional[Path] = None,
    queue_state_path: Optional[Path] = None,
) -> List[Dict]:
    """10プロジェクトの状態を集約して返す。読み取り専用。書込は一切しない。"""
    reg_path = registry_path if registry_path is not None else _DEFAULT_REGISTRY_PATH
    proj_dir = projects_dir if projects_dir is not None else _DEFAULT_PROJECTS_DIR
    q_path = queue_state_path if queue_state_path is not None else _DEFAULT_QUEUE_STATE_PATH

    registry: Dict = json.loads(reg_path.read_text(encoding="utf-8"))
    projects = registry.get("projects", [])

    queue_summary: str = "not_configured"
    if q_path.exists():
        try:
            q_data: Dict = json.loads(q_path.read_text(encoding="utf-8"))
            queue_summary = q_data.get("summary", "—")
        except Exception:
            queue_summary = "not_configured"

    result: List[Dict] = []
    for proj in projects:
        project_id: str = proj.get("project_id", "—")
        repo_path: str = proj.get("repo_path", "—")

        state: Dict = {}
        state_path = proj_dir / project_id / "state.json"
        if state_path.exists():
            try:
                state = json.loads(state_path.read_text(encoding="utf-8"))
            except Exception:
                state = {}

        git_status, branch, head = _get_git_info(repo_path)

        card: Dict = {
            "project_id": project_id,
            "repo_path": repo_path,
            "branch": branch,
            "HEAD": head,
            "git_status": git_status,
            "latest_session": state.get("last_session", state.get("latest_session", "—")),
            "four_gate": state.get("four_gate", "—"),
            "failure_type": state.get("failure_type", state.get("blockers", "—")),
            "human_gate": state.get("human_gate", "—"),
            "artifacts": state.get("artifacts", "—"),
            "queue_summary": queue_summary,
        }
        result.append(card)

    return result
