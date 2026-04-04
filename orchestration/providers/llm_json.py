# -*- coding: utf-8 -*-
"""LLM 応答から JSON オブジェクトを取り出す。"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional


def _strip_markdown_fence(text: str) -> str:
    """``` / ```json フェンスがあれば内側の本文を返す。

    終端フェンスが無い場合は開始フェンス以降を取り、末尾の ``` があれば除去する。
    """
    s = text.strip()
    m = re.search(r"```(?:json)?\s*\r?\n(.*?)\r?\n```", s, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    m_open = re.search(r"```(?:json)?\s*", s)
    if m_open:
        rest = s[m_open.end() :].strip()
        if rest.endswith("```"):
            rest = rest[: -3].strip()
        return rest
    return s


def _extract_balanced_object(raw: str) -> Optional[str]:
    """先頭の { に対応する外側の } までを返す（ダブルクォート文字列内の括弧は無視）。"""
    start = raw.find("{")
    if start < 0:
        return None
    depth = 0
    in_str = False
    esc = False
    n = len(raw)
    i = start
    while i < n:
        ch = raw[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return raw[start : i + 1]
        i += 1
    return None


def _candidate_strings(text: str) -> List[str]:
    """json 解釈に渡す候補文字列（重複除去）。"""
    stripped = text.strip()
    fenced = _strip_markdown_fence(stripped)
    out: List[str] = []
    seen: set[str] = set()

    def add(s: str) -> None:
        s = s.strip()
        if not s or s in seen:
            return
        seen.add(s)
        out.append(s)

    add(stripped)
    if fenced != stripped:
        add(fenced)
    for base in (fenced, stripped):
        bal = _extract_balanced_object(base)
        if bal:
            add(bal)
    return out


def _repair_loads(candidate: str) -> Any:
    """json.loads が通らないときの修復パース（LLM 由来の壊れ JSON 向け）。"""
    try:
        import json_repair
    except ImportError as e:
        raise RuntimeError(
            "LLM 出力の JSON 修復には json-repair パッケージが必要です。"
            " pip install -r requirements.txt または pip install json-repair を実行してください。"
        ) from e
    return json_repair.loads(candidate)


def parse_json_object(text: str) -> Dict[str, Any]:
    """モデル出力を JSON オブジェクトとして解釈する。

    JSON の前に説明文が付いている場合（リトライ時など）や markdown フェンスにも対応する。
    厳密な json.loads が失敗したときは json_repair で修復を試みる（diff 内の改行混入・未閉じ
    文字列・途中打ち切りなど LLM 由来の壊れ方）。
    """
    if not text or not text.strip():
        raise ValueError("空のテキストは JSON として解釈できません。")

    last_err: Optional[BaseException] = None
    for cand in _candidate_strings(text):
        try:
            try:
                obj: Any = json.loads(cand)
            except json.JSONDecodeError:
                obj = _repair_loads(cand)
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            last_err = e
            continue
        except Exception as e:
            # json_repair が想定外の例外を返す場合も次候補へ
            last_err = e
            continue
        if not isinstance(obj, dict):
            last_err = TypeError(
                "JSON のトップレベルがオブジェクトではありません: "
                f"{type(obj).__name__}"
            )
            continue
        return obj

    if last_err is not None:
        raise last_err
    raise ValueError("JSON 候補が得られませんでした。")
