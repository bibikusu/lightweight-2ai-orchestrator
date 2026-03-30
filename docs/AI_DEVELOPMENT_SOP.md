# AI 開発標準作業手順（SOP）

## 目的

軽量2AIオーケストレーター方式において、**仕様駆動・検収前提・再試行可能**な開発を、毎回同じ順序で安全に進めるための標準手順を定義する。

正本は `docs/master_instruction.md` および `docs/global_rules.md` とする。本 SOP はチェックリストの適用順序を示す補助文書である。

## 適用順序

1. **開始前**: `docs/templates/preflight_prerequisite_checklist.md`
2. **ブランチ・Git**: `docs/templates/target_branch_prerequisite_checklist.md`
3. **実行中**: `docs/templates/session_execution_checklist.md`
4. **完了前・マージ前**: `docs/templates/session_review_checklist.md`
5. **main 統合**: `docs/merge_policy.md`

## 役割（再掲）

| 役割 | 主担当 |
|------|--------|
| 仕様整理・判定 | GPT |
| 分析・実装参謀 | Claude |
| 実装・コマンド・検証 | Cursor / 人間 |
| 実行制御 | オーケストレーター |
| 最終承認・例外 | 人間 |

## dry-run と通常実行

- `--dry-run`: 安全確認・疎通。実API・実適用に依存する検証は仕様に従いスキップまたは代替する。
- 通常実行: 実API・検証を伴う。**main/master 上では禁止**。sandbox ブランチ前提。

## 変更単位

- **1セッション1目的**。`scope` 内のみ実施し、`out_of_scope` は変更しない。
- commit では `session_id` を追跡可能にする（例: `session-35: ...`）。

## 参考パス

- セッション定義: `docs/sessions/`
- 受入条件: `docs/acceptance/`
- 成果物・ログ: `artifacts/<session_id>/`（プロジェクト構成に従う）
