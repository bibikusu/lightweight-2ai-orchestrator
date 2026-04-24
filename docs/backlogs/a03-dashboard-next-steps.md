# A03 Dashboard v1 次工程 BACKLOG

登録日: 2026-04-24  
対象プロジェクト: A03_mane_bikusu  
前提: session-a03-dashboard-v1（docs-only 受入条件定義）完了後

---

## BACKLOG-A03-ID-MIGRATION-001

**タイトル**: data/projects.json の ID 体系を registry 正本 ID に移行する

**内容**:  
A03 の `data/projects.json` 内の `id` フィールドを、
`docs/config/project_registry.json` の正本 `project_id` に揃える。

**目的**:  
A03 dashboard が orchestrator 正本と同じ 10 プロジェクト ID で
表示・検証できるようにする。

**禁止事項**:
- `docs/config/project_registry.json` 側の変更は禁止（正本は触らない）
- `data/projects.json` 側を寄せる
- API 連携・DB 導入・実装 session の先行着手

**依存関係**:
- なし（本 BACKLOG が BACKLOG-A03-IMPL-001 の前提）

**設計判断ポイント（参謀メモ）**:

| # | 問い | 推奨方針 |
|---|------|---------|
| Q1 | 移行方式 | BACKLOG-A03-GENERATOR-001 と統合し、`generate_projects_json.py` 実行で生成する方式を優先。手動書き換えは最終手段。 |
| Q2 | 旧 ID 互換性 | localStorage に旧 ID (`A01_orchestrator` 等) が保持されている可能性あり。localStorage 対応は v1-impl session に送り、本 session は `projects.json` ファイル本体のみ対象とする。 |
| Q3 | 移行前後検証 | 移行前に現 ID 一覧を保存。移行後は registry 正本 ID との一致確認。AC は「SHA-256 差分はあるが ID 体系が registry 一致」で検証。 |

**ステータス**: BACKLOG

---

## BACKLOG-A03-GENERATOR-001

**タイトル**: registry → data/projects.json 生成スクリプトの検討

**内容**:  
`docs/config/project_registry.json` から A03 用 `data/projects.json` を生成する
`scripts/generate_projects_json.py` を検討・実装する。

**目的**:  
手動編集運用を減らし、10 プロジェクト管理の同期ズレを防ぐ。

**備考**:
- cron / 自動更新は対象外。まずは手動実行スクリプト。
- BACKLOG-A03-ID-MIGRATION-001 と統合して 1 session にまとめることを推奨。

**禁止事項**:
- cron・自動実行の実装
- `docs/config/project_registry.json` の変更
- `src/` / `dist/` / `orchestration/` の変更

**依存関係**:
- BACKLOG-A03-ID-MIGRATION-001 と並行または統合して実施

**ステータス**: BACKLOG

---

## BACKLOG-A03-IMPL-001

**タイトル**: session-a03-dashboard-v1-impl — readonly dashboard 表示改善・build・rsync

**内容**:  
`session-a03-dashboard-v1-impl` として、A03 readonly dashboard の
表示改善・`npm run build`・rsync による本番反映を行う実装 session。

**目的**:  
docs-only で確定した受入条件（AC/CC）を満たす実装を完了させ、
`mane.bikusu.net` に v1 を公開する。

**前提条件**:
- **BACKLOG-A03-ID-MIGRATION-001 完了後に着手すること**
- `data/projects.json` の ID が registry 正本 ID に一致している状態であること
- `session-a03-dashboard-v1`（docs-only）の受入が完了していること

**禁止事項**:
- API 連携
- 自然言語指示インターフェースの実装
- session 生成 UI
- pass/fail 記録 UI
- DB 導入
- `run_session.py` / `orchestration/` の変更
- `docs/config/project_registry.json` の変更

**依存関係**:
- 前提: BACKLOG-A03-ID-MIGRATION-001 完了

**ステータス**: ~~BACKLOG（着手ブロック中）~~ → **READY（着手可能）**

**ブロック解除記録**:

| 項目 | 値 |
|---|---|
| 解除日 | 2026-04-24 |
| 解除理由 | BACKLOG-A03-ID-MIGRATION-001 PASS クローズ |
| orchestrator commit | `34a0d2d` |
| A03 commit | `f699db2` |
| PASS log commit | `44421e1` |
| 次の想定 session_id | `session-a03-dashboard-v1-impl-001` |

---

## 起票順序（推奨）

```
session-a03-dashboard-v1（docs-only）完了
        ↓
BACKLOG-A03-ID-MIGRATION-001
BACKLOG-A03-GENERATOR-001  ← 統合推奨
        ↓
BACKLOG-A03-IMPL-001
```
