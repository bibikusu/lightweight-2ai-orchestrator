# next_action artifact contract v0（filesystem-first / relay 非必須）

## 0. 正本とスコープ

- **正本 JSON Schema**: `docs/schemas/next_action_v0.json`（variant / payload の構造不変量）。
- **本書のスコープ**: next_action を **成果物（artifact）としてどう保存・検証するか** の契約のみ。variant→shape の選択ロジックや runtime dispatch は **記述しない**（198-pre 等へ委譲）。
- **非スコープ**: `orchestration/**/*.py` の実装、`queue` / `scheduler` / `dashboard` / `provider` の挙動変更。

## 1. artifact relay は必須ではない

- next_action の検証・監査において、**チャットや別チャネル経由の artifact relay（本文の中継転送）を必須としない**。
- **primary audit path** は **リポジトリ上のファイルパス**（例: `docs/sessions/*.json`、`docs/acceptance/*.yaml`、本書、テンプレート）に対する **filesystem-first** の確認とする。
- 本契約および関連ドキュメントに **「artifact relay mandatory」「relay を必須とする」** 等の記述を置かない。

## 2. filesystem-first audit

- **保存先**: セッション定義は `docs/sessions/<session_id>.json`、受入は `docs/acceptance/<session_id>.yaml` を正とする（`acceptance_ref` でリンク）。
- **確認方法**: リポジトリルートを cwd とし、`test -f <path>` または `python tools/session_validate.py docs/sessions/<session_id>.json` 等の **短文・決定的** コマンドで存在と静的整合を確認する。
- **audit 対象**: `allowed_changes_detail` に列挙されたパスのみ（セッション外ファイルは対象外）。

## 3. Terminal short verification 契約

- Terminal 向け検証は **決定的な短文コマンド** に限定する（自由記述の長文判断を要求しない）。
- 具体テンプレート: `docs/templates/terminal_short_verification_v0.md`。
- 検証コマンドは **同一セッション内で固定**し、都度の解釈変更を禁止する。

## 4. GO / HOLD / FAIL routing semantics（決定的）

次の **3 値のみ** とし、**中間ラベルを置かない**。

| 判定 | 条件（すべて満たすこと） |
|------|-------------------------|
| **GO** | `allowed_changes_detail` に含まれるファイルのみが変更されている。`forbidden_changes` に該当するパスに変更がない。契約ドキュメント（本書・テンプレート）に反する記述がない。静的バリデーション（`tools/session_validate.py`）が exit 0。 |
| **HOLD** | 仕様判断・不足入力・レビュー待ちのいずれかで **マージ不能** だが、**禁止パスには触れていない** 状態。再提出または人間判断が必要。 |
| **FAIL** | `forbidden_changes` へ変更がある、または `allowed_changes_detail` 外のファイルが変更されている、または静的バリデーションが exit 非 0。 |

- 同一変更集合に対して **GO と FAIL を同時に満たさない**（排他的）。
- **曖昧な第 4 状態**（例: UNKNOWN を正とする分岐）は定義しない。

## 5. 参照

- `docs/schemas/next_action_v0.json`
- `docs/contracts/orchestration_contract_v0.md`（descriptive 文脈）
- `docs/templates/terminal_short_verification_v0.md`
