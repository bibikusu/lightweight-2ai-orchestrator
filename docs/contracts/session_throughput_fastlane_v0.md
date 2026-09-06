# Session Throughput Fastlane Contract v0

## 1. Document Identity

- Document type: contract (operational throughput)
- Version: v0
- Status: canonical operational contract
- Related documents:
  - Session: [`docs/sessions/session-196-ops-pre.json`](../sessions/session-196-ops-pre.json)
  - Acceptance: [`docs/acceptance/session-196-ops-pre.yaml`](../acceptance/session-196-ops-pre.yaml)
  - Structural scaffold: [`docs/contracts/orchestration_contract_v0.md`](./orchestration_contract_v0.md)
  - Structural scaffold: [`docs/contracts/orchestration_enums_v0.md`](./orchestration_enums_v0.md)
  - Structural scaffold: [`docs/schemas/next_action_v0.json`](../schemas/next_action_v0.json)

## 2. Purpose

本契約は、chat 経由の長文 artifact transport によるボトルネックを排除し、session の作成・保存・検証を **filesystem-first / CLI-first** に固定するための運用契約である。

本契約は descriptive operational contract であり、runtime automation / queue / scheduler / Judge / PCC の具体化は含まない。

## 3. Chat Artifact Transport Prohibition

### 3.1 禁止事項

以下を **契約レベルで禁止** する。

| ID | 禁止内容 |
| --- | --- |
| CAT-01 | chat メッセージ本文に長文 artifact 全文を貼り付けて運搬すること |
| CAT-02 | chat 経由で session JSON / acceptance YAML / contract 全文を転送すること |
| CAT-03 | chat 経由で baseline hashes ファイル全文を転送すること |
| CAT-04 | chat 経由で diff 結果の長文 raw output を運搬すること |
| CAT-05 | TerminalF 向けプロンプトに長文 artifact 本文を埋め込むこと |

### 3.2 許可される chat 運搬物

chat 経由で運搬してよいのは **参照情報のみ** とする。

- repository ルートからの相対パス（例: `docs/sessions/session-196-ops-pre.json`）
- session_id / phase_id / acceptance_ref などの識別子
- CLI 実行コマンド（短い bash 一行）
- 検証結果の要約（pass / fail / failure_type / 1 行 cause_summary）
- ファイル存在確認・ハッシュ照合の成否（boolean または短い status 文字列）

### 3.3 正本の所在

artifact 本文の正本は **repository filesystem** に置く。chat は正本の複製先ではない。

## 4. TerminalF Discipline

### 4.1 TerminalF の定義

**TerminalF** は、bash シェル上で短いコマンドを実行する operational window label である（Section 9 参照）。

### 4.2 出力規律

TerminalF 向けの出力は **pure bash only** とする。

| 規律 | 内容 |
| --- | --- |
| TDF-01 | 出力は bash コマンドまたは bash スクリプト断片のみとする |
| TDF-02 | markdown を出力しない |
| TDF-03 | prose（説明文・段落テキスト）を出力しない |
| TDF-04 | raw header（`#` / `##` / YAML front matter 等）を出力しない |
| TDF-05 | 1 コマンドは短く保ち、長文パイプチェーンを chat に貼らない |
| TDF-06 | 検証結果は exit code と短い stdout/stderr のみを返す |

### 4.3 入力規律

| 規律 | 内容 |
| --- | --- |
| TDI-01 | 長文 artifact 本文を TerminalF プロンプトに貼らない |
| TDI-02 | ファイルパスと短いオプション引数のみを入力とする |
| TDI-03 | 本文の読み書きは filesystem 経由で行う |

## 5. GPT Responsibility Boundary

### 5.1 GPT の責務（本契約における境界）

**GPT**（canonical role）は以下を担当する。

| ID | 責務 |
| --- | --- |
| GPT-01 | session 起票 JSON の構造設計と 14-key 整合 |
| GPT-02 | acceptance criteria / completion criteria の定義 |
| GPT-03 | contract 文書の章立てと責務境界の記述 |
| GPT-04 | filesystem 上のパス参照の発行（chat にはパスのみ） |
| GPT-05 | 検証結果の要約と failure_type の判定補助 |

### 5.2 GPT の非責務（本契約における境界）

