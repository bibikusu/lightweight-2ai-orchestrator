# AI Development SOP

## 目的
軽量2AIオーケストレーター方式において、セッション実行前・実行中・検収時の運用を標準化し、前提不足・スコープ逸脱・検収ブレを防ぐ。

---

## 1. 適用範囲
この SOP は、docs-only セッション、tests-only セッション、code セッションを含むすべての session execution に適用する。

---

## 2. 運用原則

- 1セッション1目的
- allowed_changes 外の変更は禁止
- prerequisite 不足を同一セッションで補わない
- acceptance_criteria 未達は完了扱いしない
- 事実と解釈を分けて記録する
- target branch と sandbox branch の前提差分を混同しない

---

## 3. 実行前チェック

実装前に必ず以下を確認する。

1. `docs/templates/preflight_prerequisite_checklist.md`
2. `docs/templates/target_branch_prerequisite_checklist.md`（merge / cherry-pick 前提がある場合）
3. session JSON
4. acceptance YAML

### 必須確認項目
- prerequisite file が tracked か
- prerequisite file が存在するか
- allowed_changes が実リポジトリと一致するか
- 既存テスト重複がないか
- working tree に scope 外変更がないか

---

## 4. 実行中チェック

実行中は、`docs/templates/session_execution_checklist.md` を使う。

### 停止条件
- allowed_changes 外修正が必要になった
- prerequisite 不足が見つかった
- 既存テストと重複が発覚した
- 複数目的に広がった
- full validation sequence が通らない

停止した場合は、同一セッションで無理に補わず、必要に応じて別セッションへ切り出す。

---

## 5. 検収チェック

検収時は、`docs/templates/session_review_checklist.md` を使う。

### 判定観点
- 仕様一致
- 変更範囲遵守
- 副作用なし
- 実装過不足なし

### failure_type
最初に該当したものを 1 つだけ採用する。

1. build_error
2. import_error
3. type_mismatch
4. test_failure
5. scope_violation
6. regression
7. spec_missing
8. not_applicable

---

## 6. target branch 確認

sandbox で成功しても、target branch に prerequisite artifact がなければ main 統合時に失敗することがある。
そのため merge / cherry-pick 前には必ず target branch 上で prerequisite artifact の tracked / existence を確認する。

---

## 7. docs-only セッションの扱い

docs-only セッションでは、runtime / tests / workflows を変更しない。
成果物本文を直接生成し、手動保存 → commit で進めることを優先する。

---

## 8. code / tests-only セッションの扱い

code / tests-only セッションでは、Cursor 実行を基本とする。
ただし pre-flight を完了してから着手し、前提不足があれば停止する。

---

## 9. 記録

各セッションで最低限残すもの：

- changed_files
- validation results
- acceptance_results
- risks
- open_issues
- final_judgement

---

## 10. 補足

この SOP は、Phase6 / Phase7 で得られた運用教訓をもとに作成した。
今後、運用で再発する failure pattern が見つかった場合は、新セッションでテンプレまたは SOP を更新する。
