"""docs/sessions/session-*.json を全件検査し lint レポートを出力する。"""

import argparse
import glob
import json
import pathlib
import sys
from datetime import datetime, timezone
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lint all docs/sessions/session-*.json files."
    )
    parser.add_argument(
        "--sessions-dir",
        default="docs/sessions",
        help="session JSON ディレクトリ (default: docs/sessions)",
    )
    parser.add_argument(
        "--output",
        default="artifacts/session-159c/json_lint_report.json",
        help="レポート出力パス (default: artifacts/session-159c/json_lint_report.json)",
    )
    return parser.parse_args()


def lint_files(sessions_dir: str) -> tuple[int, int, list[dict[str, Any]]]:
    """全 session JSON を検査する。(total, fail_count, fail_details) を返す。"""
    pattern = str(pathlib.Path(sessions_dir) / "session-*.json")
    paths = sorted(glob.glob(pattern))

    fail_details: list[dict[str, Any]] = []

    for path in paths:
        try:
            with open(path, encoding="utf-8") as f:
                json.load(f)
        except json.JSONDecodeError as e:
            fail_details.append(
                {
                    "path": path,
                    "error_message": str(e),
                    "line": e.lineno,
                    "col": e.colno,
                }
            )
        except OSError as e:
            fail_details.append(
                {
                    "path": path,
                    "error_message": f"OSError: {e}",
                    "line": None,
                    "col": None,
                }
            )

    total = len(paths)
    fail_count = len(fail_details)
    return total, fail_count, fail_details


def write_report(
    output_path: str,
    total: int,
    fail_count: int,
    fail_details: list[dict[str, Any]],
    repaired_with_note: list[str],
) -> None:
    """レポートを JSON ファイルに書き出す。"""
    out = pathlib.Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "total": total,
        "pass_count": total - fail_count,
        "fail_count": fail_count,
        "fail_details": fail_details,
        "repaired_with_note": repaired_with_note,
    }

    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


def main() -> int:
    args = parse_args()
    total, fail_count, fail_details = lint_files(args.sessions_dir)

    repaired_with_note: list[str] = [
        "session-120.json: out_of_scope は空配列 [] で暫定復旧。"
        "有効な git 履歴ソースが存在しないため意味的内容の復元は不可。"
        "後続 BACKLOG-S120-OUT-OF-SCOPE-RESTORE で正本化を候補化。",
        "session-120.json: completion_criteria CC-M01-02/03 が 1 行に混在する構文破損を最小分割修復 (案 B-1)。"
        "CC-M01-02 の condition 末尾は欠落のため残存文字列のみ保持。"
        "後続 BACKLOG-S120-003-COMPLETION-CRITERIA-RESTORE で正本化を候補化。",
    ]

    write_report(args.output, total, fail_count, fail_details, repaired_with_note)

    print(f"checked_at : {datetime.now(timezone.utc).isoformat()}")
    print(f"total      : {total}")
    print(f"pass_count : {total - fail_count}")
    print(f"fail_count : {fail_count}")
    if fail_details:
        print("fail_details:")
        for d in fail_details:
            print(f"  {d['path']} (line={d['line']}, col={d['col']}): {d['error_message']}")
    print(f"report     : {args.output}")

    return 1 if fail_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
