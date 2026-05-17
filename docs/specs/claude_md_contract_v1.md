# CLAUDE.md 契約仕様 v1 (claude_md_contract_v1)

- **session**: session-203-pre
- **type**: docs-only (契約仕様のみ。CLAUDE.md 実体の物理配置は本セッションでは禁止)
- **status**: frozen-spec
- **作成日**: 2026-05-17
- **正本種別**: ClaudeCode 向け運用契約 (人間司令塔向け正本は `docs/master_instruction.md`)
- **後方参照**: `docs/sessions/session-203-pre.json` / `docs/acceptance/session-203-pre.yaml`
- **forward 参照**: `path_mode_policy_v1.md` (session-202-pre 系列の Path mode 政策。実体は別 session で物理配置)

---

## 0. このドキュメントの位置づけと禁止事項

### 0.1 ドキュメントの目的

本ドキュメントは **CLAUDE.md がどう構成され、何を書き、何を書いてはいけないか** を
contract として freeze する仕様書である。CLAUDE.md 自体ではない。

session-203-pre は **docs-only**。本セッションでは以下を **物理的に行わない**:

- リポジトリルートへの `CLAUDE.md` ファイルの新規作成・配置
- `~/.claude/CLAUDE.md` (user 層) の作成
- `.claude/CLAUDE.local.md` (local 層) の作成
- `.claude/settings.json` の変更
- `.claude/hooks.bak` の復活

CLAUDE.md 実体の物理配置は **session-203** (本仕様の後続セッション) で実施する。
本セッションは「契約だけ」を書く。

### 0.2 本ドキュメントが規定する 7 つの章

| 章 | 内容 |
|----|------|
| §1 | CLAUDE.md 階層構造 (project / user / local の 3 層) |
| §2 | 各層の責務分担と読み込み順序 |
| §3 | CLAUDE.md に書くべき項目リスト |
| §4 | CLAUDE.md に書いてはいけない項目 |
| §5 | master_instruction.md との競合解消ルール |
| §6 | path_mode_policy_v1.md (session-202-pre) からの参照ポイント |
| §7 | 改訂手順 (変更権限・PR レビュー必須事項) |

---

## 1. CLAUDE.md 階層構造 (project / user / local の 3 層)

### 1.1 3 層モデルの定義

Claude Code は CLAUDE.md を **3 つの独立した層** から読み込む。各層は
スコープ・所有者・version 管理方法が異なる。

| 層 | パス | スコープ | git 管理 | 所有者 |
|----|------|----------|----------|--------|
| project 層 | `<repo_root>/CLAUDE.md` | リポジトリ全体 | 追跡する (commit 対象) | KUNIHIDE (司令塔) |
| user 層 | `~/.claude/CLAUDE.md` | そのマシンの全リポジトリ横断 | 追跡しない (マシンローカル) | KUNIHIDE 個人 |
| local 層 | `<repo_root>/.claude/CLAUDE.local.md` | このリポジトリの作業者ローカル | `.gitignore` 推奨 (追跡しない) | 作業者個人 |

### 1.2 project 層 (canonical)

- **役割**: 本リポジトリにおける ClaudeCode の入口・絶対禁則・規律の正本。
- **内容**: 4 原則 / 体制 v3 / 絶対禁則 / 4-gate / Skills 一覧 / 既知事故パターン。
- **必須**: 「前回の議論を知らない状態でも正しく動く」を保証する自己完結性。
- **重複禁止**: 詳細は `docs/strategy/` 配下を参照させ、project 層には
  **ポインタ + 絶対禁則のみ** を書く (内容の重複を避ける)。
- **凍結度**: 高。変更は §7 の改訂手順に従い PR レビュー必須。

### 1.3 user 層 (machine-personal)

- **役割**: KUNIHIDE がどのリポジトリで作業しても効かせたい個人設定。
- **内容例**: 応答言語の好み / エディタ慣習 / 個人的なコミットメッセージ様式。
- **禁止**: プロジェクト固有の禁則・秘密情報・本番資産パスを書かない。
- **git 管理外**: マシンローカル。リポジトリには絶対に commit しない。

### 1.4 local 層 (worktree-personal)

