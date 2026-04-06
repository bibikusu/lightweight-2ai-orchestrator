# Cluster Check Rules（Phase A 最小仕様）

## 1. 目的
- 本仕様は、A02_fina の Phase A における `cluster_check` の判定仕様を固定する。
- `cluster_check` は `blueprint` を受け取り、既存 blueprint 群との重複・衝突を判定し、`採用可 / 修正要 / 作成中止` を返す。
- 自動化は行わず、手動チェックのみを対象とする。

## 2. Responsibility Boundary（session-05 固定）
- 責務:
  - `blueprint` を入力として、既存 blueprint 群との重複・衝突を判定する。
  - 判定結果として `採用可 / 修正要 / 作成中止` の判断根拠を明確化する。
- 非責務:
  - 新規 blueprint の内容（タイトル、見出し、CTA）を新規設計しない。
  - HTML反映、メタ情報反映、JSON-LD選択は行わない（`docs/html_generation_spec.md` の責務）。
  - SEO本文生成ルールの定義は行わない。

## 3. 入力前提（判定開始条件）
`cluster_check` は、`docs/blueprint_spec.md` の完成条件を満たした新規 blueprint を受領した場合のみ判定を開始する。最低限、以下の必須受領項目が欠けていないこと。

- `search_intent`
- `target_keyword`
- `title`
- `description`
- `heading_structure`
- `cta`
- `slug`
- `jsonld_type`

いずれかが欠落している場合、判定は開始せず `修正要` として blueprint 側に差し戻す。

## 4. 判定観点（重複・衝突ルール）
既存 blueprint 群と比較し、以下を必須観点として判定する。

1. **重複（target_keyword）**
   - 同一 `target_keyword` は重複とする。
   - 表記ゆれ・語尾違い・同義に近い語は、他観点と組み合わせて実質重複を判定する。
2. **検索意図衝突（search_intent）**
   - 既存 blueprint と `search_intent` が同一、または意図が実質同等で差別化根拠がない場合は衝突とする。
3. **slug衝突（slug）**
   - 同一 `slug` は衝突とする。
   - 運用上同一URLと解釈される差分（大小文字差のみ、末尾記号差のみ等）も衝突とする。
4. **見出し構造の競合（heading_structure）**
   - `search_intent` が同一系統で、かつ `heading_structure` の主構成が同等の場合は競合とする。
5. **CTA目的衝突（cta）**
   - 既存 blueprint と同一導線・同一目的の `cta` で差別化根拠がない場合は衝突とする。

## 5. 判定結果の固定（3区分）
判定結果は以下の3区分で固定する。

1. **採用可**
   - 重複・衝突が確認されず、後続工程に渡してよい状態。
   - 後続アクション: `html_generation` へ引き渡す。
2. **修正要**
   - 入力欠落、または差別化可能な重複・衝突がある状態。
   - 後続アクション: blueprint 側へ差し戻し、修正後に再判定する。
3. **作成中止**
   - 本質的に既存 blueprint と重複・衝突し、修正で解消できない状態。
   - 後続アクション: 当該 blueprint の新規作成を中止し、別案検討に切り替える。

## 6. 差戻し条件（修正要）
以下のいずれかに該当する場合は `修正要` とする。

- 必須受領項目に欠落がある。
- `target_keyword` が類似し、`search_intent` または `heading_structure` の差別化根拠が不足している。
- `slug` が既存運用と衝突する形式になっている。
- `cta` が既存導線と実質同一で、目的差分が説明できない。

## 7. html_generation へ渡す条件（入力チェーン固定）
- 入力チェーンは `blueprint -> cluster_check -> html_generation` の順で固定する。
- `html_generation` に渡せるのは、`cluster_check` 判定結果が **採用可** の blueprint のみとする。
- `修正要` および `作成中止` は `html_generation` に渡してはならない。

## 8. review 観点
- 仕様一致: 判定観点に重複、検索意図衝突、slug衝突、見出し構造の競合、CTA目的衝突が含まれているか。
- 3区分固定: 判定結果が `採用可 / 修正要 / 作成中止` のみで定義されているか。
- 引き渡し整合: `採用可` のみが `html_generation` に渡る定義になっているか。
- 責務境界: blueprint 設計責務と html_generation 責務、SEO本文生成ルールが混入していないか。
