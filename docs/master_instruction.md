# Master Instruction v1.2

## 1. プロジェクト名

軽量2AIオーケストレーター方式 開発基盤

---

## 2. 目的

本プロジェクトの目的は、GPT・Claude・Cursor の3層体制を前提として、
システム開発を **仕様駆動・検収前提・再試行可能** な形で進めるための
最小実行基盤を構築することである。

各ツールの役割は以下とする。

- GPT = 指揮・仕様整理・判定
- Claude = 分析・実装参謀
- Cursor = 実作業・実行・検証
- 人間 = 最終承認・優先順位判断・例外判断

特に、以下を実現する。

- 人間のコピペ中継を減らす
- 1セッション単位で安全に実装を進める
- テストや検証結果を成果物として保存する
- 差戻し可能な状態で開発を前進させる
- 正本仕様を1本に保つ

---

## 3. スコープ

### 含むもの

- セッション単位の仕様読込
- ChatGPT API による仕様整形
- Claude API による実装支援
- artifacts への成果物保存
- test / lint / typecheck / build の実行
- retry 制御
- session report 生成
- sandbox branch 前提の運用
- dry-run による安全な事前確認
- git_guard による main/master 直実行抑止
- error log の保存

### 含まないもの

- 本番自動反映
- 自動マージ
- 複数セッション並列実行
- 完全無人運用
- UIダッシュボード
- 高度な優先順位最適化
- 本番DB直接操作
- proposed_patch の自動本適用
- retry の高度最適化
- provider の大規模改修

---

## 4. 成功条件

本プロジェクトの v1 系成功条件は、以下の通りとする。

- `docs/sessions/session-01.json` を読み込める
- `docs/acceptance/session-01.yaml` を参照できる
- `artifacts/session-01/responses/prepared_spec.json` を保存できる
- `artifacts/session-01/responses/implementation_result.json` を保存できる
- `artifacts/session-01/reports/session_report.md` を保存できる
- 失敗時に `artifacts/session-01/logs/error_latest.json` を保存して終了できる
- main/master 上の通常実行を git_guard で停止できる
- `--dry-run` 実行時は、安全に成果物生成のみを行える

### 補足

- v1段階では、実API未接続でも骨組み成立を優先してよい
- v1.1段階では、dry-run / git_guard / error log の挙動が固定されていることを重視する

---

## 5. 基本原則

### 原則1: 正本は1本

現行仕様の正本は本ファイルと `global_rules.md` を基準とする。
セッション定義および検収基準は `docs/global_rules.md` に従う。

### 原則2: 1セッション1目的

セッションは常に1つの目的に限定する。

### 原則3: 役割固定

- GPT = 指揮・仕様整理・判定
- Claude = 分析・実装参謀
- Cursor = 実作業・実行・検証
- オーケストレーター = 実行制御
- 人間 = 最終承認・例外判断

この役割を越境させないことを前提とする。
特に、仕様決定は GPT、比較分析は Claude、実作業は Cursor を基準とする。

### 原則4: 構造化優先

自由文ではなく JSON / YAML / 明示的な項目定義を優先する。

### 原則5: 受入条件ベース

完了判定は「コードが書けた」ではなく「受入条件を満たしたか」で判断する。

### 原則6: 通常実行と dry-run を分ける

- 通常実行は実API呼び出し・検証・制御を伴う
- `--dry-run` は安全な事前確認と成果物確認のために使う
- 通常実行と dry-run の挙動差は仕様として固定する

### 原則7: main/master 保護

- 通常実行は main/master 上では禁止
- 実変更を伴う処理は sandbox branch 前提とする

---

## 6. フェーズ方針

### Phase 0

骨組み作成

- docs 作成
- session 雛形作成
- acceptance 雛形作成
- run_session.py 骨組み作成

### Phase 1

最小疎通

- session読込
- 仕様整形ダミー
- 実装結果ダミー
- artifacts 保存
- report 保存

### Phase 2

実API連携

- OpenAI API 接続
- Claude API 接続
- 応答保存
- retry最小実装

### Phase 3

Git安全弁 + ローカル検証連携

- git_guard
- sandbox branch 前提運用
- test
- lint
- typecheck
- build
- ログ保存

### Phase 4

適用制御と retry 強化

- diff summary
- patch適用前チェック
- proposed_patch 適用制御
- retry 再投入強化

---

## 7. dry-run 方針

`--dry-run` は、以下の目的で使用する。

