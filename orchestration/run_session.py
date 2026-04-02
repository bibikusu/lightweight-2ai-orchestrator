#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml

logger = logging.getLogger(__name__)

# providers は通常実行時のみ遅延インポート（dry-run では不要）


ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT_DIR / "docs"
ARTIFACTS_DIR = ROOT_DIR / "artifacts"
CONFIG_PATH = ROOT_DIR / "orchestration" / "config.yaml"

MASTER_INSTRUCTION_PATH = DOCS_DIR / "master_instruction.md"
GLOBAL_RULES_PATH = DOCS_DIR / "global_rules.md"
ROADMAP_PATH = DOCS_DIR / "roadmap.yaml"
SESSIONS_DIR = DOCS_DIR / "sessions"

# Git 保護で拒否するブランチ名（小文字比較）
FORBIDDEN_BRANCHES = frozenset({"main", "master"})


def _ensure_repo_root_on_sys_path() -> None:
    """
    互換レイヤー: 実行時のみ ROOT_DIR を sys.path に追加する。
    import 時に副作用を持たせないため、main の冒頭でのみ呼ぶ。
    """
    root = str(ROOT_DIR)
    if root not in sys.path:
        sys.path.insert(0, root)


@dataclass
class SessionContext:
    session_id: str
    session_data: Dict[str, Any]
    acceptance_data: Dict[str, Any]
    master_instruction: str
    global_rules: str
    roadmap_text: str
    runtime_config: Dict[str, Any]


def load_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


def load_yaml_as_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {path}")
    return path.read_text(encoding="utf-8")


def load_runtime_config() -> Dict[str, Any]:
    return load_yaml(CONFIG_PATH)


def load_session_context(session_id: str) -> SessionContext:
    runtime_config = load_runtime_config()

    session_path = SESSIONS_DIR / f"{session_id}.json"
    session_data = load_json(session_path)

    acceptance_ref = session_data.get("acceptance_ref")
    if not acceptance_ref:
        raise ValueError("session JSON must contain 'acceptance_ref'")

    acceptance_ref_str = str(acceptance_ref).strip()

    # docs/ 始まりはプロジェクトルート基準、それ以外は docs/ 配下基準
    if acceptance_ref_str.startswith("docs/"):
        acceptance_path = ROOT_DIR / acceptance_ref_str
    else:
        acceptance_path = DOCS_DIR / acceptance_ref_str

    acceptance_text = load_yaml_as_text(acceptance_path)
    acceptance_data = {
        "raw_yaml": acceptance_text,
        "parsed": load_yaml(acceptance_path),
    }

    return SessionContext(
        session_id=session_id,
        session_data=session_data,
        acceptance_data=acceptance_data,
        master_instruction=load_text(MASTER_INSTRUCTION_PATH),
        global_rules=load_text(GLOBAL_RULES_PATH),
        roadmap_text=load_text(ROADMAP_PATH),
        runtime_config=runtime_config,
    )


def validate_session_required_keys(session_data: dict) -> None:
    """session.json の必須キー存在チェック。欠落時は ValueError。"""
    required = ["session_id", "phase_id", "title", "goal", "scope",
                "out_of_scope", "constraints", "acceptance_ref"]
    for key in required:
        if key not in session_data:
            raise ValueError(f"session JSON missing required key: {key}")


def resolve_acceptance_path(acceptance_ref: str, root_dir: Path, docs_dir: Path) -> Path:
    """acceptance_ref を実パスに解決する。docs/ 始まりはプロジェクトルート基準。"""
    ref = str(acceptance_ref).strip()
    if ref.startswith("docs/"):
        return root_dir / ref
    return docs_dir / ref


def validate_session_id_consistency(session_data: dict, acceptance_data: dict) -> None:
    """session.json と acceptance.yaml の session_id 一致を検証する。"""
    s_id = session_data.get("session_id", "")
    a_id = acceptance_data.get("session_id", "")
    if s_id != a_id:
        raise ValueError(
            f"session_id mismatch: session.json={s_id!r}, acceptance.yaml={a_id!r}"
        )


def run_preflight_validation(session_data: dict, acceptance_parsed: dict,
                              acceptance_ref: str, root_dir: Path, docs_dir: Path) -> None:
    """preflight: 必須キー + パス解決 + session_id 一致を一括検証。"""
    validate_session_required_keys(session_data)
    path = resolve_acceptance_path(acceptance_ref, root_dir, docs_dir)
    if not path.exists():
        raise FileNotFoundError(f"acceptance file not found: {path}")
    validate_session_id_consistency(session_data, acceptance_parsed)


def validate_session_context(ctx: SessionContext) -> None:
    required_keys = [
        "session_id",
        "phase_id",
        "title",
        "goal",
        "scope",
        "out_of_scope",
        "constraints",
        "acceptance_ref",
    ]
    for key in required_keys:
        if key not in ctx.session_data:
            raise ValueError(f"session JSON missing required key: {key}")

    if ctx.session_data["session_id"] != ctx.session_id:
        raise ValueError("session_id mismatch between filename and JSON body")

    if not ctx.session_data["goal"]:
        raise ValueError("goal must not be empty")

    if not isinstance(ctx.session_data["scope"], list):
        raise ValueError("scope must be a list")

    if not isinstance(ctx.session_data["out_of_scope"], list):
        raise ValueError("out_of_scope must be a list")


def ensure_artifact_dirs(session_id: str) -> Path:
    session_dir = ARTIFACTS_DIR / session_id
    for sub in ["prompts", "responses", "patches", "test_results", "logs", "reports"]:
        (session_dir / sub).mkdir(parents=True, exist_ok=True)
    return session_dir


def save_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def save_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _utc_timestamp_compact() -> str:
    """ログファイル名用 UTC タイムスタンプ（例: 20260322T051030Z）。"""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _iso_utc_now() -> str:
    """report.json 用の ISO8601 UTC タイムスタンプ。"""
    return datetime.now(timezone.utc).isoformat()


def _duration_sec_from_iso(started_at: str, finished_at: str) -> float:
    """started_at / finished_at（ISO8601）から経過秒を返す。解析不能時は 0.0。"""
    try:
        s = started_at.replace("Z", "+00:00")
        f = finished_at.replace("Z", "+00:00")
        t0 = datetime.fromisoformat(s)
        t1 = datetime.fromisoformat(f)
        return max(0.0, (t1 - t0).total_seconds())
    except Exception:
        return 0.0


def _git_branch_safe() -> Optional[str]:
    """ブランチ名を返す。Git でない／取得失敗時は None。"""
    if not _is_git_repository():
        return None
    try:
        return get_current_git_branch()
    except Exception:
        return None


def _git_commit_sha_safe() -> Optional[str]:
    """HEAD のコミット SHA を返す。Git でない／取得失敗時は None。"""
    if not _is_git_repository():
        return None
    try:
        p = _git_run(["rev-parse", "HEAD"])
        if p.returncode != 0:
            return None
        out = (p.stdout or "").strip()
        return out if out else None
    except Exception:
        return None