- **役割**: 作業者が当該リポジトリでだけ使う一時的なメモ・実験的ルール。
- **内容例**: 進行中の sandbox branch 名 / 一時的な検証手順。
- **禁止**: 正本的ルールを local 層に置かない (project 層が正本)。
- **git 管理外**: `.gitignore` で除外。commit すると 3 層の責務が崩壊する。

### 1.5 3 層のスコープ図 (概念)

```
user 層   (~/.claude/CLAUDE.md)        ─ マシン全体に効く
   └─ project 層 (<repo>/CLAUDE.md)    ─ このリポジトリの正本 (canonical)
        └─ local 層 (.claude/CLAUDE.local.md) ─ この作業者だけの上書き
```

スコープは外側ほど広く、内側ほど狭い。狭い層が広い層を **補足** する
(後述 §2 の読み込み順序を参照)。

---

## 2. 各層の責務分担と読み込み順序

### 2.1 責務分担マトリクス

| 項目 | project 層 | user 層 | local 層 |
|------|-----------|---------|----------|
| 4 原則 (永久固定) | ○ 正本 | × | × |
| 体制 v3 / 越権禁止 | ○ 正本 | × | × |
| 絶対禁則 (git / stash / 本番) | ○ 正本 | △ 補強可 | △ 補強可 |
| Commander = KUNIHIDE 明示 | ○ 正本 | × | × |
| 4-gate コマンド | ○ 正本 | × | × |
| md5 baseline 一覧 | ○ 正本 | × | × |
| 個人エディタ慣習 | × | ○ | △ |
| 進行中 sandbox branch メモ | × | × | ○ |
| 秘密情報 / APIキー | **禁止** | **禁止** | **禁止** |

凡例: ○ = この層に書く / △ = 補足のみ可 (正本を弱めない範囲) / × = 書かない。

### 2.2 読み込み順序 (load order)

Claude Code は以下の順で CLAUDE.md を読み込み、後勝ち補足ではなく
**「より狭いスコープが、より広いスコープを補強する」** モデルで合成する。

1. **user 層** を読む (マシン全体の前提)。
2. **project 層** を読む (リポジトリ正本)。**絶対禁則はここで確定し、後段で緩められない。**
3. **local 層** を読む (作業者ローカルの補足)。

### 2.3 競合時の優先順位 (precedence)

- **禁則の強化方向は常に許可** (より厳しくする補足は下位層でも可)。
- **禁則の緩和方向は常に禁止** (project 層の絶対禁則を user/local 層で
  上書き・無効化することはできない)。
- 価値判定・優先度・規約解釈に関わる記述は **project 層が唯一の正本**。
  user/local 層に書かれていても ClaudeCode は project 層を優先する。

### 2.4 「自己完結性」の保証要件

project 層は、過去の chat 履歴・別ドキュメントを読まなくても
ClaudeCode が **誤動作しないだけの最小情報** を内包しなければならない:

- 絶対禁則 (git push / git add . / main 直 commit / sealed stash 操作 / 本番アクセス)
- Commander = KUNIHIDE の明示と越権禁止
- 4-gate コマンドの実体
- 詳細文書への正確なポインタ

---

## 3. CLAUDE.md に書くべき項目リスト

project 層 CLAUDE.md には、以下を **必ず** 含める。各項目は本契約の
checklist であり、session-203 の実体配置時に逐一照合する。

### 3.1 Commander = KUNIHIDE の明示 (必須)

- 「**司令塔 (Commander) は KUNIHIDE (人間) である**」を冒頭付近に明記する。
- ClaudeCode の責任範囲は「現場実装 / テスト / artifact 生成 / Skills 実行」に限定。
- 価値判定 / 優先度 / リスク受容 / 規約解釈 は **KUNIHIDE 専権** と明記。
- 「これが業界標準です、採用しましょう」型の発話は越権であると明記。

### 3.2 各 Path 切替時の挙動 (必須)

- ClaudeCode が動作する Path mode (作業文脈の切替) ごとの許可・禁止挙動を
  CLAUDE.md から `path_mode_policy_v1.md` (session-202-pre 系列) へポインタする。
- Path 切替時に **絶対禁則は不変** であることを明記する
  (Path が変わっても git push 禁止・sandbox-first は緩まない)。
- 詳細は §6 を参照。

### 3.3 禁止操作 (必須・絶対禁則)

CLAUDE.md には少なくとも以下の **禁止操作 (forbidden actions)** を列挙する:

