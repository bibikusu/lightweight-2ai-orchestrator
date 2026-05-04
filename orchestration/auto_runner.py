"""auto_runner: selector → queue → run_session の最小ループ実装。

session-171c 仕様正本に基づく MVP 実装。
run_session.py との接続は subprocess 境界のみ（内部関数 import 禁止）。
"""
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

_DEFAULT_LOG_DIR = Path("artifacts/session-171e/logs")


def _call_run_session(
    session_id: str,
    project: Optional[str] = None,
    dry_run: bool = False,
    execution_mode: Optional[str] = None,
    log_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """run_session.py を subprocess 境界で呼び出す。

    run_session.py の内部関数 import は禁止。subprocess 経由のみ接続する。
    returncode == 0 を success、それ以外を failed として返す。
    stdout/stderr は log_dir が指定された場合のみ保存する。
    """
    cmd: List[str] = [
        ".venv/bin/python",
        "orchestration/run_session.py",
        "--session-id",
        session_id,
    ]
    if project is not None:
        cmd += ["--project", project]
    if dry_run:
        cmd.append("--dry-run")
    if execution_mode is not None:
        cmd += ["--execution-mode", execution_mode]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / f"{session_id}_stdout.txt").write_text(str(result.stdout or ""))
        (log_dir / f"{session_id}_stderr.txt").write_text(str(result.stderr or ""))

    return {
        "returncode": result.returncode,
        "status": "success" if result.returncode == 0 else "failed",
    }


def run_auto_runner(
    max_iterations: int,
    dry_run: bool,
    selector_command: List[str],
    queue_config_path: str,
    project: Optional[str] = None,
    execution_mode: Optional[str] = None,
    log_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """auto_runner のメインループ。

    Args:
        max_iterations: ループ上限 (1 以上の int)
        dry_run: True の場合 run_session を呼ばず 1 iteration で停止
        selector_command: selector を起動する subprocess コマンドリスト
        queue_config_path: queue 設定ファイルパス (将来の queue 接続用、本実装では参照しない)
        project: run_session に渡す --project 引数 (optional)
        execution_mode: run_session に渡す --execution-mode 引数 (optional)
        log_dir: run_session の stdout/stderr 保存先 (None の場合デフォルトパスを使用)

    Returns:
        {"iterations": list[dict], "stopped_reason": str}
        stopped_reason は "max_iterations_reached" / "no_candidate" /
        "blocked_human" / "failed" / "dry_run_completed" のいずれか
    """
    if not isinstance(max_iterations, int) or max_iterations < 1:
        raise ValueError(f"max_iterations は 1 以上の int でなければなりません: {max_iterations!r}")

    _log_dir: Path = log_dir if log_dir is not None else _DEFAULT_LOG_DIR
    iterations: List[Dict[str, Any]] = []

    for i in range(max_iterations):
        result = subprocess.run(
            selector_command,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return {"iterations": iterations, "stopped_reason": "failed"}

        try:
            parsed = json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"iterations": iterations, "stopped_reason": "failed"}

        selected_session_id = parsed.get("selected_session_id") or None
        if not selected_session_id:
            return {"iterations": iterations, "stopped_reason": "no_candidate"}

        if dry_run:
            iterations.append({
                "iteration_index": i,
                "selected_session_id": selected_session_id,
                "queue_state": "ready",
            })
            return {"iterations": iterations, "stopped_reason": "dry_run_completed"}

        rs_result = _call_run_session(
            session_id=selected_session_id,
            project=project,
            dry_run=False,
            execution_mode=execution_mode,
            log_dir=_log_dir,
        )

        iterations.append({
            "iteration_index": i,
            "selected_session_id": selected_session_id,
            "queue_state": "completed" if rs_result["status"] == "success" else "failed",
            "run_session_returncode": rs_result["returncode"],
        })

        if rs_result["status"] == "failed":
            return {"iterations": iterations, "stopped_reason": "failed"}

    return {"iterations": iterations, "stopped_reason": "max_iterations_reached"}