def save_error_log(
    session_dir: Path,
    stage: str,
    error: Union[BaseException, str],
    session_id: str,
    *,
    branch: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    失敗時に error 系ログを保存する。
    - error.json / error_latest.json: 同一内容（後方互換と最新固定）
    - error_<UTC>.json: タイムスタンプ付きコピー
    """
    if isinstance(error, BaseException):
        error_type = type(error).__name__
        message = str(error)
    else:
        error_type = "Error"
        message = str(error)
    resolved_branch = branch if branch is not None else _git_branch_safe()
    ts = _utc_timestamp_compact()
    payload: Dict[str, Any] = {
        "stage": stage,
        "error_type": error_type,
        "message": message,
        "session_id": session_id,
        "branch": resolved_branch,
        "timestamp_utc": ts,
    }
    if details:
        payload["details"] = details

    logs_dir = session_dir / "logs"
    save_json(logs_dir / "error.json", payload)
    save_json(logs_dir / "error_latest.json", payload)
    save_json(logs_dir / f"error_{ts}.json", payload)


def record_dry_run_git_warnings(session_dir: Path, session_id: str) -> None:
    """
    dry-run 専用: main/master 上でも実行は許可する。
    dirty worktree のときは警告ログのみ残し、処理は継続する。
    """
    if not _is_git_repository():
        return
    try:
        branch = get_current_git_branch()
    except Exception as e:
        warn = {
            "level": "warning",
            "reason": "git_branch_unavailable",
            "session_id": session_id,
            "branch": None,
            "message": str(e),
            "timestamp_utc": _utc_timestamp_compact(),
        }
        save_json(session_dir / "logs" / "dry_run_git_warning.json", warn)
        return

    if not is_git_worktree_dirty():
        return

    warn = {
        "level": "warning",
        "reason": "dirty_worktree",
        "session_id": session_id,
        "branch": branch,
        "message": (
            "dry-run のため続行しますが、作業ツリーに未コミットの変更があります。"
            "通常実行前にクリーンな状態を推奨します。"
        ),
        "timestamp_utc": _utc_timestamp_compact(),
    }
    save_json(session_dir / "logs" / "dry_run_git_warning.json", warn)
    print(
        f"[WARN] dry-run: dirty worktree（branch={branch!r}）。"
        f"詳細: {session_dir / 'logs' / 'dry_run_git_warning.json'}",
        file=sys.stderr,
    )


def log_stage_progress(session_id: str, stage: str, detail: str = "") -> None:
    """通常実行時、次の検証ステージが追えるよう標準出力に整理ログを出す。"""
    br = _git_branch_safe()
    suffix = f" | {detail}" if detail else ""
    print(
        f"[INFO] stage={stage} session_id={session_id} branch={br!r}{suffix}",
        flush=True,
    )


def _git_run(args: List[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
    """Git サブプロセス（shell 不使用）。"""
    return subprocess.run(
        ["git", *args],
        cwd=ROOT_DIR,
        text=True,
        capture_output=True,
        check=check,
    )


def _extract_proposed_patch_text(impl_result: Dict[str, Any]) -> str:
    """
    Claude の implementation_result から proposed_patch を文字列として抽出する。
    想定外型は空文字へフォールバック（後段で「適用なし」扱い）。
    """
    raw = impl_result.get("proposed_patch")
    if raw is None:
        return ""
    if isinstance(raw, str):
        return raw
    # 互換: 配列や辞書で返ってきた場合も落ちずに記録できるようにする
    try:
        return json.dumps(raw, ensure_ascii=False, indent=2)
    except Exception:
        return str(raw)


def normalize_patch_for_git_apply(raw_patch: str) -> str:
    """
    git apply 前に patch 文字列を正規化する。
    - ```diff / ```patch フェンスを除去
    - CRLF/CR を LF に統一
    - ---/+++ があるのに diff --git が無い塊へヘッダ補完
    - 重複した diff --git ヘッダー（偽 index 行付き）を除去
    - 末尾改行を保証
    """
    text = str(raw_patch or "")
    fenced = re.search(r"```(?:diff|patch)?\s*(.*?)```", text, flags=re.DOTALL)
    if fenced:
        text = fenced.group(1)
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip("\n")
    if not text:
        return ""

    lines = text.split("\n")

    # 重複 diff --git ヘッダーを除去:
    # "diff --git A" の直後に index 行があり、さらに "diff --git A" が続く場合、
    # 最初の diff --git と index 行を捨てて後者を残す。
    cleaned: List[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if (
            line.startswith("diff --git ")
            and i + 1 < len(lines)
            and re.match(r"^index [0-9a-f]+\.\.[0-9a-f]+ ", lines[i + 1])
            and i + 2 < len(lines)
            and lines[i + 2].startswith("diff --git ")
        ):
            # 偽 index 付き重複ヘッダー: 最初の diff --git と index を捨てる
            i += 2
            continue
        cleaned.append(line)
        i += 1
    lines = cleaned

    out: List[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("--- ") and i + 1 < len(lines) and lines[i + 1].startswith("+++ "):
            old_file = line.split(maxsplit=1)[1].strip()
            new_file = lines[i + 1].split(maxsplit=1)[1].strip()
            if not out or not out[-1].startswith("diff --git "):
                old_git = old_file if old_file.startswith(("a/", "b/", "/dev/null")) else f"a/{old_file}"
                new_git = new_file if new_file.startswith(("a/", "b/", "/dev/null")) else f"b/{new_file}"
                out.append(f"diff --git {old_git} {new_git}")
            out.append(line)
            out.append(lines[i + 1])
            i += 2
            continue
        out.append(line)
        i += 1
    return "\n".join(out).strip() + "\n"


def _expected_existing_files_from_patch(patch_text: str) -> List[str]:
    """
    proposed_patch（unified diff 想定）から「適用後に存在すべきファイル」を推定する。
    - 追加/変更: +++ b/<path> を採用
    - 削除: +++ /dev/null は除外（存在チェック対象外）
    """
    out: List[str] = []
    for line in (patch_text or "").splitlines():
        if not line.startswith("+++ "):
            continue
        rhs = line[4:].strip()
        if rhs == "/dev/null":
            continue
        if rhs.startswith("b/"):
            rhs = rhs[2:]
        rhs = normalize_changed_file_path(rhs)
        if rhs and rhs not in out:
            out.append(rhs)
    return out


def _apply_proposed_patch_and_capture_artifacts_with_artifacts(
    *,
    session_id: str,
    session_dir: Path,
    impl_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    implementation_result.proposed_patch を実ファイルへ適用し、artifact を保存する。
    返り値は impl_result へ追記可能なメタ情報（diff_summary 等）を返す。
    """
    patch_text = normalize_patch_for_git_apply(_extract_proposed_patch_text(impl_result))
    patches_dir = session_dir / "patches"
    patch_path = patches_dir / "proposed_patch.diff"
    save_text(patch_path, patch_text)

    def _artifact_path_str(path: Path) -> str:
        try:
            return str(path.relative_to(ROOT_DIR))
        except ValueError:
            return str(path)

    meta: Dict[str, Any] = {
        "patch_artifact": _artifact_path_str(patch_path),
        "patch_applied": False,
        "git_apply_returncode": None,
        "git_apply_stderr": "",
    }

    if not patch_text.strip():
        diff = _git_run(["diff"])
        save_text(patches_dir / "git_diff_after.diff", diff.stdout or "")
        names = _git_run(["diff", "--name-only"])
        save_text(patches_dir / "git_diff_after_name_only.txt", names.stdout or "")
        meta["diff_summary"] = (
            f"patch empty; git diff lines={len((diff.stdout or '').splitlines())}"
        )
        meta["git_diff_after_artifact"] = _artifact_path_str(
            patches_dir / "git_diff_after.diff"
        )
        meta["git_diff_after_name_only_artifact"] = _artifact_path_str(
            patches_dir / "git_diff_after_name_only.txt"
        )
        return meta

    p = _git_run(["apply", "--whitespace=nowarn", str(patch_path)])
    meta["git_apply_returncode"] = int(p.returncode)
    meta["git_apply_stderr"] = (p.stderr or "").strip()
    if p.returncode != 0:
        raise RuntimeError(
            "proposed_patch の適用に失敗しました: " + (p.stderr or "").strip()
        )
    meta["patch_applied"] = True

    expected = _expected_existing_files_from_patch(patch_text)
    missing: List[str] = []
    for rel in expected:
        fp = ROOT_DIR / rel
        if not fp.exists():
            missing.append(rel)
    if missing:
        raise FileNotFoundError(
            "patch 適用後に存在すべきファイルが見つかりません: " + ", ".join(missing)
        )

    diff = _git_run(["diff"])
    save_text(patches_dir / "git_diff_after.diff", diff.stdout or "")
    names = _git_run(["diff", "--name-only"])
    save_text(patches_dir / "git_diff_after_name_only.txt", names.stdout or "")
    meta["diff_summary"] = f"git diff lines={len((diff.stdout or '').splitlines())}"
    meta["git_diff_after_artifact"] = _artifact_path_str(
        patches_dir / "git_diff_after.diff"
    )
    meta["git_diff_after_name_only_artifact"] = _artifact_path_str(
        patches_dir / "git_diff_after_name_only.txt"
    )
    return meta


def _is_git_repository() -> bool:
    p = _git_run(["rev-parse", "--git-dir"])
    return p.returncode == 0


def get_current_git_branch() -> str:
    p = _git_run(["rev-parse", "--abbrev-ref", "HEAD"])
    if p.returncode != 0:
        raise RuntimeError(f"現在ブランチを取得できません: {p.stderr.strip()}")
    return p.stdout.strip()


def is_git_worktree_dirty() -> bool:
    p = _git_run(["status", "--porcelain"])
    if p.returncode != 0:
        raise RuntimeError(f"git status に失敗しました: {p.stderr.strip()}")
    return bool(p.stdout.strip())


def enforce_git_sandbox_branch(session_id: str) -> None:
    """
    main/master 上・dirty なら停止。
    sandbox/session-XX を作成または checkout する。
    """
    if not _is_git_repository():
        raise RuntimeError("Git リポジトリではありません（git init 済みか確認してください）。")

    branch = get_current_git_branch()
    if branch.lower() in FORBIDDEN_BRANCHES:
        raise RuntimeError(
            f"安全弁: ブランチが {branch!r} です。main/master 上では実行できません。"
        )

    if is_git_worktree_dirty():
        raise RuntimeError(
            "安全弁: 作業ツリーが dirty です。未コミットの変更を解消してから実行してください。"
        )

    target = f"sandbox/{session_id}"
    if branch == target:
        return

    # ローカルブランチの有無
    show_ref = _git_run(["show-ref", "--verify", "--quiet", f"refs/heads/{target}"])
    if show_ref.returncode == 0:
        co = _git_run(["checkout", target])
        if co.returncode != 0:
            raise RuntimeError(f"checkout に失敗: {co.stderr.strip()}")
    else:
        cb = _git_run(["checkout", "-b", target])
        if cb.returncode != 0:
            raise RuntimeError(f"ブランチ作成に失敗: {cb.stderr.strip()}")


def normalize_changed_file_path(path_str: str) -> str:
    """比較用に POSIX 形式へ正規化する。"""
    p = Path(path_str)
    try:
        rel = p.as_posix()
    except (OSError, ValueError):
        rel = str(path_str).replace("\\", "/")
    return rel.lstrip("./")


MAX_FILES = 5

FORBIDDEN_PATHS = [
    "docs/sessions",
    "docs/acceptance",
    "artifacts",
]


def check_file_count(changed_files: List[str]) -> bool:
    return len(changed_files) <= MAX_FILES


def check_forbidden_paths(changed_files: List[str]) -> bool:
    for f in changed_files:
        for forbidden in FORBIDDEN_PATHS:
            if f.startswith(forbidden):
                return False
    return True


def validate_patch_files(changed_files: List[str]) -> Dict[str, Any]:
    if not check_file_count(changed_files):
        return {
            "status": "error",
            "error_type": "scope_violation",
            "message": f"changed_files exceeds limit: {len(changed_files)} > {MAX_FILES}",
        }

    if not check_forbidden_paths(changed_files):
        return {
            "status": "error",
            "error_type": "scope_violation",
            "message": "forbidden path detected",
        }

    return {
        "status": "success",
    }


def _collect_forbidden_phrases(
    session_data: Dict[str, Any],
    prepared_spec: Dict[str, Any],
) -> List[str]:
    phrases: List[str] = []
    for item in session_data.get("out_of_scope", []):
        if isinstance(item, str) and item.strip():
            phrases.append(item.strip())
    fc = prepared_spec.get("forbidden_changes", [])
    if isinstance(fc, list):
        for item in fc:
            if isinstance(item, str) and item.strip():
                phrases.append(item.strip())
    return phrases


def validate_allowed_changes_detail_enforcement(
    changed_files: list,
    allowed_changes_detail: list,
) -> None:
    """allowed_changes_detail の記述に基づき、changed_files の妥当性を検証する。

    allowed_changes_detail の各項目は "path: description" 形式。
    path 部分を抽出し、changed_files がいずれかの path にマッチするかを検証する。
    マッチしない changed_file があれば ValueError を raise する。

    path が "backend/tests/*" のようにワイルドカード末尾なら、
    "backend/tests/" 配下のすべてのファイルを許可する。
    """
    # 許可パスリストを構築する
    allowed_paths: list = []
    for item in allowed_changes_detail:
        if not isinstance(item, str):
            continue
        # "path: description" 形式の先頭 path 部分を取り出す
        path_part = item.split(":")[0].strip()
        if path_part:
            allowed_paths.append(path_part)

    if not allowed_paths:
        # 許可リストが空なら検証スキップ（全許可と同義）
        return

    def _matches_detail_path(changed: str, detail_path: str) -> bool:
        """detail_path が changed にマッチするか判定する。"""
        if detail_path.endswith("/*"):
            # ワイルドカード末尾: ディレクトリ配下を全許可
            prefix = detail_path[:-2]  # "/*" を除去
            return changed == prefix or changed.startswith(prefix + "/")
        if detail_path.endswith("/"):
            # スラッシュ末尾: ディレクトリ配下を全許可
            prefix = detail_path.rstrip("/")
            return changed == prefix or changed.startswith(prefix + "/")
        return changed == detail_path

    for changed in changed_files:
        if not any(_matches_detail_path(changed, ap) for ap in allowed_paths):
            raise ValueError(
                f"changed_file {changed!r} は allowed_changes_detail に含まれていません。"
                f" 許可パス: {allowed_paths}"
            )


def validate_changed_files_before_patch(
    impl_result: Dict[str, Any],
    prepared_spec: Dict[str, Any],
    session_data: Dict[str, Any],
    max_changed_files: int,
) -> None:
    """
    proposed_patch 適用前の妥当性チェック。
    changed_files の型・件数・禁止キーワードとの衝突を検証する。
    """
    raw = impl_result.get("changed_files", [])
    if raw is None:
        raw = []
    if not isinstance(raw, list):
        raise ValueError("implementation_result.changed_files はリストである必要があります。")

    normalized: List[str] = []
    for i, item in enumerate(raw):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(
                f"implementation_result.changed_files[{i}] は空でない文字列である必要があります。"
            )
        normalized.append(normalize_changed_file_path(item))

    allowed_raw = prepared_spec.get("allowed_changes", [])
    allowed_changes: List[str] = []
    if isinstance(allowed_raw, list):
        for item in allowed_raw:
            if isinstance(item, str) and item.strip():
                allowed_changes.append(normalize_changed_file_path(item))

    def _is_explicitly_allowed(path: str) -> bool:
        for allowed in allowed_changes:
            # 末尾スラッシュはディレクトリ許可、それ以外は完全一致
            if allowed.endswith("/"):
                prefix = allowed.rstrip("/")
                if path == prefix or path.startswith(prefix + "/"):
                    return True
                continue
            if path == allowed:
                return True
        return False

    non_explicit_files = [p for p in normalized if not _is_explicitly_allowed(p)]

    vp = validate_patch_files(non_explicit_files)
    if vp["status"] == "error":
        raise ValueError(vp.get("message", "scope violation"))

    # allowed_changes_detail が存在する場合のみ粒度チェックを実行する
    allowed_changes_detail = session_data.get("allowed_changes_detail")
    if allowed_changes_detail and isinstance(allowed_changes_detail, list):
        validate_allowed_changes_detail_enforcement(normalized, allowed_changes_detail)

    if len(normalized) > max_changed_files:
        raise ValueError(
            f"changed_files が上限を超えています: {len(normalized)} > {max_changed_files}"
        )

    phrases = _collect_forbidden_phrases(session_data, prepared_spec)
    min_phrase_len = 3
    for path in non_explicit_files:
        path_l = path.lower()
        for phrase in phrases:
            pl = phrase.lower()
            if len(pl) < min_phrase_len:
                continue
            if pl in path_l:
                raise ValueError(
                    f"禁止キーワードと一致するパス: {path!r} に対して forbidden/out_of_scope の "
                    f"{phrase!r} が検出されました。"
                )
            # ディレクトリプレフィックス指定（例: production/）
            if phrase.endswith("/") or phrase.endswith("\\"):
                prefix = phrase.rstrip("/\\").lower()
                if prefix and path_l.startswith(prefix + "/"):
                    raise ValueError(
                        f"禁止プレフィックス配下のパス: {path!r} （{phrase!r}）"
                    )


def _normalize_hunk_line_prefixes(text: str) -> str:
    """
    hunk 内で +/-/スペース/\\ で始まらない行に + を補完する。
    Claude が def/class 等の行で + を省略した corrupt patch を修正する。
    """
    _HEADER = (
        "diff --git",
        "--- ",
        "+++ ",
        "index ",
        "new file",
        "deleted file",
        "old mode",
        "new mode",
    )
    fixed: List[str] = []
    in_hunk = False
    for line in text.split("\n"):
        if line.startswith(_HEADER):
            in_hunk = False
            fixed.append(line)
        elif line.startswith("@@"):
            in_hunk = True
            fixed.append(line)
        elif in_hunk and line and not line.startswith(("+", "-", " ", "\\")):
            fixed.append("+" + line)
        else:
            fixed.append(line)
    return "\n".join(fixed)


def _apply_patch_smart(patch_path: Path, repo_root: Path) -> bool:
    """Apply a unified diff patch, handling new files by direct write.

    For files that don't exist in the repo:
      - Extract '+' lines and write the file directly
    For files that already exist:
      - Use git apply --whitespace=fix

    Returns True if at least one change was made, False otherwise.
    """
    raw_text = patch_path.read_text(encoding="utf-8", errors="replace")
    # hunk 内で + が抜けた行を補完してから処理する
    text = _normalize_hunk_line_prefixes(raw_text)
    if text != raw_text:
        patch_path.write_text(text, encoding="utf-8")
    lines = text.split("\n")

    # Parse patch into per-file sections (--- ... until next --- or EOF)
    file_sections: list[dict[str, Any]] = []
    header_buf: list[str] = []
    current: dict[str, Any] | None = None

    for line in lines:
        if line.startswith("--- "):
            if current is not None:
                file_sections.append(current)
            current = {
                "source": line,
                "target": None,
                "lines": list(header_buf) + [line],
            }
            header_buf.clear()
        elif current is not None:
            if line.startswith("+++ "):
                if line.startswith("+++ b/"):
                    current["target"] = line[len("+++ b/") :]
                current["lines"].append(line)
            else:
                current["lines"].append(line)
        else:
            # diff --git など、最初の --- より前の行
            header_buf.append(line)

    if current is not None:
        file_sections.append(current)

    if not file_sections and lines:
        file_sections = [{"source": "", "target": None, "lines": lines}]

    new_file_targets: list[str] = []
    existing_file_lines: list[str] = []

    for section in file_sections:
        target = section.get("target")
        if target is None:
            existing_file_lines.extend(section["lines"])
            continue

        full_path = repo_root / target

        # @@ -0,0 ハンクは新規ファイル作成を意図しているため、既存ファイルでも上書きする
        is_new_file_hunk = any(
            sline.startswith("@@ -0,0 ") or sline.startswith("@@ -0 +")
            for sline in section["lines"]
        )

        if not full_path.exists() or is_new_file_hunk:
            if full_path.exists() and is_new_file_hunk:
                logger.info("Overwriting existing file via new-file patch: %s", target)
            # NEW FILE: extract content from '+' lines
            content_lines: list[str] = []
            for sline in section["lines"]:
                if sline.startswith("@@"):
                    continue  # skip hunk headers
                if sline.startswith("--- ") or sline.startswith("+++ "):
                    continue  # skip file headers
                if sline.startswith("+"):
                    content_lines.append(sline[1:])  # strip leading '+'
                elif sline.startswith("-"):
                    continue  # skip removal lines (shouldn't exist for new files)
                elif sline.startswith(" "):
                    content_lines.append(sline[1:])  # context line

            if content_lines:
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text("\n".join(content_lines), encoding="utf-8")
                new_file_targets.append(target)
                logger.info("Wrote new file directly: %s", target)
        else:
            # EXISTING FILE: keep in patch for git apply
            existing_file_lines.extend(section["lines"])

    applied_existing = False
    if existing_file_lines:
        remaining_patch = patch_path.parent / "remaining.patch"
        remaining_text = _normalize_hunk_line_prefixes("\n".join(existing_file_lines))
        remaining_patch.write_text(remaining_text, encoding="utf-8")
        proc = _git_run(["apply", "--whitespace=fix", str(remaining_patch)])
        if proc.returncode != 0:
            logger.warning(
                "git apply for existing files failed: %s",
                (proc.stderr or "").strip(),
            )
        else:
            applied_existing = True
        remaining_patch.unlink(missing_ok=True)

    return bool(new_file_targets) or applied_existing


def apply_proposed_patch_and_capture_artifacts(
    session_dir: Path,
    impl_result: Dict[str, Any],
    *,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Claude からの proposed_patch を artifacts/patches に保存し、
    git apply で適用したうえで git diff --name-only による実差分を取得する。
    """
    patch_dir = session_dir / "patches"
    patch_dir.mkdir(parents=True, exist_ok=True)

    raw_patch = impl_result.get("proposed_patch", "")
    if not isinstance(raw_patch, str):
        raw_patch = str(raw_patch)
    patch_text = normalize_patch_for_git_apply(raw_patch)

    patch_path = patch_dir / "proposed.patch"
    save_text(patch_path, patch_text)

    patch_targets = set(_expected_existing_files_from_patch(patch_text))

    def _collect_changed_files() -> List[str]:
        diff_proc = _git_run(["diff", "--name-only"])
        if diff_proc.returncode != 0:
            raise RuntimeError(f"git diff --name-only に失敗しました: {diff_proc.stderr.strip()}")
        tracked_changed = [
            normalize_changed_file_path(line)
            for line in (diff_proc.stdout or "").splitlines()
            if line.strip()
        ]

        untracked_proc = _git_run(["ls-files", "--others", "--exclude-standard"])
        if untracked_proc.returncode != 0:
            untracked_all = []
        else:
            untracked_all = [
                normalize_changed_file_path(line)
                for line in (untracked_proc.stdout or "").splitlines()
                if line.strip()
            ]
        untracked_all = [
            normalize_changed_file_path(line)
            for line in (untracked_proc.stdout or "").splitlines()
            if line.strip()
        ]
        # proposed_patch の +++ b/... に含まれる対象だけを untracked 収集対象にする
        untracked_changed = [p for p in untracked_all if p in patch_targets]

        merged: List[str] = []
        seen: set[str] = set()
        for path in [*tracked_changed, *untracked_changed]:
            if path and path not in seen:
                seen.add(path)
                merged.append(path)
        return merged

    # 空パッチの場合は適用せず、現在の実差分のみを返す
    if not patch_text.strip():
        changed = _collect_changed_files()
        return {
            "patch_path": patch_path,
            "applied": False,
            "changed_files": changed,
            "patch_apply_failed": False,
            "patch_apply_message": "",
        }

    patch_applied = _apply_patch_smart(patch_path, ROOT_DIR)
    if not patch_applied:
        logger.warning("No changes were applied from the patch")

    changed_files = _collect_changed_files()

    patch_apply_failed = bool(patch_text.strip()) and len(changed_files) == 0
    patch_apply_message = ""
    if patch_apply_failed:
        patch_apply_message = (
            "git apply 相当の処理後も実差分が得られませんでした（パッチ形式の不整合または適用失敗の可能性）"
        )

    return {
        "patch_path": patch_path,
        "applied": not patch_apply_failed,
        "changed_files": changed_files,
        "patch_apply_failed": patch_apply_failed,
        "patch_apply_message": patch_apply_message,
    }

def build_dry_run_prepared_spec(ctx: SessionContext) -> Dict[str, Any]:
    """dry-run 用のダミー prepared_spec（API 非呼び出し）。"""
    return {
        "session_id": ctx.session_id,
        "objective": ctx.session_data.get("goal", ""),
        "allowed_changes": ["docs/", "orchestration/", "artifacts/"],
        "forbidden_changes": list(ctx.session_data.get("out_of_scope", [])),
        "completion_criteria": ["dry-run: API を呼ばず骨組み検証のみ"],
        "acceptance_criteria": ["dry-run モード"],
        "review_points": ["dry-run"],
        "implementation_notes": ["OpenAI/Claude は呼び出していません"],
    }


def build_dry_run_implementation_result(ctx: SessionContext) -> Dict[str, Any]:
    """dry-run 用のダミー implementation_result。"""
    return {
        "session_id": ctx.session_id,
        "changed_files": [],
        "implementation_summary": ["dry-run: 実装 API は未実行"],
        "patch_status": "dry_run",
        "risks": [],
        "open_issues": [],
        "proposed_patch": "",
    }


def build_skipped_checks_result() -> Dict[str, Any]:
    """dry-run 時のローカルチェック（すべて skipped）。"""
    skipped: Dict[str, Any] = {
        "status": "skipped",
        "command": "",
        "returncode": None,
        "stdout": "",
        "stderr": "",
    }
    return {
        "test": dict(skipped),
        "lint": dict(skipped),
        "typecheck": dict(skipped),
        "build": dict(skipped),
        "success": True,
    }


def _is_read_only_live_run_outcome(ctx: SessionContext, impl_result: Dict[str, Any]) -> bool:
    """
    read-only live-run（変更対象が session 上も実装結果上も無い）かを判定する。
    allowed_changes が空のセッションに限定し、code-fix での「実装不能」と read-only 成功を混同しない。
    """
    allowed = ctx.session_data.get("allowed_changes", [])
    return bool(
        impl_result.get("patch_status") == "not_applicable"
        and impl_result.get("changed_files") == []
        and not impl_result.get("proposed_patch")
        and allowed == []
    )


def _build_check_results_for_read_only_live_run() -> Dict[str, Any]:
    """read-only live-run: patch_apply は適用対象なしとして success、ローカル checks はすべて skipped。"""
    sk: Dict[str, Any] = {
        "status": "skipped",
        "command": "",
        "returncode": None,
        "stdout": "",
        "stderr": "",
    }
    return {
        "patch_apply": {
            "status": "not_applicable",
            "command": "",
            "returncode": None,
            "stdout": "",
            "stderr": "read-only live-run: proposed_patch なし・変更対象なしのため patch 適用をスキップ",
        },
        "test": dict(sk),
        "lint": dict(sk),
        "typecheck": dict(sk),
        "build": dict(sk),
        "success": True,
        "patch_apply_failed": False,
    }


def _build_check_results_for_patch_apply_failure(patch_apply_message: str) -> Dict[str, Any]:
    """proposed_patch があるが git apply 相当で実差分が得られなかった場合の checks（以降の pytest 等は実行しない）。"""
    sk: Dict[str, Any] = {
        "status": "skipped",
        "command": "",
        "returncode": None,
        "stdout": "",
        "stderr": "",
    }
    return {
        "patch_apply": {
            "status": "failed",
            "command": "git apply",
            "returncode": 1,
            "stdout": "",
            "stderr": patch_apply_message,
        },
        "test": dict(sk),
        "lint": dict(sk),
        "typecheck": dict(sk),
        "build": dict(sk),
        "success": False,
        "patch_apply_failed": True,
    }


def _apply_patch_validate_and_run_local_checks(
    *,
    session_dir: Path,
    ctx: SessionContext,
    impl_result: Dict[str, Any],
    prepared_spec: Dict[str, Any],
    max_changed_files: int,
    skip_build: bool,
    session_id: str,
    retry_label: str = "",
) -> Dict[str, Any]:
    """
    patch 適用 → changed_files 反映 → 妥当性検証 → ローカル checks。
    patch 未適用が明白な場合は checks をスキップし patch_apply_failure 用の結果を返す。
    """
    if _is_read_only_live_run_outcome(ctx, impl_result):
        impl_result["changed_files"] = []
        impl_result["diff_summary"] = "changed_files: 0 files (read-only live-run)"
        save_json(session_dir / "responses" / "implementation_result.json", impl_result)
        check_results = _build_check_results_for_read_only_live_run()
        save_json(session_dir / "test_results" / "checks.json", check_results)
        log_stage_progress(
            session_id,
            "patch_apply",
            (retry_label + " " if retry_label else "")
            + "read-only live-run: patch 適用スキップ",
        )
        return check_results

    patch_info = apply_proposed_patch_and_capture_artifacts(
        session_dir=session_dir,
        impl_result=impl_result,
        session_id=session_id,
    )
    real_changed_files = patch_info.get("changed_files", [])
    if not isinstance(real_changed_files, list):
        real_changed_files = []
    impl_result["changed_files"] = real_changed_files
    impl_result["diff_summary"] = f"changed_files: {len(real_changed_files)} files"
    save_json(session_dir / "responses" / "implementation_result.json", impl_result)

    if patch_info.get("patch_apply_failed"):
        detail = str(patch_info.get("patch_apply_message") or "").strip()
        if not detail:
            detail = (
                "git apply 相当の処理後も実差分が得られませんでした（パッチ形式の不整合または適用失敗の可能性）"
            )
        log_stage_progress(
            session_id,
            "patch_apply",
            (retry_label + " " if retry_label else "")
            + "patch 未適用のためローカル checks（pytest 等）をスキップ",
        )
        check_results = _build_check_results_for_patch_apply_failure(detail)
        save_json(session_dir / "test_results" / "checks.json", check_results)
        return check_results

    stage_val = "patch_validation"
    log_stage_progress(
        session_id,
        stage_val,
        (retry_label + " " if retry_label else "") + "changed_files 妥当性チェック",
    )
    validate_changed_files_before_patch(
        impl_result,
        prepared_spec,
        ctx.session_data,
        max_changed_files,
    )

    stage_chk = "checks"
    log_stage_progress(
        session_id,
        stage_chk,
        (retry_label + " " if retry_label else "") + "ローカル test/lint/typecheck/build",
    )
    check_results = run_local_checks(ctx, skip_build=skip_build)
    save_json(session_dir / "test_results" / "checks.json", check_results)
    return check_results


def build_prepared_spec_prompts(ctx: SessionContext) -> Tuple[str, str]:
    system_prompt = """You are a strict spec organizer.
One session must have exactly one objective.
Return only valid JSON.
Do not add markdown fences.
Do not expand scope.
Respect allowed_changes / forbidden_changes.
Respect out_of_scope and constraints.
completion_criteria / acceptance_criteria / review_points are required.
Acceptance must be test-mappable.
Do not guess missing facts.
Keep the existing top-level key structure exactly.
"""

    user_prompt = f"""
session_id: {ctx.session_id}

[master_instruction]
{ctx.master_instruction}

[global_rules]
{ctx.global_rules}

[roadmap]
{ctx.roadmap_text}

[session_json]
{json.dumps(ctx.session_data, ensure_ascii=False, indent=2)}

[acceptance_yaml]
{ctx.acceptance_data["raw_yaml"]}

Constraints:
- allowed_changes must be concrete and actionable.
- forbidden_changes must not conflict with out_of_scope.
- completion_criteria must include normal-path, error-path, and no-side-effect checks.
- acceptance_criteria must remain test-mappable.
- review_points must include exactly these 4 axes:
  1) spec match (AC achieved)
  2) scope adherence
  3) no side effects (no regression)
  4) no over/under implementation
