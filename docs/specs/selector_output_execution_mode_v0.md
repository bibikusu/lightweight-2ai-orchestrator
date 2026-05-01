# selector 出力 I/O 契約 v1 — execution_mode 追加版 (docs-only)

## 1. 目的

本文書は、session-152 で正本化された next-session selector の出力契約に `execution_mode` フィールドを追加する I/O 契約 v1 を定義するものである。

selector が推薦する次 session の情報として「どの AI 投入パターンで実行すべきか」を出力に含めることで、人間 / GPT 司令塔が投入文を組み立てる際に必要な情報を一元的に取得できるようにする。

本文書は docs-only の契約定義のみを扱う。Python 実装・CLI・テストコードは session-156 以降の対象であり、本文書には含めない。

## 2. 正本参照

本文書は以下の正本文書に依存する。これらを改変せず参照のみ行う。

| 正本 | 参照箇所 |
|---|---|
| session-152（next-session selector I/O 契約） | 入力構造 / next_session_candidate / human_required_flag / stop_reason / 自動実行禁止 |
| session-160-pre（execution_mode v0 仕様） | execution_mode の enum 値・優先順位・fallback ポリシー |
| session-153（queue_policy_schema_v0） | queue_policy.yaml の load→validate→apply 契約 |

**enum の再定義禁止**: execution_mode の enum 値は session-160-pre を正本とし、stop_reason の enum 値は session-152 を正本とする。本文書ではいずれも再定義しない。

## 3. selector 出力の必須キー（v1）

selector は次の 4 キーを必ず返す。

| キー | 型 | 起源 | 概要 |
|---|---|---|---|
| `next_session_candidate` | string \| null | session-152 既定 | 推薦する次 session の session_id。候補なしの場合は null |
| `human_required_flag` | boolean | session-152 既定 | 推薦 session が human approval 必須かどうか |
| `stop_reason` | string \| null | session-152 既定（enum は session-152 を正本参照） | 候補なし時の停止理由。候補あり時は null |
| `execution_mode` | string | 本文書で追加（enum は session-160-pre を正本参照） | 推薦 session の実行モード |

### 3.1 next_session_candidate

session-152 で定義済みのキー。定義の正本は session-152 にある。

- 型: string または null
- 値: 推薦 session の session_id 文字列。候補が存在しない場合は null

### 3.2 human_required_flag

session-152 で定義済みのキー。定義の正本は session-152 にある。

- 型: boolean
- 値: 推薦 session の human_required フィールドの値をそのまま返す

### 3.3 stop_reason

session-152 で定義済みのキー。enum 値の正本は session-152 にある。

- 型: string または null
- 値: 候補 session が存在する場合は null。候補なし時は session-152 で正本定義された enum 値を返す
- enum 値の参照先: session-152

本文書では stop_reason の enum 値を再定義しない。

### 3.4 execution_mode（本文書で追加）

本文書で selector 出力に新たに追加するキー。

- 型: string
- 値: session-160-pre で正本定義された enum 値（full_stack または fast_path）
- enum 値の参照先: session-160-pre
- 必須: yes（next_session_candidate が null のとき、execution_mode の値は不定とし null を許容する）

本文書では execution_mode の enum 値を再定義しない。

## 4. execution_mode の決定ルール（抽象契約）

selector が execution_mode を決定する際の抽象契約を以下に定義する。

### 4.1 優先順位

1. 推薦 session の session.json に execution_mode フィールドが存在する場合、その値を採用する
2. session.json に execution_mode が存在しない場合、project_registry.json の project default を参照する

優先順位の正本定義は session-160-pre にある。selector はこの優先順位に従って値を読み取るにとどまる。

### 4.2 v0 の制約

v0 では selector が execution_mode を自動判定しない。

禁止:
- scope / title / phase_id 等の内容分析による execution_mode の自動推定
- fast_path → full_stack への同一 session 内自動昇格

許可:
- session.json の execution_mode フィールドを読み取り、そのまま output に含める
- session.json に execution_mode がない場合に project default を読み取り output に含める

自動判定ロジックは v1 以降の検討事項である。

### 4.3 許容値

execution_mode の許容値は session-160-pre の enum 定義に従う。本文書では許容値を固定値として列挙しない。selector の実装は session-160-pre の enum 定義を参照して validate すること。

## 5. human_required_flag と execution_mode の整合性条件

human_required_flag と execution_mode は矛盾を許さない。以下の整合性条件を満たすこと。

### 5.1 整合性条件

| human_required_flag | execution_mode | 可否 |
|---|---|---|
| false | full_stack | 許可 |
| false | fast_path | 許可 |
| true | full_stack | 許可（human 確認後に実行） |
| true | fast_path | **警告**（human 確認が必要な session に高速モードを適用することを明示的に許可する場合のみ） |

### 5.2 警告条件の扱い

`human_required_flag = true` かつ `execution_mode = fast_path` の組み合わせは、自動拒否ではなく警告として扱う。

理由: human 確認の必要性と実行速度は独立した軸であり、単純に矛盾しない場合がある。ただし人間 / GPT 司令塔はこの組み合わせを明示的に認識・承認すること。

### 5.3 null 状態の扱い

next_session_candidate が null（候補なし）のとき:

- human_required_flag: false を返す（候補なしのため）
- stop_reason: session-152 正本の enum 値のいずれかを返す
- execution_mode: null を許容する（実行対象が存在しないため）

## 6. 本文書の制約

- docs-only: Python 実装・CLI・テストコード・設定ファイルを含まない
- enum 再定義禁止: execution_mode の enum 値は session-160-pre 正本、stop_reason の enum 値は session-152 正本
- 実装は後続 session の対象:
  - selector Python 実装への execution_mode 組み込みは session-156 以降
  - queue_policy.yaml 実ファイルへの反映は session-154 以降
  - execution_mode 自動判定の実装は v1 以降

## 7. 想定 selector 出力形式（参考）

実装のない参考形式。キー構造の意図を示すための例示であり、実装を拘束しない。

```json
{
  "next_session_candidate": "session-XXX",
  "human_required_flag": false,
  "stop_reason": null,
  "execution_mode": "fast_path"
}
```

候補なし時:

```json
{
  "next_session_candidate": null,
  "human_required_flag": false,
  "stop_reason": "<session-152 正本の enum 値>",
  "execution_mode": null
}
```

## 8. 後続 session 候補

| session 候補 | 内容 |
|---|---|
| session-156 系 | selector Python 実装に execution_mode 読み取りを組み込む |
| session-162 系 | Project Command Center v2 UI に execution_mode 表示を組み込む |
| session-163 系 | 事務所 LLM サーバーとの接続 PoC（ω-1 ハイブリッド運用） |
