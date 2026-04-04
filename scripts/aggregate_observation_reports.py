#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""artifacts 配下の report.json（および任意の retry_state.json）を集計し、観測ダッシュボード用 JSON/Markdown を出力する。"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def iter_session_dirs(artifacts_root: Path) -> List[Path]:
    """artifacts 直下のセッション用ディレクトリを名前順で列挙する。"""
    if not artifacts_root.is_dir():
        return []
    out: List[Path] = []
    for child in sorted(artifacts_root.iterdir()):
        if child.is_dir():
            out.append(child)
    return out


def _read_retry_count(session_dir: Path) -> int:
    """responses/retry_state.json があれば retry_count を返す。無ければ 0。"""
    p = session_dir / "responses" / "retry_state.json"
    if not p.is_file():
        return 0
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return 0
        return int(raw.get("retry_count", 0))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return 0


def _load_report_dict(report_path: Path) -> Optional[Dict[str, Any]]:
    try:
        raw = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(raw, dict):
        return None
    return raw


def _normalize_changed_files(report: Dict[str, Any]) -> List[str]:
    cf = report.get("changed_files")
    if not isinstance(cf, list):
        return []
    out: List[str] = []
    for x in cf:
        if isinstance(x, str) and x.strip():
            out.append(x.strip())
    return out


def collect_session_rows(artifacts_root: Path) -> Tuple[int, List[Dict[str, Any]]]:
    """sessions_scanned と、report.json が読めた行だけのリストを返す。"""
    dirs = iter_session_dirs(artifacts_root)
    sessions_scanned = len(dirs)
    rows: List[Dict[str, Any]] = []
    for d in dirs:
        rp = d / "report.json"
        if not rp.is_file():
            continue
        rep = _load_report_dict(rp)
        if rep is None:
            continue
        sid = str(rep.get("session_id") or d.name)
        rows.append(
            {
                "session_id": sid,
                "artifact_dir": d.name,
                "report": rep,
                "retry_count": _read_retry_count(d),
                "changed_files": _normalize_changed_files(rep),
            }
        )
    return sessions_scanned, rows