- Do not guess; use only the provided context.
- Keep existing JSON top-level keys exactly as listed.

Return JSON with keys:
session_id
objective
allowed_changes
forbidden_changes
completion_criteria
acceptance_criteria
review_points
implementation_notes
"""
    return system_prompt, user_prompt


def build_implementation_prompts(
    prepared_spec: Dict[str, Any],
    ctx: SessionContext,
    retry_instruction: Optional[Dict[str, Any]] = None,
) -> Tuple[str, str]:
    system_prompt = """You are a strict implementation assistant.
Return only valid JSON.
Do not add markdown fences.
Do not expand scope.
If implementation is not possible, explain in JSON.

[patch format requirements]
- proposed_patch MUST be in unified diff format (diff --git a/<path> b/<path>, --- a/<path>, +++ b/<path>, @@ ... @@)
- Each modified file MUST have its own diff --git header
- patch_status MUST be exactly one of: "applied", "not_applicable", "dry_run", "partial"
- Do NOT use "ready", "done", "completed", "ready_for_manual_verification" or any other value for patch_status
"""

    retry_block = ""
    if retry_instruction:
        retry_block = "\n\n[retry_instruction]\n" + json.dumps(
            retry_instruction, ensure_ascii=False, indent=2
        )
        # fix_instructions と do_not_change を明示的に展開して反映する
        fix_items = retry_instruction.get("fix_instructions") or []
        dnc_items = retry_instruction.get("do_not_change") or []
        if fix_items:
            fix_lines = "\n".join(f"- {x}" for x in fix_items if x)
            retry_block += f"\n\n[fix_instructions to apply]\n{fix_lines}"
        if dnc_items:
            dnc_lines = "\n".join(f"- {x}" for x in dnc_items if x)
            retry_block += f"\n\n[do_not_change (must not touch these)]\n{dnc_lines}"

    # allowed_changes の既存ファイル内容をプロンプトに含める（パッチ生成精度向上）
    current_files_block = ""
    for item in prepared_spec.get("allowed_changes", []):
        # "path/to/file.py: description" 形式からファイルパスを抽出
        path_str = item.split(":")[0].strip() if ":" in item else item.strip()
        # ワイルドカードは除外
        if "*" in path_str or "?" in path_str:
            continue
        full_path = ROOT_DIR / path_str
        if full_path.exists() and full_path.is_file():
            try:
                content = full_path.read_text(encoding="utf-8")
                current_files_block += f"\n\n[current file: {path_str}]\n{content}"
            except Exception:
                pass

    user_prompt = f"""