- 正本入力が読めるかの確認
- artifacts 保存確認
- 実行フローの骨組み確認
- API未接続状態での事前確認

### dry-run のルール

- `--dry-run` 時は実API呼び出しを行わない
- `--dry-run` 時は patch適用を行わない
- `--dry-run` 時は Git変更を行わない
- `--dry-run` 時はダミー応答またはスタブ結果で成果物生成のみを行う
- `--dry-run` は main/master 上でも許可する
- dirty worktree の場合は警告ログを残してよい
- `--dry-run` の目的は「実装」ではなく「確認」である

---

## 8. 通常実行方針

通常実行は、実際のセッション進行を前提とする。

### 通常実行のルール

- main/master 上では禁止
- sandbox branch 前提
- dirty worktree の場合は停止
- 実API呼び出しを許可
- check結果に応じて成功 / 停止 / retry判定を行う

---

## 9. 禁止事項

- main/master への直接適用
- 仕様未確定のまま実装開始
- 1セッションで複数目的を扱うこと
- scope外の変更
- out_of_scope を無視すること
- 秘密情報をログへ保存すること
- 実装前に完了扱いすること
- archive せずに旧仕様を乱立させること
- dry-run を通常実装の代替として扱うこと
- proposed_patch を無検証で本適用すること

---

## 10. 開発物一覧

最低限必要なファイルは以下とする。

- `docs/master_instruction.md`
- `docs/global_rules.md`
- `docs/roadmap.yaml`
- `docs/sessions/session-01.json`
- `docs/acceptance/session-01.yaml`
- `orchestration/run_session.py`

必要に応じて後続で追加する。

- `orchestration/config.yaml`
- `orchestration/providers/openai_client.py`
- `orchestration/providers/claude_client.py`
- `requirements.txt`

加えて、運用上は以下を固定する。

- GPT は正本仕様と受入条件の整理に使う
- Claude は差分分析・実装方針・修正案の整理に使う
- Cursor はファイル編集・コマンド実行・検証・Git操作に使う

3ツールに同じ仕事をさせないことを原則とする。

---

## 11. 受入方針

v1.2 では、以下を満たせば合格候補とする。

- 骨組みが壊れていない
- session が読み込める
- acceptance が参照できる
- response / report が保存される
- エラー時の停止ができる
- `error_latest.json` に必要情報が残る
- 通常実行と dry-run の挙動が分離されている
- 次の patch適用前チェックと retry強化へ進める状態になっている

---

## 12. error log 方針

失敗時は、最低限以下を記録する。

- stage
- error_type
- message
- session_id
- branch
- timestamp_utc

### ログ保存方針

- 最新状態は `error_latest.json`
- 必要に応じて timestamp 付きエラーログも保存する
- ターミナル表示順が前後する可能性があるため、最終確認はログファイルを基準とする

---

## 13. 現在地

現時点で、以下は確認済みである。

- main 上の `--dry-run` は成功する
- main 上の通常実行は git_guard で停止する
- `error_latest.json` に session_id / branch / timestamp_utc が入る
- sandbox branch 上で次段検証へ進める前提がある

未実装範囲は以下とする。

- proposed_patch の実適用
- retry の Claude 再投入ループ
- provider の大改修
- 自動 merge

---

## 14. 次にやること

この文書を正本として固定した後、次の順で進める。

1. GPT・Claude・Cursor の3層体制を本プロジェクトの正式運用として固定する
2. `config.yaml` に実プロジェクトの test / lint / typecheck / build を反映する
3. `sandbox/session-01` 上で通常実行し、次の停止点を確認する
4. Cursor に渡す実装依頼文の型を固定する
5. Claude に渡す差分分析依頼文の型を固定する
6. その後に patch適用前チェック強化と retry 再投入の最小ループへ進む

---

## 15. 最終方針

本プロジェクトは、最初から完全自動化を目指さない。
v1.2 の目的は、壊さず・追跡可能で・再試行可能な最小司令塔を成立させることである。

したがって、優先順位は以下の通りとする。

1. 正本維持
2. 安全弁
3. 実行記録
4. 検証可能性
5. 自動化の拡張

また、本プロジェクトの運用は GPT・Claude・Cursor の3層分業を前提とする。

- GPT は正本維持と判定を担う
- Claude は実装参謀として差分分析と修正方針を担う
- Cursor は実際の作業実行と検証を担う