- `git push` は KUNIHIDE manual only — ClaudeCode は実行しない。
- `git add .` / `git add -A` 禁止 — 個別ファイル指定必須。
- `main` ブランチへの直接 commit 禁止 — sandbox branch のみ。
- `git stash pop / drop / apply` 禁止 — sealed stash@{0..7} 保護。
- `git push --force` / `git reset --hard` は KUNIHIDE 確認後のみ。
- sealed stash (8 件) への操作禁止。
- `.claude/settings.json` (32 bytes placeholder) の改変禁止。
- 戦略文書 (`docs/strategy/*` 等) の直接改変禁止。
- 本番 DB / production server への直接アクセス禁止。
- `npm install` / `pip install` の承認なし実行禁止。
- 凍結コード (`run_session.py` / `orchestration/`) への変更禁止。

### 3.4 4-gate コマンド (必須・実体を明記)

CLAUDE.md には 4-gate 検証コマンドの **実体** を書く (説明だけにしない):

```bash
# Gate 1: ruff (Python linting)
ruff check .

# Gate 2: pytest (unit tests)
pytest tests/ -q

# Gate 3: mypy (type check)
mypy . --ignore-missing-imports

# Gate 4: compileall (Python syntax check)
python -m compileall . -q
```

- 4 ゲートすべて PASS を artifact に記録する旨を明記。
- FAIL が残った状態の「完了」報告は `failure_type: artifact_missing` 扱いと明記。

### 3.5 md5 baseline 一覧 (必須)

CLAUDE.md には、改変禁止ファイルの **md5 baseline 一覧** を持つこと。
目的は「正本盲信」防止 (lessons-learned §3.1) と sealed 資産の改ざん検出。

- baseline は「ファイルパス → md5 ハッシュ」の表として記載。
- 対象は最低限、戦略文書群・`.claude/settings.json`・sealed stash カウント。
- baseline と現物が一致しない場合は **作業中断 → KUNIHIDE 報告** と明記。
- baseline 更新は §7 改訂手順に従い PR レビュー必須。

> 注: 本セッションは docs-only。md5 値の実測・埋め込みは session-203
> (実体配置) で行う。本契約は「md5 baseline 一覧を必ず持て」という
> 構造要件を freeze するにとどめる。

### 3.6 詳細文書へのポインタ (必須)

CLAUDE.md は内容を重複させず、以下へ正確にポインタする:

- `docs/strategy/vision-and-principles.md` (4 原則・体制 v3 正本)
- `docs/strategy/roadmap-2026.md` (Phase 計画)
- `docs/strategy/lessons-learned.md` (事故 + 再発防止)
- `docs/strategy/session-plan.yaml` (セッション計画)
- `docs/strategy/skills-template/*.md` (Skills 雛形)
- `docs/master_instruction.md` (人間司令塔向け正本 — §5 参照)

### 3.7 セッション起票・Skills 規律 (必須)

- 14 キー JSON 仕様の参照 (`/session-planner`)。
- review_points 固定 4 軸 (変更禁止) の明示。
- 4 Skills (session-planner / worker / judge-4axis / reporter) の一覧。

### 3.8 緊急時トリガー (必須)

- 凍結審議トリガー (Day 14 Hard Gate 連続 2 回失敗 / sealed stash 件数変動 等)。
- 発生時は **即時 KUNIHIDE 報告 + 作業停止** と明記。

---

## 4. CLAUDE.md に書いてはいけない項目

CLAUDE.md は git 追跡され、共有・履歴化される。以下は **いかなる層にも** 書かない。

### 4.1 秘密情報 (絶対禁止)

- API キー / アクセストークン / OAuth client secret。
- DB 接続文字列 / DB パスワード / production credential。
- 署名鍵 / SSH 秘密鍵 / TLS 秘密鍵。
- セッション cookie / bearer token の実値。

### 4.2 API キー・資格情報のプレースホルダ含む (絶対禁止)

- 「サンプル」と称した実在キー形状の文字列も禁止 (誤コピー誘発)。
- `.env` / `secrets/` の中身を引用・転記しない。CLAUDE.md からは
  「これらは読まない」という禁則のみを書く。

### 4.3 内部資産パス (禁止)

- 本番サーバの内部ホスト名 / 内部 IP / 内部ポート。
- 本番 DB のスキーマ名・テーブル名の機微な列挙。
- 個人ローカルの絶対パス (例: `/Users/<個人名>/...`) の機微部分。
  正本としての参照は「リポジトリ相対パス」または役割名で記述する。