session_id: {ctx.session_id}

[prepared_spec]
{json.dumps(prepared_spec, ensure_ascii=False, indent=2)}

[session_json]
{json.dumps(ctx.session_data, ensure_ascii=False, indent=2)}
{current_files_block}
{retry_block}

Return JSON with keys:
session_id
changed_files
implementation_summary
patch_status  (must be one of: "applied", "not_applicable", "dry_run", "partial")
risks
open_issues
proposed_patch  (must be unified diff format)
"""
    return system_prompt, user_prompt


def build_retry_prompts(
    ctx: SessionContext,
    prepared_spec: Dict[str, Any],
    impl_result: Dict[str, Any],
    check_results: Dict[str, Any],
) -> Tuple[str, str]:
    system_prompt = """You are a strict failure analyzer.
Return only valid JSON.
Do not add markdown fences.
Do not change scope.
Do not expand scope.
failure_type must be exactly one value.
Respect allowed_changes / forbidden_changes strictly.
do_not_change must stay consistent with forbidden_changes.
fix_instructions must be limited to the allowed change scope only.
Do not guess missing facts.
"""

    canonical = resolve_canonical_failure_type(check_results)
    user_prompt = f"""
session_id: {ctx.session_id}

[prepared_spec]
{json.dumps(prepared_spec, ensure_ascii=False, indent=2)}

[implementation_result]
{json.dumps(impl_result, ensure_ascii=False, indent=2)}

[check_results]
{json.dumps(check_results, ensure_ascii=False, indent=2)}

Scope note: Do not expand scope. Respect allowed_changes / forbidden_changes described in prepared_spec.
Reviewer contract:
- fix_instructions must stay within allowed_changes only.
- do_not_change must not conflict with forbidden_changes.
- cause_summary must be concrete and specific. Do not use vague words.
- Include failed_tests and error_summary.
- changed_files must be within allowed_changes.
- Keep existing JSON top-level keys exactly as listed.

Return JSON with keys:
session_id
failure_type  # failure_type は出力に1つのみ（exactly one）
priority
cause_summary
fix_instructions
do_not_change
failed_tests
error_summary
changed_files

Known failure_type (canonical): {canonical.get("failure_type")} (priority={canonical.get("priority")})
"""
    return system_prompt, user_prompt


def call_chatgpt_for_prepared_spec(ctx: SessionContext) -> Dict[str, Any]:
    from orchestration.providers.openai_client import OpenAIClientConfig, OpenAIClientWrapper

    openai_cfg = ctx.runtime_config["providers"]["openai"]
    client = OpenAIClientWrapper(
        OpenAIClientConfig(
            model=openai_cfg["model"],
            timeout_sec=openai_cfg.get("timeout_sec", 120),
            max_output_tokens=openai_cfg.get("max_output_tokens", 4000),
        )
    )
    # prepared_spec は Builder 契約反映済み prompt を用いて生成する。
    system_prompt, user_prompt = build_prepared_spec_prompts(ctx)
    return client.request_prepared_spec(system_prompt, user_prompt)


def call_chatgpt_for_retry_instruction(
    ctx: SessionContext,
    prepared_spec: Dict[str, Any],
    impl_result: Dict[str, Any],
    check_results: Dict[str, Any],
) -> Dict[str, Any]:
    # 同一原因のリトライ抑止（過去 retry_instruction.json の fingerprint と一致する場合）
    cause_fp = _compute_retry_cause_fingerprint(check_results)
    prev_path = ARTIFACTS_DIR / ctx.session_id / "responses" / "retry_instruction.json"
    if prev_path.is_file():
        try:
            prev = json.loads(prev_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            prev = {}
        if isinstance(prev, dict) and prev.get("cause_fingerprint") == cause_fp:
            merged = _merge_retry_instruction({}, ctx, prepared_spec, impl_result, check_results)
            merged["cause_fingerprint"] = cause_fp
            merged["retry_skipped_same_cause"] = True
            return merged

    from orchestration.providers.openai_client import OpenAIClientConfig, OpenAIClientWrapper

    openai_cfg = ctx.runtime_config["providers"]["openai"]
    client = OpenAIClientWrapper(
        OpenAIClientConfig(
            model=openai_cfg["model"],
            timeout_sec=openai_cfg.get("timeout_sec", 120),
            max_output_tokens=openai_cfg.get("max_output_tokens", 4000),
        )
    )
    system_prompt, user_prompt = build_retry_prompts(
        ctx, prepared_spec, impl_result, check_results
    )
    raw = client.request_retry_instruction(system_prompt, user_prompt)
    merged = _merge_retry_instruction(raw, ctx, prepared_spec, impl_result, check_results)
    merged["cause_fingerprint"] = cause_fp
    return merged


def validate_acceptance_test_mapping(
    acceptance_items: List[Dict[str, Any]],
    available_test_names: List[str],
) -> Dict[str, Any]:
    """acceptance の test_name が pytest の利用可能テスト名に存在するか検証する。"""
    avail = {x for x in available_test_names if isinstance(x, str)}
    missing: List[str] = []
    for item in acceptance_items:
        if not isinstance(item, dict):
            continue
        tn = item.get("test_name")
        if isinstance(tn, str) and tn and tn not in avail:
            missing.append(tn)
    if missing:
        return {"status": "error", "missing_test_names": missing}
    return {"status": "success", "missing_test_names": []}


def normalize_check_results_for_retry(check_results: Dict[str, Any]) -> Dict[str, Any]:
    """retry 判定用にチェック結果を正規化する（オプショナル項目をデフォルト化）。"""
    out = dict(check_results or {})
    out.setdefault("scope_violation", False)
    out.setdefault("regression_detected", False)
    out.setdefault("spec_missing_detected", False)
    out.setdefault("error_messages", [])
    out.setdefault("patch_apply_failed", False)
    return out


FAILURE_TYPE_PRIORITY_ORDER: List[str] = [
    "patch_apply_failure",
    "generated_artifact_invalid",
    "build_error",
    "import_error",
    "type_mismatch",
    "test_failure",
    "scope_violation",
    "breaking_change",
    "spec_missing",
]

VALID_FAILURE_TYPES = frozenset({
    "patch_apply_failure",
    "generated_artifact_invalid",
    "build_error",
    "import_error",
    "type_mismatch",
    "test_failure",
    "scope_violation",
    "breaking_change",
    "spec_missing",
    "no_failure",
})


def validate_failure_type(failure_type: str) -> str:
    """failure_type が定義済み enum にあるか検証する。未知値は ValueError を raise する。"""
    if failure_type not in VALID_FAILURE_TYPES:
        raise ValueError(
            f"Unknown failure_type: {failure_type!r}. Valid: {sorted(VALID_FAILURE_TYPES)}"
        )
    return failure_type


def normalize_failure_type_by_priority(candidates: list) -> str:
    """複数の failure_type 候補から、FAILURE_TYPE_PRIORITY_ORDER に基づき
    最も優先度の高い1つを返す。候補が空なら 'spec_missing' を返す。"""
    if not candidates:
        return "spec_missing"
    best: Optional[str] = None
    best_idx = len(FAILURE_TYPE_PRIORITY_ORDER)
    for ft in candidates:
        ft_str = str(ft)
        try:
            idx = FAILURE_TYPE_PRIORITY_ORDER.index(ft_str)
        except ValueError:
            idx = len(FAILURE_TYPE_PRIORITY_ORDER)
        if idx < best_idx:
            best_idx = idx
            best = ft_str
    return best if best is not None else "spec_missing"


def _extract_cause_summary(check_results: Dict[str, Any], channel: str) -> str:
    channel_result = (check_results.get(channel) or {})
    stderr = str(channel_result.get("stderr") or "").strip()
    stdout = str(channel_result.get("stdout") or "").strip()
    msg = stderr or stdout
    if not msg:
        return f"{channel} の失敗原因を特定できませんでした"
    return msg.splitlines()[0][:200]


def _test_stderr_indicates_generated_syntax_error(check_results: Dict[str, Any]) -> bool:
    """pytest 出力に生成物の SyntaxError 系（IndentationError 含む）が含まれるか。"""
    stderr = str((check_results.get("test") or {}).get("stderr") or "")
    stdout = str((check_results.get("test") or {}).get("stdout") or "")
    blob = f"{stderr}\n{stdout}"
    syntax_error_family = ("SyntaxError", "IndentationError", "TabError")
    return any(token in blob for token in syntax_error_family)


def _failure_layer_for_failure_type(failure_type: str) -> str:
    """failure_type を failure_layer（4分類）へ写す。"""
    if failure_type in ("patch_apply_failure", "generated_artifact_invalid", "type_mismatch"):
        return "generated_artifact"
    if failure_type in ("import_error", "build_error"):
        return "environment"
    if failure_type in (
        "test_failure",
        "scope_violation",
        "breaking_change",
        "spec_missing",
    ):
        return "specification"
    return "orchestrator"


def _retryable_for_failure_type(failure_type: str) -> bool:
    """人間／モデル側の再試行が合理的か（スコープ違反は原則不可）。"""
    if failure_type == "scope_violation":
        return False
    return True


def _infer_stop_stage(
    checks: Dict[str, Any],
    failure_type: str,
    aborted_stage: Optional[str],
) -> str:
    if aborted_stage and str(aborted_stage).strip():
        return str(aborted_stage).strip()
    if checks.get("patch_apply_failed") is True:
        return "patch_apply"
    pa = checks.get("patch_apply") or {}
    if isinstance(pa, dict) and pa.get("status") == "failed":
        return "patch_apply"
    return "checks"


def build_failure_record_for_report(
    checks: Dict[str, Any],
    status: str,
    *,
    error_message: Optional[str],
    aborted_stage: Optional[str],
) -> Dict[str, Any]:
    """
    report.json 用の failure メタデータ（failure_layer / stop_stage / retryable / cause_summary）。
    成功時は failure_type を除き null で揃える。
    """
    if status != "failed":
        return {
            "failure_type": None,
            "failure_layer": None,
            "stop_stage": None,
            "retryable": None,
            "cause_summary": None,
        }

    canonical = resolve_canonical_failure_type(checks)
    cf = classify_failure(checks)
    ft = str(canonical.get("failure_type") or cf.get("failure_type") or "spec_missing")
    if ft == "no_failure":
        ft = "spec_missing"
    cause = str(cf.get("cause_summary") or "").strip()
    if not cause and error_message:
        cause = str(error_message).strip()[:500]
    if not cause:
        cause = "失敗原因を特定できませんでした"

    return {
        "failure_type": ft,
        "failure_layer": _failure_layer_for_failure_type(ft),
        "stop_stage": _infer_stop_stage(checks, ft, aborted_stage),
        "retryable": _retryable_for_failure_type(ft),
        "cause_summary": cause[:2000],
    }


def classify_failure(check_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    retry 用の failure_type を正規化して 1 つだけ返す。
    優先順位:
    patch_apply_failure -> build_error -> generated_artifact_invalid(SyntaxError) ->
    import_error -> type_mismatch -> test_failure -> scope_violation -> breaking_change -> spec_missing
    """
    cr = normalize_check_results_for_retry(check_results or {})
    build = (cr.get("build") or {}).get("status")
    test = (cr.get("test") or {}).get("status")
    typecheck = (cr.get("typecheck") or {}).get("status")
    lint = (cr.get("lint") or {}).get("status")

    if cr.get("patch_apply_failed") is True:
        detail = str((cr.get("patch_apply") or {}).get("stderr") or "").strip()
        if not detail:
            detail = "proposed_patch が適用されず実差分がありません"
        return {
            "failure_type": "patch_apply_failure",
            "cause_summary": detail[:2000],
        }

    if build == "failed":
        return {
            "failure_type": "build_error",
            "cause_summary": _extract_cause_summary(cr, "build"),
        }

    if test == "failed":
        if _test_stderr_indicates_generated_syntax_error(cr):
            return {
                "failure_type": "generated_artifact_invalid",
                "cause_summary": _extract_cause_summary(cr, "test"),
            }
        test_stderr = str((cr.get("test") or {}).get("stderr") or "")
        if "ModuleNotFoundError" in test_stderr or "ImportError" in test_stderr:
            return {
                "failure_type": "import_error",
                "cause_summary": _extract_cause_summary(cr, "test"),
            }

    if typecheck == "failed":
        return {
            "failure_type": "type_mismatch",
            "cause_summary": _extract_cause_summary(cr, "typecheck"),
        }

    if lint == "failed" or test == "failed":
        return {
            "failure_type": "test_failure",
            "cause_summary": _extract_cause_summary(cr, "test" if test == "failed" else "lint"),
        }

    if cr.get("scope_violation") is True:
        return {"failure_type": "scope_violation", "cause_summary": "スコープ制約に違反しています"}

    if cr.get("regression_detected") is True:
        return {"failure_type": "breaking_change", "cause_summary": "既存の期待挙動を破壊しています"}

    if cr.get("spec_missing_detected") is True:
        return {"failure_type": "spec_missing", "cause_summary": "仕様情報が不足しています"}

    _default_ft = validate_failure_type("spec_missing")  # 戻り値 failure_type の enum 検証
    return {"failure_type": _default_ft, "cause_summary": "失敗原因を一意に特定できませんでした"}


