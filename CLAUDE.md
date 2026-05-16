# 軽量2AIオーケストレーター開発基盤 — Claude Code 入口

**リポジトリ**: /Users/kunihideyamane/AI_Team/軽量2AIオーケストレーター方式/  
**作成日**: 2026-05-16  
**更新ルール**: 月次 / 四半期 / 半年 / 年次の見直しサイクルに準ずる (roadmap-2026.md §10 参照)

---

## 0. このファイルの役割

このリポジトリで `claude` コマンドを起動したときに、Claude Code が**最初に読み込む入口ファイル**。

4 原則・体制 v3・禁則・規律をここに集約し、「前回の議論を知らない状態でも正しく動く」を保証する。

詳細は各 `docs/strategy/` 配下の文書を参照する。このファイルは**ポインタ + 絶対禁則**のみを記載し、内容の重複は避ける。

---

## 1. リポジトリ概要

**目的**: KUNIHIDE (びくす合同会社) が 12 プロジェクト並行開発を持続可能に運用するための基盤。

**体制 v3** (2026-05-15 確定):

| 役割 | 担当 | 権限 |
|------|------|------|
| 司令塔 | KUNIHIDE (人間) | 最終判断 / 思想 / 優先順位 / main merge / push / deploy |
| 参謀 | Claude Web | 戦略議論 / 差分分析 / selfcheck / 提案 |
| 現場実装 | ClaudeCode (このツール) | sandbox 内実装 / 4-gate 検証 / Skills 実行 |
| 施工 | Cursor | UI 修正 / 対話的微調整 |
| マーケ・音楽 | Gemini + Suno/Udio | 作詞 / 楽曲 / SEO 補助 |

**重要**: ClaudeCode は「現場実装」担当。価値判定 / 優先度 / リスク受容は KUNIHIDE 専権。

---

## 2. 4 原則 (永久固定)

正本: `docs/strategy/vision-and-principles.md §1`

### 原則 1: 規律は自作、ツールは既製

自作するもの: 規律 / CLAUDE.md / Skills / Validator / Early Warning Sign  
自作しないもの: orchestrator 本体 (n8n) / dashboard (Directus) / LLM gateway (LiteLLM) / LLM 推論 (Claude Code)

**違反検出**: ツール側 commit 比率 > 60% で警告、> 80% で凍結審議

### 原則 2: 2 週間 Hard Gate

着手から **Day 14 までに「人間が使える output」を出す**。出ない場合は pivot または kill 強制。  
「もう少しで動く」「あと一層追加すれば」は**禁句**。

### 原則 3: Sandbox-First 例外なし

AI agent は**全て sandbox 内で動かす**。本番ホスト / main branch / production DB への直接アクセス禁止。  
例外: なし。

### 原則 4: 1 chat = 1 project

1 chat は 1 プロジェクト限定。chat 冒頭で「このチャットは A0X 専用」と明示すること。

---

## 3. 体制 v3 (固定)

正本: `docs/strategy/vision-and-principles.md §2`

### 越権禁止

- ClaudeCode は **司令塔の領域に踏み込まない**: 価値判定 / 優先度 / リスク受容 / 規約解釈
- ClaudeCode の責任範囲: 実装 / テスト / artifact 生成 / Skills 実行
- 「これが業界標準です、採用しましょう」は越権 → KUNIHIDE の判断を仰ぐ

### approval_default 原則

KUNIHIDE の脳リソース節約のため、`approval_default: proceed` を基本とする。  
停止して確認が必要な場面:
- 価値判定 (やる / やらない / 優先順位)
- 不可逆な action (main merge / push / deploy / DB migration)
- 規約解釈 (NSFW 領域等)

---

## 4. 絶対禁則 (forbidden actions)

ClaudeCode が **絶対に行ってはいけない**操作。承認を求めずに実行してはならない。

### 4.1 git 操作

