# Master Instruction

## 1. プロジェクト名

軽量2AIオーケストレーター方式 開発基盤

---

## 2. 目的

本プロジェクトの目的は、ChatGPT と Claude を API 経由で連携させ、
システム開発を仕様駆動・検収前提・再試行可能な形で進めるための
最小実行基盤を構築することである。

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

### 含まないもの
- 本番自動反映
- 自動マージ
- 複数セッション並列実行
- 完全無人運用
- UIダッシュボード
- 高度な優先順位最適化
- 本番DB直接操作

---

## 4. 成功条件

本プロジェクトの最初の成功条件は、以下の通りとする。

1. `session-01.json` を読み込める
2. `acceptance/session-01.yaml` を参照できる
3. ChatGPT向け仕様整形結果を保存できる
4. Claude向け実装結果を保存できる
5. `artifacts/session-01/` に report を保存できる
6. 失敗時にエラー終了できる

v1段階では、実API未接続でも骨組み成立を優先してよい。

---

## 5. 基本原則

### 原則1: 正本は1本
現行仕様の正本は本ファイルと global_rules.md を基準とする。

### 原則2: 1セッション1目的
セッションは常に1つの目的に限定する。

### 原則3: 役割固定
- ChatGPT = 仕様整理
- Claude = 実装
- オーケストレーター = 制御
- 人間 = 承認

### 原則4: 構造化優先
自由文ではなく JSON / YAML / 明示的な項目定義を優先する。

### 原則5: 受入条件ベース
完了判定は「コードが書けた」ではなく「受入条件を満たしたか」で判断する。

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
ローカル検証連携
- test
- lint
- typecheck
- build
- ログ保存

### Phase 4
Git強化
- sandbox branch 自動作成
- diff summary
- patch適用制御

---

## 7. 禁止事項

- main/master への直接適用
- 仕様未確定のまま実装開始
- 1セッションで複数目的を扱うこと
- scope外の変更
- out_of_scope を無視すること
- 秘密情報をログへ保存すること
- 実装前に完了扱いすること
- archive せずに旧仕様を乱立させること

---

## 8. 開発物一覧

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

---

## 9. 受入方針

v1では、以下を満たせば合格候補とする。

- 骨組みが壊れていない
- session が読み込める
- acceptance が参照できる
- response / report が保存される
- エラー時の停止ができる
- 次の実API連携へ進める状態になっている

---

## 10. 次にやること

この文書を正本として固定した後、次の順で進める。

1. `roadmap.yaml` を作る
2. `run_session.py` をローカル配置する
3. `session-01.json` と `acceptance/session-01.yaml` を置く
4. ダミー実行で artifacts 出力を確認する
5. その後に OpenAI / Claude API 実接続へ進む