def validate_retry_instruction_schema(instruction: dict) -> None:
    """retry_instruction の必須キー・型を検証する。不正なら ValueError を raise する。"""
    # cause_summary: 非空文字列
    cs = instruction.get("cause_summary")
    if not isinstance(cs, str) or not cs.strip():
        raise ValueError("retry_instruction.cause_summary は空でない文字列である必要があります")
    # fix_instructions: 非空リスト
    fi = instruction.get("fix_instructions")
    if not isinstance(fi, list) or len(fi) == 0:
        raise ValueError("retry_instruction.fix_instructions は空でないリストである必要があります")
    # do_not_change: 非空リスト
    dnc = instruction.get("do_not_change")
    if not isinstance(dnc, list) or len(dnc) == 0:
        raise ValueError("retry_instruction.do_not_change は空でないリストである必要があります")
    # session_id: 文字列
    if "session_id" not in instruction:
        raise ValueError("retry_instruction.session_id が存在しません")
    # failure_type: 文字列
    if "failure_type" not in instruction:
        raise ValueError("retry_instruction.failure_type が存在しません")
    # priority: int
    if "priority" not in instruction:
        raise ValueError("retry_instruction.priority が存在しません")


def build_retry_instruction(
    *,
    ctx: SessionContext,
    prepared_spec: Dict[str, Any],
    failure: Dict[str, Any],
    stop_reason: str = "",
) -> Dict[str, Any]:
    """retry_instruction の必須キーを常に埋める。"""
    failure_type = str(failure.get("failure_type") or "spec_missing")
    cause_summary = str(failure.get("cause_summary") or "失敗原因を特定できませんでした")
    try:
        priority = FAILURE_TYPE_PRIORITY_ORDER.index(failure_type) + 1
    except ValueError:
        priority = len(FAILURE_TYPE_PRIORITY_ORDER)
    fix_instructions = [
        f"{failure_type} の原因 ({cause_summary}) に対する最小修正のみ実施すること。",
        "変更は allowed_changes に限定し、副作用を増やさないこと。",
    ]
    dnc: List[str] = []
    forbidden = prepared_spec.get("forbidden_changes", [])
    if isinstance(forbidden, list):
        dnc = [str(x).strip() for x in forbidden if isinstance(x, str) and str(x).strip()]
    if not dnc:
        dnc = ["out_of_scope と forbidden_changes を変更しないこと。"]
    out: Dict[str, Any] = {
        "session_id": ctx.session_id,
        "failure_type": failure_type,
        "priority": int(priority),
        "cause_summary": cause_summary,
        "fix_instructions": fix_instructions,
        "do_not_change": dnc,
    }
    if stop_reason:
        out["stop_reason"] = stop_reason
    validate_retry_instruction_schema(out)  # スキーマ検証（末尾に1行追加）
    return out


def retry_loop(
    *,
    retry_history: List[Dict[str, Any]],
    failure: Dict[str, Any],
    retry_count: int,
    max_retries: int,
) -> Dict[str, Any]:
    """同一失敗の再試行抑止と上限判定を一元化する。"""
    failure_type = str(failure.get("failure_type") or "spec_missing")
    cause_summary = str(failure.get("cause_summary") or "").strip() or "原因不明"
    for item in retry_history:
        if item.get("failure_type") == failure_type and item.get("cause_summary") == cause_summary:
            return {
                "should_retry": False,
                "failure_type": failure_type,
                "cause_summary": cause_summary,
                "retry_count": int(retry_count),
                "stop_reason": "same_failure_and_cause",
            }
    if retry_count >= max_retries:
        return {
            "should_retry": False,
            "failure_type": failure_type,
            "cause_summary": cause_summary,
            "retry_count": int(retry_count),
            "stop_reason": "max_retries_reached",
        }
    if retry_history and retry_history[-1].get("failure_type") == failure_type:
        return {
            "should_retry": False,
            "failure_type": failure_type,
            "cause_summary": cause_summary,
            "retry_count": int(retry_count),
            "stop_reason": "failure_type_repeated",
        }
    return {
        "should_retry": True,
        "failure_type": failure_type,
        "cause_summary": cause_summary,
        "retry_count": int(retry_count),
        "stop_reason": "",
    }


