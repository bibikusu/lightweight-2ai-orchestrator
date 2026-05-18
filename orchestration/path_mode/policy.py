"""Fast / Formal / Emergency 各 path の policy 定義。"""
from typing import Dict, Any

from orchestration.path_mode.constants import (
    PATH_MODE_FAST,
    PATH_MODE_FORMAL,
    PATH_MODE_EMERGENCY,
)


POLICY: Dict[str, Dict[str, Any]] = {
    PATH_MODE_FAST: {
        "description": "docs-only / 1ファイル / scope狭 / forbidden_changes 強",
        "requires_4gate": False,
        "requires_commander_notify": False,
        "typical_use": [
            "docs-only セッション",
            "JSON/YAML 単一ファイル修復",
            "明確な lint 修正",
        ],
    },
    PATH_MODE_FORMAL: {
        "description": "実装変更あり / 複数ファイル / テスト必要 / 4-gate実行",
        "requires_4gate": True,
        "requires_commander_notify": False,
        "typical_use": [
            "新規モジュール実装",
            "複数ファイル変更",
            "テストコード追加",
            "既存実装の修正",
        ],
    },
    PATH_MODE_EMERGENCY: {
        "description": "production直結 / hotfix / 司令塔即時通知",
        "requires_4gate": True,
        "requires_commander_notify": True,
        "typical_use": [
            "本番障害対応",
            "hotfix",
            "critical バグ修正",
        ],
    },
}


def get_policy(path_mode: str) -> Dict[str, Any]:
    """指定 path_mode の policy を返す。未知の path_mode は ValueError。"""
    if path_mode not in POLICY:
        raise ValueError(f"unknown path_mode: {path_mode!r}")
    return POLICY[path_mode]
