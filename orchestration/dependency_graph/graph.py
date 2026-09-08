"""dependency graph ビルダー (session-194)。

session JSON の depends_on / blocks から read-only projection として
DependencyGraphResult を生成し、artifacts/session-190/dependency_graph/graph.json に出力する。
"""

import dataclasses
import json
import pathlib
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclasses.dataclass(frozen=True)
class DependencyGraphResult:
    success: bool
    failure_type: Optional[str]
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    errors: List[str]


def _load_session(session_id: str, repo_root: pathlib.Path) -> Dict[str, Any]:
    path = repo_root / "docs" / "sessions" / f"{session_id}.json"
    with open(str(path), encoding="utf-8") as f:
        return json.load(f)


def _detect_cycle(
    adj: Dict[str, List[str]],
    node_ids: List[str],
) -> Optional[str]:
    visited: Set[str] = set()

    def dfs(node: str, path: List[str], in_path: Set[str]) -> Optional[str]:
        if node in in_path:
            start = path.index(node)
            cycle: List[str] = path[start:] + [node]
            return " -> ".join(cycle)
        if node in visited:
            return None
        visited.add(node)
        path.append(node)
        in_path.add(node)
        for neighbor in sorted(adj.get(node, [])):
            result = dfs(neighbor, path, in_path)
            if result is not None:
                return result
        path.pop()
        in_path.remove(node)
        return None

    for node in sorted(node_ids):
        if node not in visited:
            result = dfs(node, [], set())
            if result is not None:
                return result
    return None


def build_dependency_graph(
    session_ids: List[str],
    repo_root: pathlib.Path,
) -> DependencyGraphResult:
    """session JSON を読み取り DependencyGraphResult を返す。成功時に artifact を書き出す。"""
    session_id_set: Set[str] = set(session_ids)

    sessions: Dict[str, Dict[str, Any]] = {}
    for sid in session_ids:
        sessions[sid] = _load_session(sid, repo_root)

    # depends_on / blocks から正規化 edge セットを構築
    # edge (src, tgt): tgt が src に depends_on している (src → tgt)
    edge_set: Set[Tuple[str, str]] = set()
    errors: List[str] = []

    for sid in session_ids:
        data = sessions[sid]
        depends_on: List[str] = data.get("depends_on", [])
        blocks: List[str] = data.get("blocks", [])

        # depends_on: sid が dep に依存 → edge (dep → sid)
        for dep in depends_on:
            if dep not in session_id_set:
                errors.append(
                    f"dangling reference: {sid} depends_on {dep}"
                    " which is not in session_ids"
                )
            else:
                edge_set.add((dep, sid))

        # blocks: sid が blk をブロック → blk が sid に依存 → edge (sid → blk)
        for blk in blocks:
            if blk in session_id_set:
                edge_set.add((sid, blk))

    if errors:
        return DependencyGraphResult(
            success=False,
            failure_type="spec_missing",
            nodes=[],
            edges=[],
            metadata={"count": len(session_ids)},
            errors=errors,
        )

    # cycle 検出
    adj: Dict[str, List[str]] = {}
    for src, tgt in edge_set:
        adj.setdefault(src, []).append(tgt)

    cycle_path = _detect_cycle(adj, session_ids)
    if cycle_path is not None:
        return DependencyGraphResult(
            success=False,
            failure_type="spec_missing",
            nodes=[],
            edges=[],
            metadata={"count": len(session_ids)},
            errors=[f"cycle detected: {cycle_path}"],
        )

    # nodes: session_id 昇順、ready = depends_on が空の場合 True
    sorted_ids: List[str] = sorted(session_ids)
    nodes: List[Dict[str, Any]] = []
    for sid in sorted_ids:
        depends_on_list: List[str] = sessions[sid].get("depends_on", [])
        nodes.append({"id": sid, "ready": len(depends_on_list) == 0})

    # edges: (source, target) 昇順でソートして deterministic に出力
    edges: List[Dict[str, Any]] = [
        {"source": src, "target": tgt, "type": "depends_on"}
        for src, tgt in sorted(edge_set)
    ]

    metadata: Dict[str, Any] = {"count": len(nodes)}

    # artifact 書き出し
    artifact_dir = repo_root / "artifacts" / "session-190" / "dependency_graph"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / "graph.json"

    artifact_data: Dict[str, Any] = {
        "edges": edges,
        "errors": [],
        "failure_type": None,
        "metadata": metadata,
        "nodes": nodes,
        "success": True,
    }
    with open(str(artifact_path), "w", encoding="utf-8") as f:
        json.dump(artifact_data, f, sort_keys=True, indent=2, ensure_ascii=False)

    return DependencyGraphResult(
        success=True,
        failure_type=None,
        nodes=nodes,
        edges=edges,
        metadata=metadata,
        errors=[],
    )
