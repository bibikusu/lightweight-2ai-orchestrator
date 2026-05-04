"""auto_runner: selector → queue → run_session の最小ループ実装。

session-171c 仕様正本に基づく MVP 実装。
run_session 実呼び出しは session-171e+ で接続予定。
"""
import json
import subprocess
from typing import Any, Dict, List


def run_auto_runner(
    max_iterations: int,
    dry_run: bool,
    selector_command: List[str],
    queue_config_path: str,
) -> Dict[str, Any]:
    """auto_runner のメインループ。

    Args:
        max_iterations: ループ上限 (1 以上の int)
        dry_run: True の場合 run_session を呼ばず 1 iteration で停止
        selector_command: selector を起動する subprocess コマンドリスト
        queue_config_path: queue 設定ファイルパス (将来の queue 接続用、本実装では参照しない)

    Returns:
        {"iterations": list[dict], "stopped_reason": str}
        stopped_reason は "max_iterations_reached" / "no_candidate" /
        "blocked_human" / "failed" / "dry_run_completed" のいずれか
    """
    if not isinstance(max_iterations, int) or max_iterations < 1:
        raise ValueError(f"max_iterations は 1 以上の int でなければなりません: {max_iterations!r}")

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

        iteration_record: Dict[str, Any] = {
            "iteration_index": i,
            "selected_session_id": selected_session_id,
            "queue_state": "ready",
        }
        iterations.append(iteration_record)

        if dry_run:
            return {"iterations": iterations, "stopped_reason": "dry_run_completed"}

    return {"iterations": iterations, "stopped_reason": "max_iterations_reached"}