**GPT** は以下を **行わない**。

| ID | 非貴務 |
| --- | --- |
| GPT-N01 | artifact payload transport（長文本文の chat 経由運搬） |
| GPT-N02 | repository への直接ファイル書き込み（Human / ClaudeCode / Cursor の窓口に委譲） |
| GPT-N03 | bash コマンドの直接実行（TerminalF に委譲） |
| GPT-N04 | baseline hash の計算実行（TerminalF / 将来 CLI に委譲） |
| GPT-N05 | canonical role の再定義（session-179 scope） |

## 6. Operational Window Responsibilities

### 6.1 Canonical role と operational window label

本セクションの canonical role 名は session-179 で確立された **GPT / Claude Web / ClaudeCode / Cursor / Human** を指す。これらは Section 9 で定義する operational window label とは別概念である。

### 6.2 責務境界マトリクス

| Canonical role | 主窓口 | 作成 | 保存 | 検証 | chat 運搬 | filesystem 正本 |
| --- | --- | --- | --- | --- | --- | --- |
| GPT | — | session JSON / contract 草案 | パス参照発行のみ | 要約判定 | パス・識別子・要約のみ | 参照 |
| Claude Web | — | レビュー・起票補助 | なし | 目視レビュー | 短いフィードバックのみ | 参照 |
| ClaudeCode | ClaudeCodeE | 実装・編集 | repository 書き込み | test 実行 | パス・要約のみ | 正本 |
| Cursor | CursorD | 編集・diff | repository 書き込み | lint / test 起動 | パス・要約のみ | 正本 |
| Human | — | 承認・merge | git 操作 | 最終ゲート | 任意（長文禁止は全窓口共通） | 正本 |
| Terminal | TerminalF | なし | なし | bash 検証コマンド | pure bash のみ | 正本読取 |

### 6.3 Operational window label 一覧

| Label | 対応 canonical role | 窓口の役割 |
| --- | --- | --- |
| TerminalF | Terminal | pure bash / short command による filesystem 検証 |
| CursorD | Cursor | repository 編集・保存・IDE 内検証 |
| ClaudeCodeE | ClaudeCode | repository 編集・保存・CLI test 実行 |

### 6.4 共通規律

- 全 operational window に CAT-01〜CAT-05（Section 3）が適用される。
- 保存の正本は常に repository filesystem とする。
- chat はハンドオフの索引層であり、payload 運搬層ではない。

## 7. Session Package Structure

### 7.1 定義

**session package** とは、1 セッションの起票・検証・完了判定に必要な filesystem artifact の集合である。

### 7.2 必須メンバー

| メンバー | 標準パス | 役割 |
| --- | --- | --- |
| session JSON | `docs/sessions/{session_id}.json` | 14-key session 定義の正本 |
| acceptance YAML | `docs/acceptance/{session_id}.yaml` | AC / CC / change_guardrails の正本 |
| contract（該当時） | `docs/contracts/{contract_name}_v{N}.md` | 横断運用契約の正本 |
| baseline hashes（該当時） | `artifacts/{session_id}/baseline_hashes.txt` | non_regression 照合用ハッシュ一覧 |

### 7.3 整合規則

| ID | 規則 |
| --- | --- |
| SP-01 | session JSON の `acceptance_ref` は acceptance YAML パスと一致する |
| SP-02 | session JSON の `session_id` はファイル名の stem と一致する |
| SP-03 | acceptance YAML の `session_id` は session JSON と一致する |
| SP-04 | contract を参照する session は、contract パスを `allowed_changes_detail` または `scope` に明記する |
| SP-05 | baseline hashes は session package の補助メンバーであり、session JSON 14-key には含めない |
| SP-06 | session package の全文は filesystem から読み取り、chat に複製しない |

### 7.4 配置例（session-196-ops-pre）

```
docs/sessions/session-196-ops-pre.json
docs/acceptance/session-196-ops-pre.yaml
docs/contracts/session_throughput_fastlane_v0.md
```

## 8. CLI Candidates

> **本契約は CLI を実装しない。候補定義のみ。**
>
> 以下は将来の implementation session 向け責務定義であり、本契約 v0 時点では `tools/` 配下にファイルを作成しない。