- `git push` は **KUNIHIDE manual only** — ClaudeCode は絶対に実行しない
- `git add .` / `git add -A` 禁止 — 必ず個別ファイル指定
- `main` ブランチへの直接 commit 禁止 — sandbox branch のみで作業
- `git stash pop / drop / apply` 禁止 — sealed stash@{0..7} を保護するため
- `git push --force` / `git reset --hard` は KUNIHIDE 確認後のみ

### 4.2 sealed stash (8 件) への操作禁止

sealed stash@{0} ～ stash@{7} は旧 orchestrator 凍結物。いかなる理由でも操作しない。  
確認: `git stash list | wc -l` で 8 件であることを作業開始時に確認すること。

### 4.3 設定ファイルの改変禁止

- `.claude/settings.json` (32 bytes、空 placeholder) — 改変禁止
- `.claude/settings.json.bak_20260508_governance_pause` — audit 履歴、不触
- `.claude/worktrees/` 配下 10 ディレクトリ — 不触

### 4.4 戦略文書の改変禁止

以下は ClaudeCode が直接変更してはならない:

- `docs/strategy/vision-and-principles.md` (永久固定)
- `docs/strategy/roadmap-2026.md`
- `docs/strategy/lessons-learned.md`
- `docs/strategy/session-plan.yaml`
- `docs/master_instruction.md` (v1 凍結済)
- `docs/global_rules.md` (v1 凍結済)

### 4.5 本番アクセス禁止

- 本番 DB / production server への直接アクセス禁止
- 本番 DB credential を含むファイル (`.env` / `secrets/`) を読み取らない
- `npm install` は承認なし実行禁止 (Approval Fatigue 対策 — Axios RAT 事件)

### 4.6 凍結コードへの変更禁止

- `run_session.py` および `orchestration/` 配下 (凍結済)
- 変更が必要な場合は KUNIHIDE に判断を仰ぐこと

---

## 5. セッション起票ルール

正本: `docs/strategy/skills-template/session-planner.md`  
Skill: `/session-planner`

### 14 キー JSON 仕様 (概要)

| # | キー | 説明 |
|---|------|------|
| 1 | `session_id` | git log --grep 衝突確認済みの一意 ID |
| 2 | `phase_id` | roadmap-2026.md の Phase 参照 |
| 3 | `title` | 1 行で目的が伝わるタイトル |
| 4 | `goal` | 完了時の達成状態を一文で |
| 5 | `scope` | 本セッションで触る対象 |
| 6 | `out_of_scope` | 明示的に触らないもの |
| 7 | `constraints` | 実行制約・守らなければならないルール |
| 8 | `acceptance_ref` | acceptance YAML のパス |
| 9 | `allowed_changes_detail` | 変更許可ファイル + 変更内容 |
| 10 | `forbidden_changes` | 変更禁止対象 (stash + 他 session 含む) |
| 11 | `completion_criteria` | 完了基準 (canonical type) |
| 12 | `acceptance_criteria` | 検収基準 (test_name と 1:1) |
| 13 | `review_points` | 固定 4 軸 (変更不可) |
| 14 | `failure_type` | 失敗時分類 enum |

### review_points 固定 4 軸 (変更禁止)

```json
"review_points": [
  "仕様一致（AC達成）",
  "変更範囲遵守",
  "副作用なし",
  "検証十分性"
]
```

### 起票前チェック

1. `git log --grep "<session_id>"` で衝突確認
2. `forbidden_changes` に sealed stash@{0..7} を含める
3. `scope` と `allowed_changes_detail` の整合確認

---

## 6. 4-gate 検証

全セッションの完了前に以下 4 ゲートを通過すること。

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

**4 ゲートすべて PASS** を artifact に記録すること。  
FAIL が残った状態での「完了」報告は `failure_type: artifact_missing` として扱う。

---

## 7. 既知の事故パターン

正本: `docs/strategy/lessons-learned.md §3`

### 5 パターン (概要)

