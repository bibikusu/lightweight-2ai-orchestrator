# -*- coding: utf-8 -*-
"""report JSON 読み込み・必須キー検証のテスト用ヘルパー（session-33）。"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest


def repo_root() -> Path:
    """このファイルからリポジトリルート（backend の親）を返す。"""
    return Path(__file__).resolve().parents[2]


def load_json_object(
    path: Path,
    *,
    missing_file_message: str | None = None,
    root_not_dict_message: str | None = None,
) -> dict[str, Any]:
    """JSON ファイルを読み込み、ルートが object であることを検証する。"""
    if not path.is_file():
        msg = missing_file_message or f"レポートが見つかりません: {path}"
        pytest.fail(msg)
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        msg = root_not_dict_message or f"{path.name} のルートは JSON object である必要があります"
        pytest.fail(msg)
    return raw


def load_report_json(
    relative_path: str | Path,
    *,
    missing_file_message: str | None = None,
    root_not_dict_message: str | None = None,
) -> dict[str, Any]:
    """リポジトリルートからの相対パスでレポート JSON を読み込む。"""
    path = repo_root() / Path(relative_path)
    return load_json_object(
        path,
        missing_file_message=missing_file_message,
        root_not_dict_message=root_not_dict_message,
    )


def assert_required_keys(
    data: Mapping[str, Any],
    required: frozenset[str],
    *,
    label: str | None = None,
) -> None:
    """必須キーがすべて存在することを検証する（不足時は従来どおりの文言）。"""
    missing = required - data.keys()
    if label is None:
        assert not missing, f"不足キー: {sorted(missing)}"
    else:
        assert not missing, f"{label} の不足キー: {sorted(missing)}"