### 8.1 tools/session_validate.py

| 項目 | 定義 |
| --- | --- |
| 責務 | session JSON の 14-key 存在検証、acceptance_ref パス存在検証、session_id とファイル名 stem の一致検証 |
| 入力 | `--session-id`、任意で `--repo-root` |
| 出力 | exit code 0（pass）/ 非 0（fail）、stdout に短い検証サマリ |
| 非責務 | contract 本文の意味論検証、runtime 実行 |

### 8.2 tools/diff_guard.py

| 項目 | 定義 |
| --- | --- |
| 責務 | `git diff --name-only` 結果が `allowed_changes` / `forbidden_changes` に適合するか検証 |
| 入力 | `--allowed`（パスリスト）、任意で `--forbidden`（パスリスト）、`--repo-root` |
| 出力 | exit code 0（範囲内）/ 非 0（範囲外差分検出）、stdout に違反パス一覧（短形式） |
| 非責務 | diff 内容の意味論レビュー、自動 revert |

### 8.3 tools/hash_guard.py

| 項目 | 定義 |
| --- | --- |
| 責務 | 指定ファイル群の SHA-256 を計算し、baseline_hashes.txt または引数指定ハッシュと照合 |
| 入力 | `--baseline`（baseline_hashes.txt パス）または `--expected-sha256`、対象ファイルパスリスト |
| 出力 | exit code 0（一致）/ 非 0（不一致）、stdout に不一致ファイル名のみ |
| 非責務 | baseline の自動更新、chat へのハッシュ全文出力 |

### 8.4 tools/session_package.py

| 項目 | 定義 |
| --- | --- |
| 責務 | session package（Section 7）の必須メンバー存在確認を一括実行し、欠落を報告 |
| 入力 | `--session-id`、`--repo-root` |
| 出力 | exit code 0（package 完全）/ 非 0（欠落あり）、stdout に欠落メンバー名のみ |
| 非責務 | package の自動生成、session JSON の自動起票 |

### 8.5 実装境界の明示

- 本契約 v0 は上記 4 CLI の **候補定義のみ** を固定する。
- `tools/session_validate.py` / `tools/diff_guard.py` / `tools/hash_guard.py` / `tools/session_package.py` のいずれも **本契約では作成しない**。
- CLI 実装は別 session の scope とする。

## 9. Operational Window Labels vs Canonical Roles

### 9.1 非同一性の宣言

**TerminalF / CursorD / ClaudeCodeE** は operational window label である。これらは canonical role（GPT / Claude Web / ClaudeCode / Cursor / Human）の **再定義ではない**。

| Operational window label | 対応する canonical role | 再定義ではない理由 |
| --- | --- | --- |
| TerminalF | Terminal | Terminal 窓口における pure bash 運用規律のラベル |
| CursorD | Cursor | Cursor IDE 窓口における編集・保存運用のラベル |
| ClaudeCodeE | ClaudeCode | Claude Code 窓口における編集・test 実行運用のラベル |

### 9.2 禁止事項

| ID | 禁止内容 |
| --- | --- |
| OWL-01 | operational window label で canonical role 名を置換すること |
| OWL-02 | Role v2（session-179）の canonical role 定義を変更すること |
| OWL-03 | operational window label を schema enum として canonical scaffold に追加すること（本契約 v0 scope 外） |

### 9.3 参照関係

- canonical role の正本は session-179 scope に属する。
- 本契約は operational throughput のための **窓口ラベル** を追加定義するのみである。
- `docs/contracts/orchestration_contract_v0.md` および `docs/contracts/orchestration_enums_v0.md` は本契約 v0 では変更しない。

## 10. Non-Statements (explicit boundary)

本契約は以下を **記述しない**。

- queue / scheduler の実装仕様
- Judge / PCC の runtime 振る舞い
- auto-merge 手順
- CLI 4 件の実装コード
- `docs/schemas/next_action_v0.json` の変更
- Role v2 canonical role の変更

## 11. Versioning

- 本契約は version `v0`。
- 後続バージョンは CLI 実装完了後に exit code 仕様・引数 schema を追加してよいが、Section 3（chat transport 禁止）と Section 9（label / role 非同一性）は後方互換で維持する。
