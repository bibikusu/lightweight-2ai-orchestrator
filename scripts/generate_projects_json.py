#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_projects_json.py

docs/config/project_registry.json を正本として、
A03_mane_bikusu 用 data/projects.json を生成する手動実行スクリプト。

使い方:
  # dry-run（ファイルは書き込まない）
  python3 scripts/generate_projects_json.py

  # 実際に書き込む（backup を自動作成してから上書き）
  python3 scripts/generate_projects_json.py --force

session: session-a03-id-migration-generator-001
"""

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

# --- パス定数 ---
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
REGISTRY_PATH = REPO_ROOT / "docs/config/project_registry.json"
OUTPUT_PATH = Path(
    "/Users/kunihideyamane/AI_Team/projects/A03_mane_bikusu/public/data/projects.json"
)
BACKUP_SUFFIX = "session-a03-id-migration-generator-001"

# --- プレースホルダ値（session 定義で確定済み、変更禁止） ---
PLACEHOLDER = {
    "status": "planned",
    "priority": 3,
    "next_action": "未設定（別sessionで確定）",
    "current_phase": "未設定（別sessionで確定）",
}


def load_registry() -> list:
    """project_registry.json を読み込み、d['projects'] を返す。"""
    d = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return d["projects"]


def generate_entries(registry_projects: list) -> list:
    """registry エントリから projects.json 用エントリを生成する。"""
    entries = []
    for p in registry_projects:
        entry = {
            "id": p["project_id"],
            "name": p["name"],
            "status": PLACEHOLDER["status"],
            "priority": PLACEHOLDER["priority"],
            "next_action": PLACEHOLDER["next_action"],
            "current_phase": PLACEHOLDER["current_phase"],
        }
        entries.append(entry)
    return entries


def create_backup(output_path: Path) -> Path:
    """既存ファイルを backup する。命名規則: *.bak.YYYYMMDD-<BACKUP_SUFFIX>"""
    date_str = datetime.now().strftime("%Y%m%d")
    backup_path = output_path.parent / f"projects.json.bak.{date_str}-{BACKUP_SUFFIX}"
    shutil.copy2(output_path, backup_path)
    print(f"[backup] {backup_path}")
    return backup_path


def main():
    parser = argparse.ArgumentParser(
        description=(
            "docs/config/project_registry.json を正本として "
            "A03_mane_bikusu 用 data/projects.json を生成します。\n"
            "デフォルトは dry-run です。--force を付けると実際に書き込みます。"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="実際にファイルを書き込む（省略時は dry-run）",
    )
    parser.add_argument(
        "--output",
        default=str(OUTPUT_PATH),
        help=f"出力先パス（デフォルト: {OUTPUT_PATH}）",
    )
    args = parser.parse_args()

    output_path = Path(args.output)

    # registry を読み込んでエントリを生成
    registry_projects = load_registry()
    entries = generate_entries(registry_projects)

    # 生成内容をプレビュー表示
    print(f"[info] registry: {len(registry_projects)} projects")
    print(f"[info] output  : {output_path}")
    print("[info] entries:")
    for e in entries:
        print(f"  {e['id']:40s} {e['name']}")

    if not args.force:
        print()
        print("[dry-run] ファイルは書き込まれていません。")
        print("[dry-run] --force を付けて実行すると上書きします。")
        return

    # 出力先ファイルが存在する場合は backup を作成
    if output_path.exists():
        create_backup(output_path)
    else:
        print(f"[warn] {output_path} が存在しないため backup をスキップします。")

    # JSON を書き込む
    output_path.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[write] {output_path} ({len(entries)} entries)")


if __name__ == "__main__":
    main()
