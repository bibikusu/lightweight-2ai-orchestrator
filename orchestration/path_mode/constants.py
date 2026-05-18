"""path_mode 判定で使用する定数・閾値定義。"""
from typing import Final, Literal

# --- PathMode 文字列定数 ---
PATH_MODE_FAST: Final[Literal["fast"]] = "fast"
PATH_MODE_FORMAL: Final[Literal["formal"]] = "formal"
PATH_MODE_EMERGENCY: Final[Literal["emergency"]] = "emergency"

VALID_PATH_MODES: Final[tuple] = (PATH_MODE_FAST, PATH_MODE_FORMAL, PATH_MODE_EMERGENCY)

# --- 14キー必須キー ---
REQUIRED_SESSION_KEYS: Final[tuple] = (
    "session_id",
    "phase_id",
    "title",
    "goal",
    "scope",
    "out_of_scope",
    "constraints",
    "acceptance_ref",
    "allowed_changes_detail",
    "forbidden_changes",
    "completion_criteria",
    "acceptance_criteria",
    "review_points",
    "failure_type",
)

# --- Emergency 判定キーワード ---
EMERGENCY_SCOPE_KEYWORDS: Final[tuple] = (
    "production",
    "hotfix",
    "critical",
    "emergency",
    "本番",
    "緊急",
)

EMERGENCY_TITLE_KEYWORDS: Final[tuple] = (
    "hotfix",
    "emergency",
    "critical",
    "urgent",
    "緊急",
)

# --- Fast Path 判定キーワード ---
FAST_SCOPE_KEYWORDS: Final[tuple] = (
    "docs-only",
    "docs only",
    "ドキュメントのみ",
)

# 1ファイルとみなす allowed_changes_detail の最大エントリ数
FAST_MAX_ALLOWED_FILES: Final[int] = 1
