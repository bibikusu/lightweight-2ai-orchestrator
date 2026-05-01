# Project Command Center v2 UI 仕様 v0

## 1. 設計目的

Project Command Center v2 は、複数プロジェクトの目的・仕様書・session・実行モードを一目で理解し、迷わず次の session を設計できるようにするための司令塔 UI である。

目的は「情報を並べるUI」ではなく、「判断を強制するUI」を作ること。

v0 では read-only + session 生成支援に限定する。

## 2. UI 5 領域

### 2.1 Project Overview

#### 責務

各 project の目的・現在状態・詰まりを一目で把握する。

#### 入力

- docs/config/project_registry.json
- docs/sessions/*.json
- docs/acceptance/*.yaml
- docs/specs/*.md

#### 出力

- project 状態の表示
- 関連仕様書の表示
- 最新 session / 次 session 候補の表示

#### 表示項目

- project_id
- project_name
- purpose
- current_phase
- related_specs
- latest_session
- next_session_candidate
- deploy_risk
- db_touch_allowed
- night_batch_allowed
- recommended_execution_mode

#### 編集権限

v0 では read-only。

### 2.2 Mode Selector

#### 責務

execution_mode を選択する。

#### 入力

- project の deploy_risk
- session の scope
- session の out_of_scope
- acceptance の確定状態
- 人間の司令塔判断

#### 出力

- execution_mode: full_stack または fast_path

#### 表示要件

推奨モードと推奨理由を併記する。

例:

推奨: FULL_STACK
理由: 新規仕様 / UI設計 / deploy_risk=medium

推奨: FAST_PATH
理由: docs-only / JSON修復 / acceptance既存

#### 編集権限

人間が明示選択する。

v0 では自動判定しない。

### 2.3 Spec Builder

#### 責務

session JSON / acceptance YAML / 投入文を生成するための入力フォーム。

#### 入力項目

- session_id
- phase_id
- title
- goal
- scope
- out_of_scope
- constraints
- allowed_changes
- allowed_changes_detail
- forbidden_changes
- completion_criteria
- acceptance_criteria
- review_points
- execution_mode

#### 出力

- docs/sessions/*.json
- docs/acceptance/*.yaml
- GPT 投入文
- Claude 投入文
- ClaudeCode 投入文

#### 編集権限

人間が入力・承認する。

### 2.4 Session Generator

#### 責務

Spec Builder の入力から正規ファイルを生成する。

#### 入力

Spec Builder の入力データ。

#### 出力

- docs/sessions/<session_id>.json
- docs/acceptance/<session_id>.yaml

#### 必須検査

- required keys が存在する
- scope が空ではない
- out_of_scope が空ではない
- allowed_changes_detail がパス単位で定義されている
- acceptance_criteria と test_name が 1 対 1
- review_points の 4 番目が 検証十分性
- execution_mode が full_stack または fast_path

#### 編集権限

v0 では docs/sessions/*.json と docs/acceptance/*.yaml の作成支援のみ。

### 2.5 Execution Panel

#### 責務

GPT / Claude / ClaudeCode への投入文を表示する。

#### 入力

- session JSON
- acceptance YAML
- execution_mode
- project 情報
- allowed_changes_detail
- forbidden_changes

#### 出力

- GPT 用プロンプト
- Claude 用プロンプト
- ClaudeCode 用プロンプト

#### 表示要件

execution_mode に応じて投入順を変える。

full_stack:
GPT → Claude → ClaudeCode

fast_path:
GPT → ClaudeCode

#### 編集権限

v0 では read-only。実行は人間が外部ツールで行う。

## 3. MVP 範囲

v0 の MVP は以下に限定する。

- project 状態の read-only 表示
- execution_mode の人間選択
- session JSON 生成支援
- acceptance YAML 生成支援
- GPT / Claude / ClaudeCode 投入文生成支援

## 4. v0 でやらないこと

- UI 実装
- 自動実行
- queue 操作
- selector 実装変更
- project_registry.json 編集
- queue_policy.yaml 編集
- run_session.py 編集
- ClaudeCode hooks / MCP 設定変更
- 事務所 LLM 接続
- デプロイ

## 5. 編集権限マトリクス

| 対象 | v0 編集可否 |
|---|---|
| docs/sessions/*.json | 生成支援のみ可 |
| docs/acceptance/*.yaml | 生成支援のみ可 |
| docs/specs/*.md | 仕様作成のみ可 |
| docs/config/project_registry.json | 編集不可 |
| docs/config/queue_policy.yaml | 編集不可 |
| orchestration/run_session.py | 編集不可 |
| selector / queue / scheduler | 編集不可 |
| .claude/settings.json | 編集不可 |

## 6. future_extensions

以下は v2 以降の候補であり、v0 では実装しない。

### Roadmap Builder

Phase / project / 必要 session / 依存関係 / 状態を管理する画面。

### Session Queue View

queue_state を可視化する画面。

想定状態:
- pending
- ready
- running
- retry_waiting
- blocked_human
- completed
- failed

### Human Gate Panel

blocked_human の承認・差戻し・中止を行う画面。

### Local LLM Lane

事務所 LLM サーバーを軽量作業部隊として扱う補助レーン。