def resolve_canonical_failure_type(check_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    正本の failure_type ＋ no_failure を返す。
    priority は小さいほど高優先（0 は no_failure）。
    既存テスト互換のため build_error=1, import_error=2, type_mismatch=3, test_failure=4 は維持する。
    """
    cr = normalize_check_results_for_retry(check_results or {})

    if cr.get("patch_apply_failed") is True:
        return {"failure_type": "patch_apply_failure", "priority": 1}

    # フラグ系（テストが成功でも scope_violation 等が立つことがある）
    flag_map = [
        ("scope_violation", "scope_violation", 5),
        ("regression_detected", "breaking_change", 6),
        ("spec_missing_detected", "spec_missing", 7),
    ]
    flagged: List[Tuple[str, int]] = []
    for k, ft, pri in flag_map:
        if cr.get(k) is True:
            flagged.append((ft, pri))
    if flagged:
        ft, pri = sorted(flagged, key=lambda x: x[1])[0]
        return {"failure_type": ft, "priority": pri}

    if cr.get("success") is True:
        return {"failure_type": "no_failure", "priority": 0}

    build = (cr.get("build") or {}).get("status")
    typecheck = (cr.get("typecheck") or {}).get("status")
    lint = (cr.get("lint") or {}).get("status")
    test = (cr.get("test") or {}).get("status")

    if build == "failed":
        return {"failure_type": "build_error", "priority": 1}

    # 生成された Python / テストの SyntaxError（pytest 収集・実行時）
    if test == "failed" and _test_stderr_indicates_generated_syntax_error(cr):
        return {"failure_type": "generated_artifact_invalid", "priority": 2}

    # import_error は test の stderr から推定（ModuleNotFoundError 等）
    if test == "failed":
        stderr = str((cr.get("test") or {}).get("stderr") or "")
        if "ModuleNotFoundError" in stderr or "ImportError" in stderr:
            return {"failure_type": "import_error", "priority": 2}

    if typecheck == "failed":
        return {"failure_type": "type_mismatch", "priority": 3}

    if lint == "failed" or test == "failed":
        return {"failure_type": "test_failure", "priority": 4}

    # ここまで来たら「失敗だが特定できない」扱い。最小限で test_failure に寄せる。
    return {"failure_type": "test_failure", "priority": 4}


def classify_failure_type(check_results: Dict[str, Any]) -> Dict[str, Any]:
    """旧互換: build/typecheck/lint/test の固定優先順位で failure_type を返す。"""
    cr = check_results or {}
    order = [("build", "build_failure", 4), ("typecheck", "typecheck_failure", 3), ("lint", "lint_failure", 2), ("test", "test_failure", 1)]
    for key, ft, pri in order:
        if (cr.get(key) or {}).get("status") == "failed":
            return {"failure_type": ft, "priority": pri}
    return {"failure_type": "no_failure", "priority": 0}


def _compute_retry_cause_fingerprint(check_results: Dict[str, Any]) -> str:
    """同一原因判定用のフィンガープリント（安定・短縮）。"""
    cr = normalize_check_results_for_retry(check_results or {})
    canonical = resolve_canonical_failure_type(cr)
    parts = {
        "failure_type": canonical.get("failure_type"),
        "priority": canonical.get("priority"),
        "patch_apply_failed": bool(cr.get("patch_apply_failed")),
        "patch_apply_stderr": (str((cr.get("patch_apply") or {}).get("stderr") or ""))[:500],
        "test_stderr": ((cr.get("test") or {}).get("stderr") or "")[:500],
        "build_stderr": ((cr.get("build") or {}).get("stderr") or "")[:500],
        "typecheck_stderr": ((cr.get("typecheck") or {}).get("stderr") or "")[:500],
        "lint_stderr": ((cr.get("lint") or {}).get("stderr") or "")[:500],
        "flags": {
            "scope_violation": bool(cr.get("scope_violation")),
            "regression_detected": bool(cr.get("regression_detected")),
            "spec_missing_detected": bool(cr.get("spec_missing_detected")),
        },
    }
    s = json.dumps(parts, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def _merge_retry_instruction(
    raw: Dict[str, Any],
    ctx: SessionContext,
    prepared_spec: Dict[str, Any],
    impl_result: Dict[str, Any],
    check_results: Dict[str, Any],
) -> Dict[str, Any]:
    """OpenAI からの出力を正規化し、必須キーを埋める。"""
    canonical = resolve_canonical_failure_type(check_results)
    # cause_summary は classify_failure から取得（resolve_canonical_failure_type は持たない）
    _cf = classify_failure(check_results)
    out: Dict[str, Any] = dict(raw or {})
    out["session_id"] = ctx.session_id
    out["failure_type"] = canonical["failure_type"]
    out["priority"] = canonical["priority"]

    if not isinstance(out.get("cause_summary"), str) or not str(out.get("cause_summary")).strip():
        out["cause_summary"] = str(_cf.get("cause_summary") or "原因不明")

    fi = out.get("fix_instructions")
    if isinstance(fi, str):
        fi = [fi]
    if not isinstance(fi, list) or not any(isinstance(x, str) and x.strip() for x in fi):
        out["fix_instructions"] = [
            "失敗ログ（stderr / stdout）を確認し、原因に直接対応する最小修正を行うこと。",
            "スコープを拡張せず、既存仕様・制約を守ること。",
        ]
    else:
        out["fix_instructions"] = [str(x).strip() for x in fi if isinstance(x, str) and x.strip()]

    dnc = out.get("do_not_change")
    if isinstance(dnc, str):
        dnc = [dnc]
    if not isinstance(dnc, list):
        dnc = []
    forb = prepared_spec.get("forbidden_changes", [])
    if isinstance(forb, list):
        for x in forb:
            if isinstance(x, str) and x.strip():
                dnc.append(x.strip())
    if not dnc:
        dnc = ["out_of_scope と forbidden_changes を変更しないこと。"]
    # 重複排除（順序維持）
    seen: set[str] = set()
    uniq: List[str] = []
    for x in dnc:
        sx = str(x).strip()
        if not sx or sx in seen:
            continue
        seen.add(sx)
        uniq.append(sx)
    out["do_not_change"] = uniq

    return out


def compute_next_retry_count(current: int, did_request_new_instruction: bool) -> int:
    """リトライ指示を新規取得した場合のみ retry_count を +1 する。"""
    if did_request_new_instruction:
        return int(current) + 1
    return int(current)


def _read_retry_state_count(session_dir: Path) -> int:
    p = session_dir / "responses" / "retry_state.json"
    if not p.is_file():
        return 0
    try:
        return int(json.loads(p.read_text(encoding="utf-8")).get("retry_count", 0))
    except (ValueError, TypeError, json.JSONDecodeError):
        return 0


def _write_retry_state_count(session_dir: Path, n: int) -> None:
    save_json(session_dir / "responses" / "retry_state.json", {"retry_count": int(n)})


def build_session_report_record(
    ctx: SessionContext,
    prepared_spec: Dict[str, Any],
    impl_result: Dict[str, Any],
    checks: Dict[str, Any],
    *,
    status: Optional[str] = None,
    completion: Optional[str] = None,
    retry_control: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """機械向けの session_report.json レコードを生成する。"""
    rc = retry_control or {}
    acceptance_items = []
    parsed = (ctx.acceptance_data or {}).get("parsed") or {}
    if isinstance(parsed, dict):
        ai = parsed.get("acceptance", [])
        if isinstance(ai, list):
            acceptance_items = ai

    fn_results = (checks or {}).get("test_function_results") or {}
    acceptance_results: List[Dict[str, Any]] = []
    for item in acceptance_items:
        if not isinstance(item, dict):
            continue
        tid = item.get("id")
        tn = item.get("test_name")
        desc = item.get("description")
        if not isinstance(tn, str) or not tn:
            continue
        passed = fn_results.get(tn)
        if passed is True:
            res = "passed"
        elif passed is False:
            res = "failed"
        else:
            res = "not_applicable"
        row: Dict[str, Any] = {"id": tid, "test": tn, "result": res}
        if isinstance(desc, str) and desc:
            row["description"] = desc
        acceptance_results.append(row)

    def _to_pf(v: Any) -> str:
        s = str(v or "").strip().lower()
        if s in ("passed", "pass", "ok", "success"):
            return "pass"
        if s in ("failed", "fail", "error"):
            return "fail"
        return "skip"

    def _normalize_str_list(v: Any) -> List[str]:
        if not isinstance(v, list):
            return []
        return [str(x) for x in v if isinstance(x, str)]

    normalized_status = "failed" if str(status or "").strip().lower() == "failed" else "success"
    normalized_completion = str(completion or "").strip().lower()
    valid_completion = {"review_required", "retry_required", "stopped"}
    if normalized_completion not in valid_completion:
        if normalized_status == "success":
            normalized_completion = "review_required"
        else:
            normalized_completion = "retry_required"

    changed_files = _normalize_str_list(impl_result.get("changed_files", []))
    diff_summary_raw = impl_result.get("diff_summary")
    if isinstance(diff_summary_raw, str) and diff_summary_raw.strip():
        diff_summary = diff_summary_raw.strip()
    elif changed_files:
        diff_summary = f"changed_files: {len(changed_files)} files"
    else:
        diff_summary = "changed_files: none"

    return {
        "session_id": ctx.session_id,
        "status": normalized_status,
        "completion": normalized_completion,
        "phase_id": (ctx.session_data or {}).get("phase_id"),
        "title": (ctx.session_data or {}).get("title"),
        "goal": (ctx.session_data or {}).get("goal"),
        "objective": prepared_spec.get("objective"),
        "changed_files": changed_files,
        "diff_summary": diff_summary,
        "test_result": _to_pf((checks.get("test") or {}).get("status")),
        "lint_result": _to_pf((checks.get("lint") or {}).get("status")),
        "typecheck_result": _to_pf((checks.get("typecheck") or {}).get("status")),
        "build_result": _to_pf((checks.get("build") or {}).get("status")),
        "risks": _normalize_str_list(impl_result.get("risks", [])),
        "open_issues": _normalize_str_list(impl_result.get("open_issues", [])),
        "acceptance_results": list(acceptance_results),
        "retry_count": int(rc.get("retry_count", 0) or 0),
        "max_retries": int(rc.get("max_retries", 0) or 0),
        "retry_stopped_same_cause": bool(rc.get("retry_stopped_same_cause", False)),
        "retry_stopped_max_retries": bool(rc.get("retry_stopped_max_retries", False)),
    }


def build_acceptance_results_for_report_json(
    ctx: Optional[SessionContext],
    checks: Dict[str, Any],
) -> List[Dict[str, str]]:
    """
    report.json 用の acceptance_results を生成する。
    形式は最小限（id, result）で、result は passed/failed/not_applicable の3値のみ。
    """
    if ctx is None:
        return []
    parsed = (ctx.acceptance_data or {}).get("parsed") or {}
    acceptance_items = parsed.get("acceptance", []) if isinstance(parsed, dict) else []
    if not isinstance(acceptance_items, list):
        return []

    fn_results = (checks or {}).get("test_function_results") or {}
    out: List[Dict[str, str]] = []
    for item in acceptance_items:
        if not isinstance(item, dict):
            continue
        tid = item.get("id")
        tn = item.get("test_name")
        if not isinstance(tid, str) or not tid:
            continue
        if not isinstance(tn, str) or not tn:
            result = "not_applicable"
        else:
            passed = fn_results.get(tn)
            if passed is True:
                result = "passed"
            elif passed is False:
                result = "failed"
            else:
                result = "not_applicable"
        out.append({"id": tid, "result": result})
    return out


def _any_check_skipped(checks: Optional[Dict[str, Any]]) -> bool:
    """test/lint/typecheck/build のいずれかが skipped なら True（条件付き完了の判定用）。"""
    if not checks or not isinstance(checks, dict):
        return False
    for name in ("test", "lint", "typecheck", "build"):
        st = (checks.get(name) or {}).get("status")
        if st == "skipped":
            return True
    return False


def _any_acceptance_not_applicable(acceptance_results: List[Dict[str, Any]]) -> bool:
    """受理基準の一部が not_applicable のとき True（条件付き完了の判定用）。"""
    for item in acceptance_results or []:
        if isinstance(item, dict) and item.get("result") == "not_applicable":
            return True
    return False


def validate_acceptance_test_names(acceptance_items: list) -> None:
    """acceptance.yaml の各項目に test_name が必須であることを検証する。
    test_name が欠落している項目があれば ValueError を raise する。"""
    for i, item in enumerate(acceptance_items):
        if not isinstance(item, dict):
            continue
        if not item.get("test_name"):
            ac_id = item.get("id", f"index-{i}")
            raise ValueError(
                f"acceptance item {ac_id} is missing required 'test_name'"
            )


def evaluate_completion_decision(
    acceptance_data: dict,
    checks_results: dict,
    changed_files: list,
    allowed_changes: list,
) -> dict:
    """completion 判定を機械的に行う。

    pass 条件（全て満たす必要あり）:
      1. acceptance の全 AC に test_name が存在する
      2. checks の test/lint/typecheck/build が全て passed or skipped
      3. changed_files が allowed_changes 内

    いずれか1つでも不成立なら fail を返す。

    Returns: {"completion": "pass" | "fail", "reasons": [...]}
    """
    reasons: list = []

    # 条件1: acceptance 全項目に test_name が存在する
    items = acceptance_data.get("items", []) if isinstance(acceptance_data, dict) else []
    try:
        validate_acceptance_test_names(items)
    except ValueError as exc:
        reasons.append(str(exc))

    # 条件2: checks の各カテゴリが passed または skipped
    required_checks = ["test", "lint", "typecheck", "build"]
    for check_key in required_checks:
        result = checks_results.get(check_key, "")
        if result not in ("passed", "skipped"):
            reasons.append(f"check '{check_key}' is '{result}' (expected passed or skipped)")

    # 条件3: changed_files が allowed_changes 内
    allowed_set = set(allowed_changes)
    for cf in changed_files:
        if cf not in allowed_set:
            reasons.append(f"changed_file {cf!r} is not in allowed_changes")

    if reasons:
        return {"completion": "fail", "reasons": reasons}
    return {"completion": "pass", "reasons": []}


def decide_completion_status(
    status: str,
    acceptance_results: List[Dict[str, Any]],
    risks: List[Any],
    open_issues: List[Any],
    checks: Optional[Dict[str, Any]] = None,
    *,
    retry_control: Optional[Dict[str, Any]] = None,
    aborted_stage: Optional[str] = None,
) -> Dict[str, Any]:
    """
    completion_status（実行完了時に確定するライフサイクル）と human_review_needed を決定する。
    completion_status は review_required / passed / conditional_pass / failed / stopped のみ。
    """
    rc = retry_control or {}
    if bool(rc.get("retry_stopped_same_cause")) or bool(rc.get("retry_stopped_max_retries")):
        return {"completion_status": "stopped", "human_review_needed": False}
    if aborted_stage is not None and str(aborted_stage).strip():
        return {"completion_status": "stopped", "human_review_needed": False}

    has_fail = any(
        isinstance(item, dict) and item.get("result") == "failed"
        for item in (acceptance_results or [])
    )
    if status == "failed" or has_fail:
        return {"completion_status": "failed", "human_review_needed": False}

    if len(risks or []) > 0 or len(open_issues or []) > 0:
        return {"completion_status": "review_required", "human_review_needed": True}

    if status == "dry_run":
        return {"completion_status": "conditional_pass", "human_review_needed": False}

    if _any_check_skipped(checks) or _any_acceptance_not_applicable(acceptance_results):
        return {"completion_status": "conditional_pass", "human_review_needed": False}

    return {"completion_status": "passed", "human_review_needed": False}


def _session_index_row_from_report_dict(
    data: Dict[str, Any], fallback_dir_name: str
) -> Dict[str, Any]:
    """artifacts 配下の report.json 1件から index 行を作る（欠損は規格化、KeyError は出さない）。"""
    sid_raw = data.get("session_id")
    session_id = str(sid_raw) if sid_raw is not None else fallback_dir_name
    status_raw = data.get("status")
    status = str(status_raw) if status_raw is not None else "unknown"
    cs_raw = data.get("completion_status")
    completion_status = str(cs_raw) if cs_raw is not None else "unknown"
    br = data.get("branch")
    branch = br if isinstance(br, str) and br.strip() else "unavailable"
    cmt = data.get("commit_sha")
    commit_sha = cmt if isinstance(cmt, str) and cmt.strip() else "unavailable"
    dur_raw = data.get("duration_sec")
    try:
        duration_sec = float(dur_raw) if dur_raw is not None else 0.0
    except (TypeError, ValueError):
        duration_sec = 0.0
    ft = data.get("failure_type")
    if ft is None or ft == "":
        failure_type = "unknown"
    else:
        failure_type = str(ft)
    return {
        "session_id": session_id,
        "status": status,
        "completion_status": completion_status,
        "branch": branch,
        "commit_sha": commit_sha,
        "duration_sec": duration_sec,
        "failure_type": failure_type,
    }


def _build_artifacts_index_and_summary(
    artifacts_dir: Path, current_payload: Dict[str, Any]
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    artifacts 配下の report.json を走査し sessions 一覧と summary を返す。
    現在の実行分は current_payload で上書き（ディスク未反映でも集計に含める）。
    """
    current_id = str(current_payload.get("session_id") or "")
    rows: Dict[str, Dict[str, Any]] = {}
    if artifacts_dir.is_dir():
        for child in sorted(artifacts_dir.iterdir()):
            if not child.is_dir():
                continue
            rp = child / "report.json"
            if not rp.is_file():
                continue
            try:
                raw = json.loads(rp.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if not isinstance(raw, dict):
                continue
            sid = str(raw.get("session_id") or child.name)
            rows[sid] = _session_index_row_from_report_dict(raw, child.name)
    rows[current_id] = _session_index_row_from_report_dict(
        current_payload, current_id or "unknown"
    )
    sessions_sorted = sorted(rows.values(), key=lambda x: x["session_id"])
    total = len(sessions_sorted)
    success_count = sum(1 for s in sessions_sorted if s["status"] == "success")
    failed_count = sum(1 for s in sessions_sorted if s["status"] == "failed")
    success_rate = (float(success_count) / float(total)) if total else 0.0
    failure_type_counts: Dict[str, int] = {}
    for s in sessions_sorted:
        fk = s["failure_type"]
        failure_type_counts[fk] = failure_type_counts.get(fk, 0) + 1
    duration_sum = sum(s["duration_sec"] for s in sessions_sorted)
    duration_avg = (duration_sum / float(total)) if total else 0.0
    summary: Dict[str, Any] = {
        "total_sessions": total,
        "success_count": success_count,
        "failed_count": failed_count,
        "success_rate": success_rate,
        "failure_type_counts": failure_type_counts,
        "duration_avg": duration_avg,
    }
    return sessions_sorted, summary


def extract_api_usage(response: dict) -> dict:
    """API レスポンスから usage 情報を抽出する。
    usage が存在しない場合は空辞書を返す（エラーにしない）。"""
    if not isinstance(response, dict):
        return {}
    usage = response.get("usage")
    if isinstance(usage, dict):
        return usage
    return {}


# 概算コスト単価（USD / 1Mトークン）—静的定数として管理する
_COST_PER_1M_TOKENS: Dict[str, Dict[str, float]] = {
    "openai": {"input": 2.50, "output": 10.00},   # gpt-4o 概算
    "claude": {"input": 3.00, "output": 15.00},    # claude-sonnet-4 概算
}


def estimate_cost(usage: dict, provider: str) -> float:
    """usage 辞書から概算コスト（USD）を計算する。
    usage が欠落・不正な場合は 0.0 を返す（エラーにしない）。"""
    if not isinstance(usage, dict) or not usage:
        return 0.0
    rates = _COST_PER_1M_TOKENS.get(provider, {})
    if not rates:
        return 0.0
    # OpenAI: prompt_tokens / completion_tokens
    # Claude: input_tokens / output_tokens
    input_tokens = int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
    output_tokens = int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
    cost = (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1_000_000
    return round(cost, 8)


def build_cost_summary(api_usage: dict, api_call_count: dict) -> dict:
    """api_usage と api_call_count から cost summary を生成する。
    usage が欠落している場合は 0.0 として扱う（エラーにしない）。"""
    if not isinstance(api_usage, dict):
        api_usage = {}
    if not isinstance(api_call_count, dict):
        api_call_count = {}
    summary: Dict[str, Any] = {}
    total_usd = 0.0
    for provider in ("openai", "claude"):
        usage = api_usage.get(provider) or {}
        call_count = int(api_call_count.get(provider) or 0)
        cost = estimate_cost(usage, provider)
        total_usd += cost
        summary[provider] = {
            "estimated_cost_usd": cost,
            "call_count": call_count,
        }
    summary["total_estimated_cost_usd"] = round(total_usd, 8)
    return summary


def persist_session_reports(
    session_dir: Path,
    ctx: Optional[SessionContext],
    prepared_spec: Dict[str, Any],
    impl_result: Dict[str, Any],
    checks: Dict[str, Any],
    *,
    status: str,
    dry_run: bool,
    started_at: str,
    finished_at: str,
    retry_instruction: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
    retry_control: Optional[Dict[str, Any]] = None,
    aborted_stage: Optional[str] = None,
    api_usage: Optional[Dict[str, Any]] = None,
    api_call_count: Optional[Dict[str, Any]] = None,
) -> None:
    """
    既存 report 関数を活用しつつ、検収用 report.json を標準出力する。
    - reports/session_report.md: 人間向け（既存 generate_report）
    - reports/session_report.json: 機械向け（既存 build_session_report_record）
    - report.json: 検収用の標準化レポート（本セッション仕様）
    """
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / "reports").mkdir(parents=True, exist_ok=True)

    # 既存の md/json（ctx が無い場合は最小限に落とす）
    if ctx is not None:
        report_md = generate_report(
            ctx=ctx,
            prepared_spec=prepared_spec,
            impl_result=impl_result,
            checks=checks,
            retry_instruction=retry_instruction,
            aborted_stage=aborted_stage,
        )
        save_text(session_dir / "reports" / "session_report.md", report_md)

        report_obj = build_session_report_record(
            ctx,
            prepared_spec,
            impl_result,
            checks,
            status=status,
            completion=(
                "review_required"
                if status == "success"
                else (
                    "stopped"
                    if (
                        bool((retry_control or {}).get("retry_stopped_same_cause"))
                        or bool((retry_control or {}).get("retry_stopped_max_retries"))
                    )
                    else "retry_required"
                )
            ),
            retry_control=retry_control,
        )
        save_json(session_dir / "reports" / "session_report.json", report_obj)

    # 標準化 report.json（常に 1 つだけ上書き生成）
    changed_files = impl_result.get("changed_files", [])
    if not isinstance(changed_files, list):
        changed_files = []

    failure_type: Optional[str] = None
    if status == "failed":
        try:
            failure_type = resolve_canonical_failure_type(checks).get("failure_type")
        except Exception:
            failure_type = None
        # no_failure は失敗時の failure_type としては意味が薄いので null 扱い
        if failure_type == "no_failure":
            failure_type = None

    git_branch = _git_branch_safe()
    git_sha = _git_commit_sha_safe()
    branch_out = git_branch if git_branch else "unavailable"
    commit_out = git_sha if git_sha else "unavailable"
    merged_to_main = bool(
        git_branch and git_branch.strip().lower() in ("main", "master")
    )

    payload: Dict[str, Any] = {
        "session_id": (ctx.session_id if ctx is not None else str(session_dir.name)),
        "status": status,
        "dry_run": bool(dry_run),
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_sec": _duration_sec_from_iso(started_at, finished_at),
        "changed_files": changed_files,
        "risks": list(impl_result.get("risks", []) or []),
        "open_issues": list(impl_result.get("open_issues", []) or []),
        "checks": checks if isinstance(checks, dict) else {},
        "failure_type": failure_type,
        "error_message": error_message if (status == "failed") else None,
        "branch": branch_out,
        "commit_sha": commit_out,
        "source_branch": branch_out,
        "merged_to_main": merged_to_main,
    }
    payload.update(
        build_failure_record_for_report(
            checks if isinstance(checks, dict) else {},
            status,
            error_message=error_message,
            aborted_stage=aborted_stage,
        )
    )
    if "acceptance_results" not in payload:
        payload["acceptance_results"] = build_acceptance_results_for_report_json(ctx, checks)
    completion = decide_completion_status(
        status,
        payload.get("acceptance_results", []),
        payload.get("risks", []),
        payload.get("open_issues", []),
        payload.get("checks") if isinstance(payload.get("checks"), dict) else {},
        retry_control=retry_control,
        aborted_stage=aborted_stage,
    )
    payload["completion_status"] = completion["completion_status"]
    payload["human_review_needed"] = completion["human_review_needed"]
    # API usage 情報（存在する場合のみ記録する）
    _api_usage_safe = api_usage if isinstance(api_usage, dict) else {}
    _api_call_count_safe = api_call_count if isinstance(api_call_count, dict) else {}
    payload["api_usage"] = _api_usage_safe
    payload["api_call_count"] = _api_call_count_safe
    # cost summary（usage から概算コストを計算する。欠落時は 0.0 として扱う）
    payload["cost_summary"] = build_cost_summary(_api_usage_safe, _api_call_count_safe)
    # Phase2: evaluate_completion_decision を追加フィールドとして記録する（decide_completion_status を置換しない）
    try:
        _acc_parsed = (ctx.acceptance_data.get("parsed") or {}) if ctx is not None else {}
        _acc_items = _acc_parsed.get("acceptance", [])
        _allowed = list(ctx.session_data.get("allowed_changes", [])) if ctx is not None else []
        # checks の値を evaluate_completion_decision が期待するフラット形式に正規化する
        _norm_checks = {
            k: (v.get("status", "") if isinstance(v, dict) else str(v or ""))
            for k, v in (checks if isinstance(checks, dict) else {}).items()
            if k in ("test", "lint", "typecheck", "build")
        }
        payload["phase2_completion_eval"] = evaluate_completion_decision(
            acceptance_data={"items": _acc_items if isinstance(_acc_items, list) else []},
            checks_results=_norm_checks,
            changed_files=changed_files,
            allowed_changes=_allowed,
        )
    except Exception:
        payload["phase2_completion_eval"] = {"completion": "fail", "reasons": ["evaluation error"]}
    artifacts_root = session_dir.parent
    sessions_index, summary_metrics = _build_artifacts_index_and_summary(
        artifacts_root, payload
    )
    payload["sessions"] = sessions_index
    payload["summary"] = summary_metrics
    save_json(session_dir / "report.json", payload)


def _persist_guard_failure_artifacts(
    session_dir: Path,
    impl_result: Dict[str, Any],
    error: Exception,
    stage: str,
) -> None:
    """validate_impl_result 失敗時に raw response と failure reason を保存する。"""
    responses_dir = session_dir / "responses"
    try:
        save_json(responses_dir / "guard_failure_raw_response.json", impl_result)
        save_json(
            responses_dir / "guard_failure_reason.json",
            {
                "error_type": type(error).__name__,
                "message": str(error),
                "stage": stage,
            },
        )
        logger.info("Guard failure artifacts persisted under: %s", responses_dir)
    except Exception as persist_err:
        logger.warning("Failed to persist guard failure artifacts: %s", persist_err)


_IMPL_BLOCKING_KEYS = (
    "changed_files",
    "implementation_summary",
    "proposed_patch",
)
_PATCH_STATUS_ALIASES: dict[str, str] = {
    "no_patch_required": "not_applicable",
    "none": "not_applicable",
    "no_changes": "not_applicable",
    "skip": "not_applicable",
    "skipped": "not_applicable",
    "ready": "applied",  # Claude が patch_status="ready" を返す場合のエイリアス
}

_VALID_PATCH_STATUSES = frozenset(
    {"applied", "partial", "not_applicable", "dry_run"}
)


def validate_impl_result(result: dict) -> None:
    """Claude 実装応答の必須キー存在を検証する。

    blocking（ValueError）:
        - changed_files / implementation_summary / proposed_patch が欠落の場合
    warning のみ（raise しない）:
        - session_id が欠落の場合
        - patch_status が欠落または有効値以外の場合
        - changed_files が list でない場合
        - implementation_summary が list でも str でもない場合
    """
    # blocking 必須キー存在確認
    for key in _IMPL_BLOCKING_KEYS:
        if key not in result:
            raise ValueError(
                f"Claude implementation result missing required key: '{key}'"
            )

    # session_id 欠落（warning のみ）
    if "session_id" not in result:
        logger.warning(
            "validate_impl_result: session_id is missing from implementation result"
        )

    # patch_status 正規化（非正規値を正規値へ変換）
    raw_status = result.get("patch_status", "")
    normalized = _PATCH_STATUS_ALIASES.get(raw_status, raw_status)
    if normalized != raw_status:
        logger.info("patch_status normalized: '%s' -> '%s'", raw_status, normalized)
        result["patch_status"] = normalized

    # patch_status 検証（warning のみ）
    if "patch_status" not in result:
        logger.warning(
            "validate_impl_result: patch_status is missing from implementation result"
        )
    elif result["patch_status"] not in _VALID_PATCH_STATUSES:
        logger.warning(
            "validate_impl_result: invalid patch_status '%s'. "
            "Expected one of: %s",
            result["patch_status"],
            sorted(_VALID_PATCH_STATUSES),
        )

    # 型チェック（warning のみ）
    changed_files = result["changed_files"]
    if not isinstance(changed_files, list):
        logger.warning(
            "validate_impl_result: changed_files is not a list (got %s)",
            type(changed_files).__name__,
        )

    impl_summary = result["implementation_summary"]
    if not isinstance(impl_summary, (list, str)):
        logger.warning(
            "validate_impl_result: implementation_summary is not list or str (got %s)",
            type(impl_summary).__name__,
        )


def call_claude_for_implementation(
    prepared_spec: Dict[str, Any],
    ctx: SessionContext,
    retry_instruction: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    from orchestration.providers.claude_client import ClaudeClientConfig, ClaudeClientWrapper

    claude_cfg = ctx.runtime_config["providers"]["claude"]
    client = ClaudeClientWrapper(
        ClaudeClientConfig(
            model=claude_cfg["model"],
            timeout_sec=claude_cfg.get("timeout_sec", 180),
            max_output_tokens=claude_cfg.get("max_output_tokens", 6000),
        )
    )
    system_prompt, user_prompt = build_implementation_prompts(
        prepared_spec, ctx, retry_instruction
    )
    return client.request_implementation(system_prompt, user_prompt)


def run_command(command: str, timeout_sec: int = 300) -> Dict[str, Any]:
    if not command.strip():
        return {
            "status": "skipped",
            "command": command,
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "timeout": False,
        }

    # pytest 実行中に pytest コマンドを再帰起動してハングするのを防ぐ。
    if os.environ.get("PYTEST_CURRENT_TEST") and "pytest" in command.lower():
        return {
            "status": "skipped",
            "command": command,
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "timeout": False,
        }

    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=ROOT_DIR,
            text=True,
            capture_output=True,
            timeout=timeout_sec,
        )
    except subprocess.TimeoutExpired:
        return {
            "status": "failed",
            "command": command,
            "returncode": -1,
            "stdout": "",
            "stderr": "timeout exceeded",
            "timeout": True,
        }

    return {
        "status": "passed" if proc.returncode == 0 else "failed",
        "command": command,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "timeout": False,
    }


def run_local_checks(ctx: SessionContext, skip_build: bool = False) -> Dict[str, Any]:
    commands = ctx.runtime_config.get("commands", {})
    stop_on_first = ctx.runtime_config.get("runtime", {}).get(
        "stop_on_first_check_failure", True
    )

    results: Dict[str, Any] = {}

    test_result = run_command(commands.get("test", ""))
    results["test"] = test_result
    if stop_on_first and test_result["status"] == "failed":
        results["success"] = False
        return results

    lint_result = run_command(commands.get("lint", ""))
    results["lint"] = lint_result
    if stop_on_first and lint_result["status"] == "failed":
        results["success"] = False
        return results

    typecheck_result = run_command(commands.get("typecheck", ""))
    results["typecheck"] = typecheck_result
    if stop_on_first and typecheck_result["status"] == "failed":
        results["success"] = False
        return results

    if skip_build:
        results["build"] = {
            "status": "skipped",
            "command": "",
            "returncode": None,
            "stdout": "",
            "stderr": "",
        }
    else:
        build_result = run_command(commands.get("build", ""))
        results["build"] = build_result
        if stop_on_first and build_result["status"] == "failed":
            results["success"] = False
            return results

    results["success"] = all(
        results[name]["status"] in ("passed", "skipped")
        for name in ["test", "lint", "typecheck", "build"]
    )
    return results


def generate_report(
    ctx: SessionContext,
    prepared_spec: Dict[str, Any],
    impl_result: Dict[str, Any],
    checks: Dict[str, Any],
    retry_instruction: Optional[Dict[str, Any]] = None,
    aborted_stage: Optional[str] = None,
) -> str:
    lines = [
        f"# Session Report: {ctx.session_id}",
        "",
        f"- Phase: {ctx.session_data['phase_id']}",
        f"- Title: {ctx.session_data['title']}",
        f"- Goal: {ctx.session_data['goal']}",
    ]
    if aborted_stage:
        lines.extend(["", f"## Aborted at stage: {aborted_stage}"])

    lines.extend([
        "",
        "## Prepared Spec",
        f"- Objective: {prepared_spec.get('objective')}",
        "",
        "## Changed Files",
    ])

    changed_files = impl_result.get("changed_files", [])
    if changed_files:
        lines.extend([f"- {x}" for x in changed_files])
    else:
        lines.append("- none")

    lines.extend([
        "",
        "## Implementation Summary",
        *[f"- {x}" for x in impl_result.get("implementation_summary", [])],
        "",
        "## Checks",
        f"- Test: {checks.get('test', {}).get('status')}",
        f"- Lint: {checks.get('lint', {}).get('status')}",
        f"- Typecheck: {checks.get('typecheck', {}).get('status')}",
        f"- Build: {checks.get('build', {}).get('status')}",
        f"- Success: {checks.get('success')}",
        "",
        "## Risks",
        *[f"- {x}" for x in impl_result.get("risks", [])],
        "",
        "## Open Issues",
        *[f"- {x}" for x in impl_result.get("open_issues", [])],
    ])

    if retry_instruction:
        fix_lines = retry_instruction.get("fix_instructions", [])
        if isinstance(fix_lines, str):
            fix_lines = [fix_lines]
        lines.extend([
            "",
            "## Retry Instruction",
            f"- Failure Type: {retry_instruction.get('failure_type')}",
            f"- Priority: {retry_instruction.get('priority')}",
            f"- Cause Summary: {retry_instruction.get('cause_summary')}",
            "### Fix Instructions",
            *[f"- {x}" for x in fix_lines],
        ])

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--session-id", required=True, help="e.g. session-01")
    parser.add_argument("--max-retries", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-build", action="store_true")
    return parser.parse_args()


def _max_changed_files_from_config(cfg: Dict[str, Any]) -> int:
    lim = cfg.get("limits") or {}
    n = lim.get("max_changed_files", 5)
    if not isinstance(n, int) or n < 0:
        raise ValueError("config limits.max_changed_files は 0 以上の整数である必要があります。")
    return n


def main() -> int:
    _ensure_repo_root_on_sys_path()
    args = parse_args()
    session_dir = ensure_artifact_dirs(args.session_id)
    started_at = _iso_utc_now()
    stage = "init"
    ctx: Optional[SessionContext] = None

    try:
        stage = "loading"
        ctx = load_session_context(args.session_id)
        stage = "validating"
        validate_session_context(ctx)

        max_retries = (
            args.max_retries
            if args.max_retries is not None
            else ctx.runtime_config.get("limits", {}).get("max_retries", 3)
        )
        max_retries_config = int(max_retries) if isinstance(max_retries, int) else 0
        # v1 制約: リトライ実行は最大1回まで（指示生成＋Claude再投入の単発）
        mr = max_retries_config
        mr = min(mr, 1)
        max_retries_effective = mr
        max_changed_files = _max_changed_files_from_config(ctx.runtime_config)

        if args.dry_run:
            record_dry_run_git_warnings(session_dir, args.session_id)
        else:
            stage = "git_guard"
            log_stage_progress(args.session_id, stage, "ブランチ検証・sandbox へ切替")
            enforce_git_sandbox_branch(args.session_id)
            log_stage_progress(args.session_id, "git_guard", "完了 → 以降は API 呼び出し")

        spec_system, spec_user = build_prepared_spec_prompts(ctx)
        save_text(session_dir / "prompts" / "prepared_spec_system.txt", spec_system)
        save_text(session_dir / "prompts" / "prepared_spec_user.txt", spec_user)

        if args.dry_run:
            prepared_spec = build_dry_run_prepared_spec(ctx)
            impl_system, impl_user = build_implementation_prompts(prepared_spec, ctx)
            save_text(session_dir / "prompts" / "implementation_system.txt", impl_system)
            save_text(session_dir / "prompts" / "implementation_user.txt", impl_user)

            save_json(session_dir / "responses" / "prepared_spec.json", prepared_spec)
            impl_result = build_dry_run_implementation_result(ctx)
            save_json(session_dir / "responses" / "implementation_result.json", impl_result)

            check_results = build_skipped_checks_result()
            save_json(session_dir / "test_results" / "checks.json", check_results)

            persist_session_reports(
                session_dir,
                ctx,
                prepared_spec,
                impl_result,
                check_results,
                status="dry_run",
                dry_run=True,
                started_at=started_at,
                finished_at=_iso_utc_now(),
                retry_instruction=None,
                error_message=None,
                retry_control={
                    "retry_count": 0,
                    "max_retries": int(
                        ctx.runtime_config.get("limits", {}).get("max_retries", 0) or 0
                    ),
                    "retry_stopped_same_cause": False,
                    "retry_stopped_max_retries": False,
                },
            )
            print(f"[OK] dry-run completed: {args.session_id}")
            print(f"[INFO] artifacts saved under: {session_dir}")
            return 0

        stage = "prepared_spec"
        log_stage_progress(
            args.session_id, stage, "OpenAI（Builder契約反映の仕様整形）呼び出し開始"
        )
        prepared_spec = call_chatgpt_for_prepared_spec(ctx)
        save_json(session_dir / "responses" / "prepared_spec.json", prepared_spec)
        openai_usage = extract_api_usage(prepared_spec)  # usage 抽出（なければ空辞書）

        impl_system, impl_user = build_implementation_prompts(prepared_spec, ctx, None)
        save_text(session_dir / "prompts" / "implementation_system.txt", impl_system)
        save_text(session_dir / "prompts" / "implementation_user.txt", impl_user)

        # 実装＋チェック（初回）
        stage = "implementation"
        log_stage_progress(args.session_id, stage, "Claude（実装案）呼び出し開始")
        impl_result = call_claude_for_implementation(prepared_spec, ctx, None)
        claude_usage = extract_api_usage(impl_result)  # usage 抽出（なければ空辞書）
        claude_call_count = 1
        try:
            validate_impl_result(impl_result)
        except ValueError as guard_err:
            _persist_guard_failure_artifacts(session_dir, impl_result, guard_err, stage)
            raise
        save_json(session_dir / "responses" / "implementation_result.json", impl_result)

        stage = "patch_apply"
        log_stage_progress(
            args.session_id,
            stage,
            "patch 抽出→実ファイル適用→artifact 保存→実ファイル存在確認→git diff 再取得",
        )
        check_results = _apply_patch_validate_and_run_local_checks(
            session_dir=session_dir,
            ctx=ctx,
            impl_result=impl_result,
            prepared_spec=prepared_spec,
            max_changed_files=max_changed_files,
            skip_build=args.skip_build,
            session_id=args.session_id,
        )

        retry_instruction: Optional[Dict[str, Any]] = None
        retry_stopped_same_cause = False
        retry_stopped_max_retries = False
        retry_history: List[Dict[str, Any]] = []

        # retry_count は永続化（成功時は 0 に戻す）
        retry_count = _read_retry_state_count(session_dir)
        if check_results.get("success"):
            if retry_count != 0:
                retry_count = 0
                _write_retry_state_count(session_dir, retry_count)

        # 失敗時はリトライループへ
        while not check_results.get("success"):
            # 同一原因チェック（max_retries 上限到達時は retry_exhausted より優先して打ち切る）
            fp = _compute_retry_cause_fingerprint(check_results)
            prev_retry_path = session_dir / "responses" / "retry_instruction.json"
            prev_fp = None
            if prev_retry_path.is_file():
                try:
                    prev_fp = json.loads(prev_retry_path.read_text(encoding="utf-8")).get(
                        "cause_fingerprint"
                    )
                except json.JSONDecodeError:
                    prev_fp = None
            if prev_fp is not None and prev_fp == fp and retry_count >= max_retries_effective:
                retry_instruction = _merge_retry_instruction(
                    {}, ctx, prepared_spec, impl_result, check_results
                )
                retry_instruction["cause_fingerprint"] = fp
                retry_instruction["retry_skipped_same_cause"] = True
                retry_instruction["retry_count"] = retry_count
                retry_instruction["max_retries"] = max_retries_config
                retry_instruction["max_retries_effective"] = max_retries_effective
                save_json(prev_retry_path, retry_instruction)
                retry_stopped_same_cause = True
                break

            failure = classify_failure(check_results)
            decision = retry_loop(
                retry_history=retry_history,
                failure=failure,
                retry_count=retry_count,
                max_retries=max_retries_effective,
            )
            if not decision.get("should_retry"):
                reason = str(decision.get("stop_reason") or "retry_stopped")
                retry_instruction = build_retry_instruction(
                    ctx=ctx,
                    prepared_spec=prepared_spec,
                    failure=failure,
                    stop_reason=reason,
                )
                if reason == "max_retries_reached":
                    retry_stopped_max_retries = True
                    retry_instruction["retry_exhausted"] = True
                else:
                    retry_stopped_same_cause = True
                retry_instruction["retry_count"] = retry_count
                retry_instruction["max_retries"] = max_retries_config
                retry_instruction["max_retries_effective"] = max_retries_effective
                save_json(session_dir / "responses" / "retry_instruction.json", retry_instruction)
                break

            # retry 指示を生成（関数内で同一原因は抑止される）
            stage = "retry_instruction"
            log_stage_progress(
                args.session_id,
                stage,
                "チェック失敗 → OpenAI で Reviewer契約反映済みのリトライ指示を生成",
            )
            retry_instruction = call_chatgpt_for_retry_instruction(
                ctx, prepared_spec, impl_result, check_results
            )
            retry_instruction["failure_type"] = decision["failure_type"]
            retry_instruction["cause_summary"] = decision["cause_summary"]
            # 同一原因抑止の場合は retry_count を増やさない
            did_new = not bool(retry_instruction.get("retry_skipped_same_cause"))
            if did_new:
                retry_count = compute_next_retry_count(retry_count, True)
                _write_retry_state_count(session_dir, retry_count)
            else:
                retry_stopped_same_cause = True
                print("同一原因のためリトライ試行を停止")

            retry_instruction["retry_count"] = retry_count
            retry_instruction["max_retries"] = max_retries_config
            retry_instruction["max_retries_effective"] = max_retries_effective
            retry_history.append(
                {
                    "attempt": retry_count,
                    "failure_type": str(retry_instruction.get("failure_type") or ""),
                    "cause_summary": str(retry_instruction.get("cause_summary") or ""),
                }
            )
            save_json(session_dir / "responses" / "retry_instruction.json", retry_instruction)

            if retry_stopped_same_cause:
                break

            # Claude retry を実行
            stage = "implementation_retry"
            log_stage_progress(args.session_id, stage, f"retry_count={retry_count}")
            impl_result = call_claude_for_implementation(
                prepared_spec, ctx, retry_instruction
            )
            claude_usage = extract_api_usage(impl_result)  # retry usage を上書き更新
            claude_call_count += 1
            try:
                validate_impl_result(impl_result)
            except ValueError as guard_err:
                _persist_guard_failure_artifacts(session_dir, impl_result, guard_err, stage)
                raise
            save_json(
                session_dir / "responses" / "implementation_result.json",
                impl_result,
            )

            stage = "patch_apply"
            log_stage_progress(
                args.session_id,
                stage,
                "retry: patch 抽出→実ファイル適用→artifact 保存→実ファイル存在確認→git diff 再取得",
            )
            check_results = _apply_patch_validate_and_run_local_checks(
                session_dir=session_dir,
                ctx=ctx,
                impl_result=impl_result,
                prepared_spec=prepared_spec,
                max_changed_files=max_changed_files,
                skip_build=args.skip_build,
                session_id=args.session_id,
                retry_label="retry:",
            )

            if check_results.get("success"):
                retry_count = 0
                _write_retry_state_count(session_dir, retry_count)
                break

        overall_success = bool(check_results.get("success"))
        check_results["success"] = overall_success

        persist_session_reports(
            session_dir,
            ctx,
            prepared_spec,
            impl_result,
            check_results,
            status="success" if overall_success else "failed",
            dry_run=False,
            started_at=started_at,
            finished_at=_iso_utc_now(),
            retry_instruction=retry_instruction,
            error_message=None,
            retry_control={
                "retry_count": retry_count,
                "max_retries": max_retries_config,
                "retry_stopped_same_cause": retry_stopped_same_cause,
                "retry_stopped_max_retries": retry_stopped_max_retries,
            },
            api_usage={"openai": openai_usage, "claude": claude_usage},
            api_call_count={"openai": 1, "claude": claude_call_count},
        )

        print(f"[OK] session processed: {args.session_id}")
        print(f"[INFO] artifacts saved under: {session_dir}")

        return 0 if overall_success else 1

    except Exception as e:
        br = _git_branch_safe()
        save_error_log(
            session_dir,
            stage,
            e,
            args.session_id,
            branch=br,
        )
        print(
            f"[ERROR] stage={stage} session_id={args.session_id} branch={br!r} "
            f"error_type={type(e).__name__} message={e}",
            file=sys.stderr,
        )
        # 可能なら途中までのレポートを残す
        try:
            ps: Dict[str, Any] = {}
            ir: Dict[str, Any] = {}
            if (session_dir / "responses" / "prepared_spec.json").exists():
                ps = load_json(session_dir / "responses" / "prepared_spec.json")
            if (session_dir / "responses" / "implementation_result.json").exists():
                ir = load_json(session_dir / "responses" / "implementation_result.json")
            chk: Dict[str, Any] = {"success": False}
            if (session_dir / "test_results" / "checks.json").exists():
                chk = load_json(session_dir / "test_results" / "checks.json")

            persist_session_reports(
                session_dir,
                ctx,
                ps or {"objective": None},
                ir
                or {
                    "changed_files": [],
                    "implementation_summary": [],
                    "risks": [],
                    "open_issues": [],
                },
                chk,
                status="failed",
                dry_run=bool(args.dry_run),
                started_at=started_at,
                finished_at=_iso_utc_now(),
                retry_instruction=None,
                error_message=str(e),
                retry_control={
                    "retry_count": 0,
                    "max_retries": 0,
                    "retry_stopped_same_cause": False,
                    "retry_stopped_max_retries": False,
                },
                aborted_stage=stage,
            )
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