### 4.4 価値判定・優先順位の決め打ち (禁止)

- 「この機能を最優先する」等の価値判定を ClaudeCode 向け CLAUDE.md に
  固定で書かない (KUNIHIDE 専権。roadmap/session-plan が正本)。

### 4.5 内容の重複 (禁止)

- 戦略文書の本文を CLAUDE.md に丸ごとコピーしない (ポインタのみ)。
  重複は更新漏れ・正本盲信 (lessons-learned §3.1) を誘発する。

### 4.6 検出と是正

- 秘密情報の混入が疑われる場合、ClaudeCode は **commit せず即 KUNIHIDE 報告**。
- hooks 側 (`hooks_contract_v1.md` 参照) の PreToolUse/PostToolUse ガードと
  二重化して防御する。

---

## 5. master_instruction.md との競合解消ルール

### 5.1 2 つの正本の役割分担

| ドキュメント | 読者 | 役割 |
|--------------|------|------|
| `CLAUDE.md` (project 層) | **ClaudeCode (機械実装担当)** | 現場実装の禁則・規律・4-gate の運用契約 |
| `docs/master_instruction.md` | **人間司令塔 (KUNIHIDE)** | 思想・体制・意思決定の正本 (v1 凍結済) |

- CLAUDE.md は master_instruction.md の **下位の運用具体化** であり、
  master_instruction.md の思想・体制を **逸脱・上書きしない**。
- master_instruction.md は v1 凍結済。ClaudeCode は直接変更しない (絶対禁則)。

### 5.2 競合が起きたときの優先順位

1. **思想・体制・価値判定の競合** → `master_instruction.md` が優先。
   CLAUDE.md の記述が master_instruction.md と矛盾する場合、
   CLAUDE.md 側が誤り。ClaudeCode は **作業を止めて KUNIHIDE に報告**する。
2. **現場実装手順の具体 (4-gate コマンド・禁則の運用詳細)** → `CLAUDE.md` が
   実務の参照点。ただし master_instruction.md の禁則を緩める方向は不可。
3. **絶対禁則は常に「より厳しい方」を採用** (どちらかが禁止していれば禁止)。

### 5.3 競合検出時の ClaudeCode の挙動

- 競合を発見しても **ClaudeCode は自己判断で解消しない** (規約解釈は越権)。
- 競合点・該当箇所・推奨解釈案を整理し、KUNIHIDE の判断を仰ぐ。
- master_instruction.md / CLAUDE.md のどちらを直すかの決定は KUNIHIDE 専権。

### 5.4 非重複の原則

- 同一ルールを両方に重複記載しない。master_instruction.md が思想を述べ、
  CLAUDE.md はその運用契約を書く。重複は競合の温床になる。

---

## 6. path_mode_policy_v1.md (session-202-pre) からの参照ポイント

### 6.1 参照関係

- `path_mode_policy_v1.md` は session-202-pre 系列で扱う **Path mode 政策**文書。
- 本契約時点では物理未配置の **forward reference** (session-201-pre が
  worker_report_contract.md を forward 参照したのと同じ扱い)。
- CLAUDE.md は path_mode_policy_v1.md へ **ポインタのみ** を持ち、内容を
  重複させない (§4.5)。

### 6.2 CLAUDE.md が path_mode_policy_v1.md から取り込むべき参照ポイント

| # | 参照ポイント | CLAUDE.md 側の扱い |
|---|--------------|--------------------|
| 1 | Path mode の定義 (作業文脈の切替単位) | ポインタ + 「絶対禁則は Path 不変」明記 |
| 2 | 各 Path で許可される操作集合 | ポインタのみ (実体は policy 文書) |
| 3 | 各 Path で禁止される操作集合 | 絶対禁則と矛盾しないことを明記 |
| 4 | Path 切替の承認境界 (誰が切替を許可するか) | 切替判断は KUNIHIDE 専権と明記 |
| 5 | Path 切替時の sandbox-first 不変条件 | 原則 3 (Sandbox-First) は全 Path で不変 |

### 6.3 不変条件 (Path によらず保持)