def compute_dashboard(
    sessions_scanned: int, rows: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """集計結果の本体（中間メトリクス。最終 JSON は build_dashboard_document で整形）。"""
    sessions_with_report = len(rows)
    success_n = sum(1 for r in rows if str(r["report"].get("status")) == "success")
    failed_n = sum(1 for r in rows if str(r["report"].get("status")) == "failed")
    other_status_n = sessions_with_report - success_n - failed_n
    success_rate = (float(success_n) / float(sessions_with_report)) if sessions_with_report else 0.0

    # failure_type 分布は status=failed のセッションのみを母集団とする（success と __success__ は混在させない）
    ft_counts: Counter[str] = Counter()
    for r in rows:
        if str(r["report"].get("status")) != "failed":
            continue
        ft = r["report"].get("failure_type")
        if ft is None or (isinstance(ft, str) and ft.strip() == ""):
            # 失敗だが failure_type 未設定は成功キーに寄せず、件数は failed_count 側と同期できるよう欠損用バケットに分類する
            ft_key = "__missing_failure_type__"
        else:
            ft_key = str(ft)
        ft_counts[ft_key] += 1

    cs_counts: Counter[str] = Counter()
    for r in rows:
        cs = r["report"].get("completion_status")
        key = str(cs) if cs is not None else "__unknown__"
        cs_counts[key] += 1

    empty_changed = sum(1 for r in rows if len(r["changed_files"]) == 0)
    nonempty_changed = sessions_with_report - empty_changed
    per_session_counts = [len(r["changed_files"]) for r in rows]
    total_file_refs = sum(per_session_counts)
    avg_files = (float(total_file_refs) / float(sessions_with_report)) if sessions_with_report else 0.0

    file_hits: Counter[str] = Counter()
    for r in rows:
        for p in r["changed_files"]:
            file_hits[p] += 1
    top_changed_files = [
        {"path": p, "count": c} for p, c in file_hits.most_common(50)
    ]

    retry_values = [int(r["retry_count"]) for r in rows]

    return {
        "sessions_scanned": sessions_scanned,
        "sessions_with_report": sessions_with_report,
        "success_n": success_n,
        "failed_n": failed_n,
        "other_status_n": other_status_n,
        "success_rate": success_rate,
        "failure_type_distribution": dict(
            sorted(ft_counts.items(), key=lambda x: (-x[1], x[0]))
        ),
        "completion_status_distribution": dict(
            sorted(cs_counts.items(), key=lambda x: (-x[1], x[0]))
        ),
        "changed_files_stats": {
            "empty_count": empty_changed,
            "nonempty_count": nonempty_changed,
            "total_changed_file_refs": total_file_refs,
            "avg_files_per_session": round(avg_files, 6),
            "top_changed_files": top_changed_files,
        },
        "retry_stats": _retry_stats(rows, retry_values),
    }


def _retry_stats(rows: List[Dict[str, Any]], retry_values: List[int]) -> Dict[str, Any]:
    if not rows:
        return {
            "sessions_with_retry_state_file": 0,
            "total_retry_count": 0,
            "avg_retry_count": 0.0,
            "max_retry_count": 0,
            "retry_histogram": {},
        }
    with_file = 0
    for r in rows:
        p = r.get("artifact_path_obj")
        if isinstance(p, Path) and (p / "responses" / "retry_state.json").is_file():
            with_file += 1
    hist: Counter[int] = Counter()
    for v in retry_values:
        hist[v] += 1
    total = sum(retry_values)
    avg = float(total) / float(len(retry_values)) if retry_values else 0.0
    mx = max(retry_values) if retry_values else 0
    return {
        "sessions_with_retry_state_file": with_file,
        "total_retry_count": int(total),
        "avg_retry_count": round(avg, 6),
        "max_retry_count": int(mx),
        "retry_histogram": {str(k): int(v) for k, v in sorted(hist.items())},
    }


def attach_paths_for_retry_stats(rows: List[Dict[str, Any]], artifacts_root: Path) -> None:
    """各行に artifact_dir から絶対パスを付与（retry ファイル有無の判定用）。"""
    for r in rows:
        r["artifact_path_obj"] = artifacts_root / str(r["artifact_dir"])


def build_dashboard_document(
    artifacts_root: Path,
) -> Dict[str, Any]:
    sessions_scanned, rows = collect_session_rows(artifacts_root)
    attach_paths_for_retry_stats(rows, artifacts_root)
    body = compute_dashboard(sessions_scanned, rows)
    doc: Dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifacts_root": str(artifacts_root.resolve()),
        "sessions_scanned": body["sessions_scanned"],
        "sessions_with_report": body["sessions_with_report"],
        "success_rate": body["success_rate"],
        "success_count": body["success_n"],
        "failed_count": body["failed_n"],
        "other_status_count": body["other_status_n"],
        "failure_type_distribution": body["failure_type_distribution"],
        "completion_status_distribution": body["completion_status_distribution"],
        "changed_files_stats": body["changed_files_stats"],
        "retry_stats": body["retry_stats"],
        "sessions": [
            {
                "session_id": r["session_id"],
                "artifact_dir": r["artifact_dir"],
                "status": r["report"].get("status"),
                "failure_type": r["report"].get("failure_type"),
                "completion_status": r["report"].get("completion_status"),
                "retry_count": r["retry_count"],
                "changed_files_count": len(r["changed_files"]),
            }
            for r in rows
        ],
    }
    return doc


