#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
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


def save_error_log(
    session_dir: Path,
    stage: str,
    error: Union[BaseException, str],
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """失敗時に artifacts/session-XX/logs/error.json を保存する。"""
    if isinstance(error, BaseException):
        error_type = type(error).__name__
        message = str(error)
    else:
        error_type = "Error"
        message = str(error)
    payload: Dict[str, Any] = {
        "stage": stage,
        "error_type": error_type,
        "message": message,
    }
    if details:
        payload["details"] = details
    save_json(session_dir / "logs" / "error.json", payload)


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
) -> Tuple[str, str]:
    system_prompt = """You are a strict implementation assistant.
Return only valid JSON.
Do not add markdown fences.
Do not expand scope.
If implementation is not possible, explain in JSON.
"""

    user_prompt = f"""
session_id: {ctx.session_id}

[prepared_spec]
{json.dumps(prepared_spec, ensure_ascii=False, indent=2)}

[session_json]
{json.dumps(ctx.session_data, ensure_ascii=False, indent=2)}

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
"""

    user_prompt = f"""
session_id: {ctx.session_id}

[prepared_spec]
{json.dumps(prepared_spec, ensure_ascii=False, indent=2)}

[implementation_result]
{json.dumps(impl_result, ensure_ascii=False, indent=2)}

[check_results]
{json.dumps(check_results, ensure_ascii=False, indent=2)}

Return JSON with keys:
session_id
failure_type
priority
cause_summary
fix_instructions
do_not_change
"""
    return system_prompt, user_prompt


def call_chatgpt_for_prepared_spec(ctx: SessionContext) -> Dict[str, Any]:
    from providers.openai_client import OpenAIClientConfig, OpenAIClientWrapper

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
    from providers.openai_client import OpenAIClientConfig, OpenAIClientWrapper

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
    return client.request_retry_instruction(system_prompt, user_prompt)


def call_claude_for_implementation(
    prepared_spec: Dict[str, Any],
    ctx: SessionContext,
) -> Dict[str, Any]:
    from providers.claude_client import ClaudeClientConfig, ClaudeClientWrapper

    claude_cfg = ctx.runtime_config["providers"]["claude"]
    client = ClaudeClientWrapper(
        ClaudeClientConfig(
            model=claude_cfg["model"],
            timeout_sec=claude_cfg.get("timeout_sec", 180),
            max_output_tokens=claude_cfg.get("max_output_tokens", 6000),
        )
    )
    system_prompt, user_prompt = build_implementation_prompts(prepared_spec, ctx)
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

        if not args.dry_run:
            stage = "git_guard"
            enforce_git_sandbox_branch(args.session_id)

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
            print(f"[OK] dry-run completed: {args.session_id}")
            print(f"[INFO] artifacts saved under: {session_dir}")
            return 0

        stage = "prepared_spec"
        prepared_spec = call_chatgpt_for_prepared_spec(ctx)
        save_json(session_dir / "responses" / "prepared_spec.json", prepared_spec)

        impl_system, impl_user = build_implementation_prompts(prepared_spec, ctx)
        save_text(session_dir / "prompts" / "implementation_system.txt", impl_system)
        save_text(session_dir / "prompts" / "implementation_user.txt", impl_user)

        stage = "implementation"
        impl_result = call_claude_for_implementation(prepared_spec, ctx)
        save_json(session_dir / "responses" / "implementation_result.json", impl_result)

        stage = "patch_validation"
        validate_changed_files_before_patch(
            impl_result,
            prepared_spec,
            ctx.session_data,
            max_changed_files,
        )

        stage = "checks"
        check_results = run_local_checks(ctx, skip_build=args.skip_build)
        save_json(session_dir / "test_results" / "checks.json", check_results)

        retry_instruction = None

        if not check_results.get("success"):
            stage = "retry_instruction"
            if max_retries > 0:
                retry_instruction = call_chatgpt_for_retry_instruction(
                    ctx, prepared_spec, impl_result, check_results
                )
                save_json(
                    session_dir / "responses" / "retry_instruction.json",
                    retry_instruction,
                )

        report_md = generate_report(
            ctx=ctx,
            prepared_spec=prepared_spec,
            impl_result=impl_result,
            checks=check_results,
            retry_instruction=retry_instruction,
        )
        save_text(session_dir / "reports" / "session_report.md", report_md)

        print(f"[OK] session processed: {args.session_id}")
        print(f"[INFO] artifacts saved under: {session_dir}")

        return 0 if check_results.get("success") else 1

    except Exception as e:
        save_error_log(session_dir, stage, e)
        print(f"[ERROR] [{stage}] {e}", file=sys.stderr)
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
