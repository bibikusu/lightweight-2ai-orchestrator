#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml

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

    acceptance_path = DOCS_DIR / acceptance_ref
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


def _git_branch_safe() -> Optional[str]:
    """ブランチ名を返す。Git でない／取得失敗時は None。"""
    if not _is_git_repository():
        return None
    try:
        return get_current_git_branch()
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

    vp = validate_patch_files(normalized)
    if vp["status"] == "error":
        raise ValueError(vp.get("message", "scope violation"))

    if len(normalized) > max_changed_files:
        raise ValueError(
            f"changed_files が上限を超えています: {len(normalized)} > {max_changed_files}"
        )

    phrases = _collect_forbidden_phrases(session_data, prepared_spec)
    min_phrase_len = 3
    for path in normalized:
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


def build_prepared_spec_prompts(ctx: SessionContext) -> Tuple[str, str]:
    system_prompt = """You are a strict spec organizer.
Return only valid JSON.
Do not add markdown fences.
Do not expand scope.
Respect out_of_scope and constraints.
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
"""

    retry_block = ""
    if retry_instruction:
        retry_block = "\n\n[retry_instruction]\n" + json.dumps(
            retry_instruction, ensure_ascii=False, indent=2
        )

    user_prompt = f"""
session_id: {ctx.session_id}

[prepared_spec]
{json.dumps(prepared_spec, ensure_ascii=False, indent=2)}

[session_json]
{json.dumps(ctx.session_data, ensure_ascii=False, indent=2)}
{retry_block}

Return JSON with keys:
session_id
changed_files
implementation_summary
patch_status
risks
open_issues
proposed_patch
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
    return out


def resolve_canonical_failure_type(check_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    正本7値＋ no_failure を返す。
    priority は小さいほど高優先（0 は no_failure）。
    """
    cr = normalize_check_results_for_retry(check_results or {})

    # フラグ系（テストが成功でも scope_violation 等が立つことがある）
    flag_map = [
        ("scope_violation", "scope_violation", 5),
        ("regression_detected", "regression", 6),
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
    out: Dict[str, Any] = dict(raw or {})
    out["session_id"] = ctx.session_id
    out["failure_type"] = canonical["failure_type"]
    out["priority"] = canonical["priority"]

    if not isinstance(out.get("cause_summary"), str) or not str(out.get("cause_summary")).strip():
        out["cause_summary"] = f"failure_type={canonical['failure_type']} priority={canonical['priority']}"

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
        if not isinstance(tn, str) or not tn:
            continue
        passed = fn_results.get(tn)
        if passed is True:
            res = "pass"
        elif passed is False:
            res = "fail"
        else:
            res = "unknown"
        acceptance_results.append({"id": tid, "test": tn, "result": res})

    def _to_pf(v: Any) -> str:
        return "pass" if v == "passed" else ("fail" if v == "failed" else "skip")

    return {
        "session_id": ctx.session_id,
        "phase_id": (ctx.session_data or {}).get("phase_id"),
        "title": (ctx.session_data or {}).get("title"),
        "goal": (ctx.session_data or {}).get("goal"),
        "objective": prepared_spec.get("objective"),
        "changed_files": list(impl_result.get("changed_files", []) or []),
        "diff_summary": impl_result.get("diff_summary"),
        "test_result": _to_pf((checks.get("test") or {}).get("status")),
        "lint_result": _to_pf((checks.get("lint") or {}).get("status")),
        "typecheck_result": _to_pf((checks.get("typecheck") or {}).get("status")),
        "build_result": _to_pf((checks.get("build") or {}).get("status")),
        "risks": list(impl_result.get("risks", []) or []),
        "open_issues": list(impl_result.get("open_issues", []) or []),
        "acceptance_results": acceptance_results,
        "retry_count": int(rc.get("retry_count", 0) or 0),
        "max_retries": int(rc.get("max_retries", 0) or 0),
        "retry_stopped_same_cause": bool(rc.get("retry_stopped_same_cause", False)),
        "retry_stopped_max_retries": bool(rc.get("retry_stopped_max_retries", False)),
    }


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


def run_command(command: str) -> Dict[str, Any]:
    if not command.strip():
        return {
            "status": "skipped",
            "command": command,
            "returncode": None,
            "stdout": "",
            "stderr": "",
        }

    proc = subprocess.run(
        command,
        shell=True,
        cwd=ROOT_DIR,
        text=True,
        capture_output=True,
    )
    return {
        "status": "passed" if proc.returncode == 0 else "failed",
        "command": command,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
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

            report_md = generate_report(
                ctx=ctx,
                prepared_spec=prepared_spec,
                impl_result=impl_result,
                checks=check_results,
                retry_instruction=None,
            )
            save_text(session_dir / "reports" / "session_report.md", report_md)
            report_obj = build_session_report_record(
                ctx,
                prepared_spec,
                impl_result,
                check_results,
                retry_control={
                    "retry_count": 0,
                    "max_retries": int(ctx.runtime_config.get("limits", {}).get("max_retries", 0) or 0),
                    "retry_stopped_same_cause": False,
                    "retry_stopped_max_retries": False,
                },
            )
            save_json(session_dir / "reports" / "session_report.json", report_obj)
            print(f"[OK] dry-run completed: {args.session_id}")
            print(f"[INFO] artifacts saved under: {session_dir}")
            return 0

        stage = "prepared_spec"
        log_stage_progress(
            args.session_id, stage, "OpenAI（仕様整形）呼び出し開始"
        )
        prepared_spec = call_chatgpt_for_prepared_spec(ctx)
        save_json(session_dir / "responses" / "prepared_spec.json", prepared_spec)

        impl_system, impl_user = build_implementation_prompts(prepared_spec, ctx, None)
        save_text(session_dir / "prompts" / "implementation_system.txt", impl_system)
        save_text(session_dir / "prompts" / "implementation_user.txt", impl_user)

        # 実装＋チェック（初回）
        stage = "implementation"
        log_stage_progress(args.session_id, stage, "Claude（実装案）呼び出し開始")
        impl_result = call_claude_for_implementation(prepared_spec, ctx, None)
        save_json(session_dir / "responses" / "implementation_result.json", impl_result)

        stage = "patch_validation"
        log_stage_progress(args.session_id, stage, "changed_files 妥当性チェック")
        validate_changed_files_before_patch(
            impl_result,
            prepared_spec,
            ctx.session_data,
            max_changed_files,
        )

        stage = "checks"
        log_stage_progress(args.session_id, stage, "ローカル test/lint/typecheck/build")
        check_results = run_local_checks(ctx, skip_build=args.skip_build)
        save_json(session_dir / "test_results" / "checks.json", check_results)

        retry_instruction: Optional[Dict[str, Any]] = None
        retry_stopped_same_cause = False
        retry_stopped_max_retries = False

        # retry_count は永続化（成功時は 0 に戻す）
        retry_count = _read_retry_state_count(session_dir)
        if check_results.get("success"):
            if retry_count != 0:
                retry_count = 0
                _write_retry_state_count(session_dir, retry_count)

        # 失敗時はリトライループへ
        while not check_results.get("success"):
            # 同一原因で打ち切り（retry_count 上限より優先）
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

            # 上限到達で打ち切り（この場合 OpenAI は呼ばない）
            if retry_count >= max_retries and not (prev_fp and prev_fp == fp):
                retry_stopped_max_retries = True
                retry_instruction = _merge_retry_instruction(
                    {}, ctx, prepared_spec, impl_result, check_results
                )
                retry_instruction["retry_exhausted"] = True
                retry_instruction["cause_fingerprint"] = fp
                retry_instruction["retry_count"] = retry_count
                retry_instruction["max_retries"] = max_retries
                save_json(session_dir / "responses" / "retry_instruction.json", retry_instruction)
                break

            # retry 指示を生成（関数内で同一原因は抑止される）
            stage = "retry_instruction"
            log_stage_progress(args.session_id, stage, "チェック失敗 → OpenAI でリトライ指示")
            retry_instruction = call_chatgpt_for_retry_instruction(
                ctx, prepared_spec, impl_result, check_results
            )
            # 同一原因抑止の場合は retry_count を増やさない
            did_new = not bool(retry_instruction.get("retry_skipped_same_cause"))
            if did_new:
                retry_count = compute_next_retry_count(retry_count, True)
                _write_retry_state_count(session_dir, retry_count)
            else:
                retry_stopped_same_cause = True
                print("同一原因のためリトライ試行を停止")

            retry_instruction["retry_count"] = retry_count
            retry_instruction["max_retries"] = max_retries
            save_json(session_dir / "responses" / "retry_instruction.json", retry_instruction)

            if retry_stopped_same_cause:
                break

            # Claude retry を実行
            stage = "implementation_retry"
            log_stage_progress(args.session_id, stage, f"retry_count={retry_count}")
            impl_result = call_claude_for_implementation(
                prepared_spec, ctx, retry_instruction
            )
            save_json(
                session_dir / "responses" / "implementation_result.json",
                impl_result,
            )

            stage = "checks"
            log_stage_progress(args.session_id, stage, "ローカル checks 再実行")
            check_results = run_local_checks(ctx, skip_build=args.skip_build)
            save_json(session_dir / "test_results" / "checks.json", check_results)

            if check_results.get("success"):
                retry_count = 0
                _write_retry_state_count(session_dir, retry_count)
                break

        report_md = generate_report(
            ctx=ctx,
            prepared_spec=prepared_spec,
            impl_result=impl_result,
            checks=check_results,
            retry_instruction=retry_instruction,
        )
        save_text(session_dir / "reports" / "session_report.md", report_md)

        report_obj = build_session_report_record(
            ctx,
            prepared_spec,
            impl_result,
            check_results,
            retry_control={
                "retry_count": retry_count,
                "max_retries": max_retries,
                "retry_stopped_same_cause": retry_stopped_same_cause,
                "retry_stopped_max_retries": retry_stopped_max_retries,
            },
        )
        save_json(session_dir / "reports" / "session_report.json", report_obj)

        print(f"[OK] session processed: {args.session_id}")
        print(f"[INFO] artifacts saved under: {session_dir}")

        return 0 if check_results.get("success") else 1

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
            if ctx is not None and stage not in ("loading", "validating", "init"):
                ps: Dict[str, Any] = {}
                ir: Dict[str, Any] = {}
                if (session_dir / "responses" / "prepared_spec.json").exists():
                    ps = load_json(session_dir / "responses" / "prepared_spec.json")
                if (session_dir / "responses" / "implementation_result.json").exists():
                    ir = load_json(session_dir / "responses" / "implementation_result.json")
                if ps or ir:
                    chk: Dict[str, Any] = {"success": False}
                    if (session_dir / "test_results" / "checks.json").exists():
                        chk = load_json(session_dir / "test_results" / "checks.json")
                    report_md = generate_report(
                        ctx,
                        ps or {"objective": None},
                        ir or {"implementation_summary": [], "risks": [], "open_issues": []},
                        chk,
                        aborted_stage=stage,
                    )
                    save_text(session_dir / "reports" / "session_report.md", report_md)
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