def render_markdown(doc: Dict[str, Any]) -> str:
    """Markdown ダッシュボード（summary とセッション行を含む）。"""
    lines: List[str] = []
    lines.append("# 観測ダッシュボード（artifacts 集計）")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- generated_at: `{doc.get('generated_at')}`")
    lines.append(f"- artifacts_root: `{doc.get('artifacts_root')}`")
    lines.append(f"- sessions_scanned: {doc.get('sessions_scanned')}")
    lines.append(f"- sessions_with_report: {doc.get('sessions_with_report')}")
    lines.append(f"- success_rate: **{doc.get('success_rate')}**")
    lines.append(f"- success_count: {doc.get('success_count')}")
    lines.append(f"- failed_count: {doc.get('failed_count')}")
    lines.append(
        f"- other_status_count: {doc.get('other_status_count')}"
    )
    lines.append("")
    lines.append("### failure_type_distribution")
    lines.append("")
    lines.append(
        "（`status` が `failed` のセッションのみを集計。成功セッションは含めない。"
        " `failure_type` が未設定の失敗は `__missing_failure_type__` に分類。`__success__` キーは使わない。）"
    )
    lines.append("")
    for k, v in (doc.get("failure_type_distribution") or {}).items():
        lines.append(f"- `{k}`: {v}")
    lines.append("")
    lines.append("### retry_stats")
    lines.append("")
    rs = doc.get("retry_stats") or {}
    for key in (
        "sessions_with_retry_state_file",
        "total_retry_count",
        "avg_retry_count",
        "max_retry_count",
    ):
        lines.append(f"- {key}: {rs.get(key)}")
    lines.append(f"- retry_histogram: `{rs.get('retry_histogram')}`")
    lines.append("")
    lines.append("### changed_files_stats")
    lines.append("")
    cfs = doc.get("changed_files_stats") or {}
    lines.append(f"- empty_count: {cfs.get('empty_count')}")
    lines.append(f"- nonempty_count: {cfs.get('nonempty_count')}")
    lines.append(f"- avg_files_per_session: {cfs.get('avg_files_per_session')}")
    lines.append("")
    lines.append("## Sessions")
    lines.append("")
    lines.append(
        "| session_id | status | failure_type | completion_status | retry_count | changed_files_count |"
    )
    lines.append("| --- | --- | --- | --- | ---: | ---: |")
    for s in doc.get("sessions") or []:
        lines.append(
            "| {sid} | {st} | {ft} | {cs} | {rc} | {cc} |".format(
                sid=s.get("session_id"),
                st=s.get("status"),
                ft=s.get("failure_type"),
                cs=s.get("completion_status"),
                rc=s.get("retry_count"),
                cc=s.get("changed_files_count"),
            )
        )
    lines.append("")
    return "\n".join(lines)


def write_dashboard(
    doc: Dict[str, Any], out_dir: Path, *, json_name: str, md_name: str
) -> Tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    jp = out_dir / json_name
    mp = out_dir / md_name
    jp.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    mp.write_text(render_markdown(doc), encoding="utf-8")
    return jp, mp


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="artifacts の report.json を集計する")
    parser.add_argument(
        "--artifacts",
        type=Path,
        default=None,
        help="artifacts ディレクトリ（既定: リポジトリ直下の artifacts）",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="出力先（既定: docs/pipeline_v0）",
    )
    parser.add_argument(
        "--json-name",
        default="dashboard_latest.json",
        help="JSON ファイル名",
    )
    parser.add_argument(
        "--md-name",
        default="dashboard_latest.md",
        help="Markdown ファイル名",
    )
    args = parser.parse_args(argv)

    root = _repo_root()
    artifacts = (args.artifacts if args.artifacts is not None else root / "artifacts").resolve()
    out_dir = (args.out_dir if args.out_dir is not None else root / "docs" / "pipeline_v0").resolve()

    doc = build_dashboard_document(artifacts)
    write_dashboard(doc, out_dir, json_name=args.json_name, md_name=args.md_name)
    print(f"Wrote: {(out_dir / args.json_name).as_posix()}")
    print(f"Wrote: {(out_dir / args.md_name).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
