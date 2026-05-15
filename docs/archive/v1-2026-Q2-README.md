# v1 凍結アーカイブ — 2026-Q2

旧・軽量2AIオーケストレーター方式（v1）の境界定義。
物理退避は別セッションで実施する。本書は docs 上の打ち切り・凍結宣言の正本とする。

## 凍結日・対象

| 項目 | 内容 |
|---|---|
| 凍結日 | 2026-Q2（session `V2-Z0-FREEZE`） |
| 対象リポ | `/Users/kunihideyamane/AI_Team/軽量2AIオーケストレーター方式/` |
| 凍結マーク済み正本 | `docs/master_instruction.md` / `docs/global_rules.md` |
| v2 移行先 | phase `phase-v2-foundation` 以降のセッション群 |

## GPT 判定待ち 4件 — 打ち切り

以下は GPT 判定待ちのまま残存していた線。v2 移行に伴い **打ち切り（terminated）** とする。

| session_id | 状態 | 理由 |
|---|---|---|
| `session-178-pre` | **打ち切り** | VCER/RB 正本化は v1 線。v2 では新検収モデルへ再設計 |
| `session-172d` | **打ち切り** | 172d 実装線は v1 orchestrator 前提。v2 基盤確定後に必要なら再起票 |
| `session-179` | **打ち切り** | global_rules 昇格は v1 凍結対象外。v2 契約へ移行 |
| `T2` | **打ち切り** | 構造改修サブ線。T1–T4 全体凍結に含む（下記） |

## Role v2 線 — 凍結

Role v2（役割再定義・global_rules 連動）関連セッションは **凍結（frozen）** とする。再開時は v2 正本から新 session を起票する。

| session_id | 状態 |
|---|---|
| `session-179` | **凍結**（上記 GPT 待ち打ち切りと併記） |
| `session-180-pre` | **凍結** |
| `session-180` | **凍結** |
| `session-181-pre` | **凍結** |
| `session-181` | **凍結** |

## 構造改修線 T1–T4 — 凍結

v1 orchestrator の構造改修（queue / scheduler / runtime 分割等）を想定した線。

| 線 ID | 状態 | 備考 |
|---|---|---|
| `T1` | **凍結** | 構造改修 Phase 1 |
| `T2` | **凍結** | GPT 判定待ち 4件の 1 つとして打ち切り併記 |
| `T3` | **凍結** | 構造改修 Phase 3 |
| `T4` | **凍結** | 構造改修 Phase 4 |

## 新旧境界（参照のみ）

- **v1**: 本リポの `master_instruction.md` v1.2 / `global_rules.md` v1.2 / `orchestration/run_session.py` 中心の session 駆動
- **v2**: `phase-v2-foundation` — A03 ポータル案 A、事務所 LLM 接続、judge/observation 等新契約（別セッション所管）

## 操作禁止（本凍結の意味）

- v1 正本への追記・削除・昇格は禁止（凍結マークブロックのみ許可済み）
- 既存 `docs/sessions/` / `docs/acceptance/` 配下の履歴ファイルは改変しない
- `sealed stash@{0..6}` には触れない
- 物理 `archive/` 退避は **別セッション**