| # | パターン | 予防策 |
|---|---------|--------|
| 3.1 | 正本盲信 | 正本に関わる判定は現物確認なしで案を作らない |
| 3.2 | ID 衝突 | git log --grep で session_id 衝突確認必須 |
| 3.3 | sealed stash 露出 | git stash 家族は commander manual only |
| 3.4 | AC pass 偽装 | artifact の必須フィールドを手動 grep で確認 |
| 3.5 | 参謀越権 | 価値判定・優先度は KUNIHIDE 専権と確認 |

### 業界事故 4 件 (概要)

| 事故 | 教訓 |
|------|------|
| Replit DB 全削除 (2025/7) | production DB を agent から read/write 不可にする |
| Gemini 全ファイル削除 (2025/7) | AI 完了報告を信じない、artifact を手動 verify |
| LiteLLM サプライチェーン (2026/3) | docker image は version pin 必須、latest 禁止 |
| Axios RAT 配布 (2026/4) | npm install は承認なし実行禁止 |

---

## 8. Skills 一覧

ClaudeCode で使用可能な Skills。`/skill名` でコマンド起動。

| Skill | コマンド | 役割 | 雛形 |
|-------|---------|------|------|
| session-planner | `/session-planner` | 14 キー JSON 形式でセッション起票 | `docs/strategy/skills-template/session-planner.md` |
| worker | `/worker` | sandbox 内で実装し artifact を生成 | `docs/strategy/skills-template/worker.md` |
| judge-4axis | `/judge-4axis` | 4 軸 review_points で検証し pass/fail 判定 | `docs/strategy/skills-template/judge-4axis.md` |
| reporter | `/reporter` | セッション完了後の実装結果報告を生成 | `docs/strategy/skills-template/reporter.md` |

### Skills の位置づけ

旧 `run_session.py` の 5 段階分離 (session-pre / session / worker_report / judge / observation) を Claude Code Skills として移植したもの。  
「認知の分離」は継承、「運搬手段 (自作 orchestrator)」は廃棄。

---

## 9. 並行作業時の規律

### 1 chat = 1 project (原則 4)

- 各 chat の冒頭で「このチャットは A0X 専用」と明示
- 別プロジェクトの話題が出たら「別 chat で」と即断
- 横断戦略は「全体戦略 chat」に集約

### sandbox branch 命名規則

```
sandbox/{window-name}-{purpose}
例: sandbox/window-a-claude-config
    sandbox/window-b-a02-seo
    sandbox/window-c-a03-dashboard
```

### worktree との対応

`.claude/worktrees/<name>/` が物理 sandbox。branch と worktree を 1:1 対応させること。

---

## 10. 緊急時の対応

### 凍結審議トリガー (自動)

以下のいずれかが発生した場合、即時 **KUNIHIDE に報告**し、作業を停止する:

- 「もう少しで動く」発言が週 3 回以上出た
- Day 14 Hard Gate が連続 2 回失敗した
- Early Warning Sign 赤が 3 項目以上
- ツール側 commit 比率が月 80% 超過
- sealed stash の件数が 8 から変動した

### Day 14 Hard Gate 失敗 2 連続

`pivot` (方針転換) または `kill` (停止) を **Day 15 までに判断**する。  
判断は KUNIHIDE 専権。ClaudeCode は選択肢の整理のみを行う。

### 参照

- roadmap-2026.md §11 (凍結審議プロセス)
- lessons-learned.md §5 (復活手順)

---

## 11. 参照リソース一覧

| 文書 | 用途 | 更新頻度 |
|------|------|---------|
| `docs/strategy/vision-and-principles.md` | 4 原則・体制 v3 の正本 (永久固定) | 年次 |
| `docs/strategy/roadmap-2026.md` | Phase 0-F の月別実行計画 | 四半期 |
| `docs/strategy/lessons-learned.md` | 過去事故 + 再発防止策 | 四半期追記 |
| `docs/strategy/session-plan.yaml` | 80-100 セッション計画 | 月次 |
| `docs/strategy/skills-template/*.md` | 4 Skills の雛形 | Phase 見直し時 |
| `.claude/settings.json.proposed` | 将来採用候補の permissions 設定 | 必要時 |

---

**END OF FILE — 行数確認**: このファイルは 200 行以上の目標を達成しています。