- `git push` 禁止 / `git add .` 禁止 / main 直 commit 禁止 は **全 Path で不変**。
- sealed stash@{0..7} 保護は **全 Path で不変**。
- 本番アクセス禁止は **全 Path で不変**。
- Path 切替は禁則を緩めるための手段ではない (§2.3 の禁則緩和禁止と一致)。

### 6.4 forward reference の解消時期

- path_mode_policy_v1.md の物理配置・内容 freeze は session-202-pre 系列で実施。
- CLAUDE.md 実体配置 (session-203) 時点で path_mode_policy_v1.md が存在する場合、
  本 §6 の参照ポイントを実リンクへ差し替える。
- 存在しない場合は forward reference のまま明示し、解消 session を記録する。

---

## 7. 改訂手順 (変更権限・PR レビュー必須事項)

### 7.1 変更権限 (誰が CLAUDE.md を変えられるか)

| 層 | 変更権限保持者 | ClaudeCode の権限 |
|----|----------------|--------------------|
| project 層 | KUNIHIDE のみ (司令塔専権) | 提案・差分作成のみ。直接確定・merge・push は不可 |
| user 層 | KUNIHIDE 個人 | 関与しない (マシンローカル) |
| local 層 | 当該作業者 | 補足メモのみ。正本化は不可 |

- ClaudeCode は project 層 CLAUDE.md の **草案・差分提案まで**。
  確定 (main merge / push) は KUNIHIDE manual only (絶対禁則 §3.3)。

### 7.2 改訂のトリガー

- 月次 / 四半期 / 半年 / 年次の見直しサイクル (roadmap-2026.md §10 準拠)。
- 絶対禁則の追加が必要な事故・教訓が発生したとき (lessons-learned 追記と連動)。
- master_instruction.md 改訂に伴う運用契約の追従が必要なとき。

### 7.3 PR レビュー必須事項 (改訂 PR のチェックリスト)

CLAUDE.md を改訂する PR は、以下を **すべて** 満たさなければ merge 不可:

1. **絶対禁則の非緩和**: 既存の絶対禁則が削除・緩和されていないこと
   (強化方向のみ許可)。
2. **Commander 明示の保持**: Commander = KUNIHIDE / 越権禁止の記述が残ること。
3. **4-gate の整合**: 4-gate コマンドが現行 Gate 定義と一致すること。
4. **md5 baseline 整合**: baseline 一覧が改変禁止ファイルの現物と一致すること。
5. **秘密情報の不在**: §4 の禁止項目 (秘密情報・APIキー・内部資産パス) が
   混入していないこと (hooks 側ガードと二重チェック)。
6. **非重複**: 戦略文書本文の重複コピーがないこと (ポインタであること)。
7. **master_instruction.md 非競合**: §5 の競合解消ルールに反しないこと。
8. **session 起票整合**: 改訂が session JSON (14-key) + acceptance YAML を伴うこと。

### 7.4 改訂の禁止事項

- ClaudeCode による project 層 CLAUDE.md の **無断確定・無断 push** は絶対禁止。
- レビューを経ない絶対禁則の削除・緩和は禁止。
- 秘密情報・内部資産パスの追加は、いかなる改訂でも禁止 (§4)。

### 7.5 改訂の記録

- 改訂は session JSON (`docs/sessions/`) + acceptance YAML (`docs/acceptance/`) を
  伴って起票する (起票なしの直変更は禁止)。
- 改訂履歴は commit message と session artifact に残す。

---

## 8. 本契約の受入対応 (acceptance マッピング)

本契約が満たすべき検証可能条件は `docs/acceptance/session-203-pre.yaml` に
1:1 で定義される。要点:

- 本ファイルが存在し 400 行以上であること。
- §1〜§7 の 7 章がすべて存在すること。
- 「Commander = KUNIHIDE」「3 層 (project / user / local)」「禁止操作」
  「4-gate」「md5 baseline」「master_instruction.md」「path_mode_policy_v1.md」
  の各キーワードが本文に明記されていること。
- 秘密情報・API キー実値が本文に **含まれていない** こと。

---

## 9. 改訂履歴

| version | date | session | 変更概要 |
|---------|------|---------|----------|
| v1 | 2026-05-17 | session-203-pre | 初版 freeze (docs-only 契約仕様。CLAUDE.md 実体配置は session-203) |

---

**END OF FILE — claude_md_contract_v1.md (v1, frozen-spec, docs-only)**