この分業を保つこと自体を、安全性と速度の両立条件とする。

### drift detector の位置付け

drift detector は、危険な session 定義を prepared_spec 前に停止する fail-fast 安全弁である。
session-123 時点では、既存 session との互換性維持のため temporary compatibility mode を採用する。
ただしこれは恒久仕様ではなく、default-on への移行を前提とした暫定運用とする。
global_rules.md の「drift detector v0.1 の適用方針」セクションと合わせて参照すること。

## drift detector 適用レベル

drift detector は段階的に適用レベルを引き上げる。

### v0.1

- opt-in モード

### v0.2

- 新規 session は default-on 候補とする
- 具体閾値は session-126 で決定する（session-126 で既存 session 群を実測し、実測後に確定する）

### v1.0

- 既存 session 群の準拠確認完了後、全 session に強制適用する

### 運用原則

- fail-fast を最優先とする
- drift を許容する運用は禁止する
- 実測前に default-on 移行判断を行わない

## legacy 凍結と新規厳格化

- 過去の全面修正ではなく、未来の品質固定を優先する
- 既存 session は legacy として凍結(書き換えない)
- 新規 session は canonical 前提で生成
- legacy は whitelist 管理とする
- 整理対象は現役 session のみとする(session-128 で選別)

### Phase ロードマップ

- Phase 1 (session-127): 運用方針固定 / legacy whitelist 初期版作成
- Phase 1b (session-127b): drift_detector.py への legacy 除外ロジック実装
- Phase 2 (session-128): 現役参照対象 session の選別
- Phase 3 (session-129 以降): 現役 session の canonical 整理

legacy の詳細運用ルールは global_rules.md の「new / legacy session 運用ルール」セクションを参照すること。

---

## M03: state handoff / resume

### 目的

途中失敗または中断時に、run_session.py と Master が共有可能な最小 state を保持し、安全に再開できる基盤を段階的に整備する。

### M03-A の範囲

- state handoff の責任境界定義
- 永続化 state JSON の最小 schema 定義
- resume 開始条件 / 停止条件 / 不整合時の扱い定義

### 責任境界

- **run_session.py**: session 内 stage 実行、checkpoint 記録、failure state 記録
- **Master**: session 間の継続判断、resume 要否判断、次 session 起票判断

### 原則

- retry と resume は別責務
- state 不整合時は安全側に倒して停止候補とする
- M03-A は docs-only とし、実装は後続 session (M03-B 以降) で行う

### M03-pre 補足方針 (session-132-pre)

- M03-C (resume 読込) は **docs/global_rules.md で定義された pipeline stage 正式リスト 10 値** を参照する
- checkpoint 記録用の `checkpoint_failure_type` は、session 検収・差戻し用の `failure_type` と **別管理** とする(両者を混同しない)
- `completed_stages` は resume 判定の **補助情報** であり、業務的な全完了履歴を意味しない。retry 早期 break 時には短縮されうる
- これら定義の本体は `docs/global_rules.md` にあり、`docs/master_instruction.md` はあくまで参照方針を示す

### M03-D 前提の補足方針 (session-133-pre)

M03-D では resume 実行整合性強化を実装するが、resume 例外規則・artifact 欠損時停止規則・retry 経路履歴表現・skip 可否の正式定義は **`docs/global_rules.md` を正本**とする。`docs/master_instruction.md` は当該方針の参照文書とし、`state.json` schema の既存互換性維持を前提とする。

- resume 実行整合性の定義本体は `global_rules.md` に置く。
- M03-D はその正本定義に従って実装を行う。
- `state.json` schema は既存互換を維持する。
- retry 経路の補助履歴は別責務として扱う。
- `loading` / `validating` 常時実行の原則を維持する。
- artifact 欠損時は fail-fast 停止を原則とする。
- skip 可否の正式定義は `global_rules.md` の stage 表を参照する。

---

## dashboard state writer 方針 (session-145a)

dashboard 向け `state.json` は、bootstrap 段階と恒久運用段階で責務を分離する。

- bootstrap は **手動配置** とする
- 恒久運用での正式更新は **後続 session の writer 実装** で行う
- session-145a は docs-only で方針固定のみを扱う
- session-145b は 10 プロジェクト一括ではなく **3〜4 プロジェクト先行** で進める
- `dashboard/viewer.js` と dashboard schema 契約はこの段階では変更しない
- `run_session.py` および Hook / MCP による自動更新接続は後続に分離する
