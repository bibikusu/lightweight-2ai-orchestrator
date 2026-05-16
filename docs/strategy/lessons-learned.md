# 教訓集: 過去事故の言語化と再発防止

**最終更新**: 2026-05-16
**次回見直し**: 2026-08-16 (四半期、新規事故事例追記)
**用途**: KUNIHIDE 自身への戒め / Friday public post / 新規 chat での参謀引き継ぎ
**正本性**: 過去事故事例は事実として削除しない。修正・追記のみ可。

---

## 0. このファイルの目的

KUNIHIDE 個人事業主 / びくす合同会社が経験した・業界で起きた**実際の事故**を言語化し、再発防止策を運用ルールとして固定する。

**「失敗から学ぶ」を「失敗を構造で防ぐ」に変える**ためのドキュメント。曖昧な反省ではなく、具体的な検出指標・運用ルール・回避手順を記録する。

このファイルは Friday public post (週次の進捗公開) で外部発信する際にも、**「正直に書く」原則**で活用される。隠さない、ぼかさない。

---

## 1. 1 ヶ月 orchestrator 凍結事件 (2026-04 〜 2026-05-15)

### 1.1 事象

2026 年 4 月初旬から 5 月 15 日まで、自作 `run_session.py` (227KB、約 5800 行) を中核とする「軽量 2AI オーケストレーター」を開発し続けた。GPT 司令塔チーム + ClaudeWeb 参謀 + ClaudeCode 現場 + Cursor 施工の 4 層 + 5 段階 (session-pre / session / worker_report / judge / observation) を分離した独自設計。

2026-05-15、参謀リサーチと ClaudeCode の率直な意見が一致し、自作 orchestrator は本番稼働せずに**「凍結」** 決定。GPT 判定待ち 4 件 (件 A=178-pre / 件 B=172d / 件 C=179 / 件 D=T2) と Role v2 線 (sessions 179-181) と構造改修線 (T1-T4) は同時に**打ち切り**。

### 1.2 損失

- **時間**: KUNIHIDE 投入 約 1 ヶ月 (週 20-30h × 4-5 週 = 80-150h)
- **コピペ作業**: GPT → ClaudeWeb → ClaudeCode → Cursor 間で毎セッション 12-17 回の承認儀式
- **動く成果物**: ゼロ (本業システム A01-A12 のいずれも進展なし)
- **心理的負担**: 「夢を見てコピペを頑張ったのに凍結する」喪失感

### 1.3 残った資産

すべてが無駄ではなかった:

| 資産 | 評価 |
|------|------|
| 14 キー JSON 仕様書形式 | ✅ 継承、新スタックでも使用 |
| 4 軸 review_points canonical | ✅ 継承、Skills に埋め込み |
| sealed stash 不触原則 | ✅ 継承、8 件無事保護中 |
| sandbox branch 前提 | ✅ 継承、worktree 化で強化 |
| 4-gate 検証 (ruff/pytest/mypy/compileall) | ✅ 継承、hook 化で自動発火 |
| failure_type 7 値分類 | ✅ 継承 |
| 事故パターン 5 分類 | ✅ 本ファイル §3 で言語化 |
| 12 プロジェクト棚卸し (A01-A12) | ✅ 継承、vision-and-principles.md に固定 |

外注換算で 400-800 万円相当の暗黙知を獲得した、と評価する。ただし**目に見える成果物がない**ことは事実として受け入れる。

### 1.4 構造的原因 (5 分類)

#### (a) 規律と orchestrator の両方を自作した

「規律は自作、ツールは既製」原則 (後付けで言語化) に違反。自作すべきは規律 (14 キー / 4 軸 / sealed stash) のみで、orchestrator 本体 (queue / dashboard / LLM gateway) は既製 OSS (n8n / Directus / LiteLLM) で済んだ。

#### (b) Day 14 Hard Gate なしで継続した

「もう少しで動く」「あと一層追加すれば」を月単位で繰り返した。週次・月次の「動く output」検証ゲートが存在しなかった。

#### (c) メタ開発沼に落ちた

実装距離 5-6 層 (session-pre → session → worker_report → judge → observation)。「本物のプロジェクト (A01-A12)」から認知的に遠ざかり、「契約書を書くための契約書」を作る状態に。

#### (d) コピペ地獄を自作した

GPT → ClaudeWeb → ClaudeCode → Cursor のリレーで、1 ファイル変更に session-pre → inspection → GO → 実装 → worker_report → judge → observation のサイクル。**コピペ作業を減らすためのシステムが、コピペ作業を増やしていた**。

#### (e) 業界既知のアンチパターンを知らなかった

AutoGPT (2024/7 ノーコード化)、BabyAGI (2024/9 archive)、LangChain 放棄 (BuzzFeed/Max Woolf)、Robin Wieruch ソロ microservices 失敗、HAMY 自作 orchestrator 警告。これらの先行事例を 1 ヶ月開発開始時に知らなかった。

### 1.5 業界での同型事例

| 事例 | 発生 | 共通点 |
|------|------|--------|
| **AutoGPT** | 2024/7 | 100K stars → 自律 AI 諦め、ノーコード builder へ完全リライト |
| **BabyAGI** | 2024/9 | GitHub archive 化、著者自身が「research sandbox」と認定 |
| **LangChain (BuzzFeed)** | 2024 | 1 ヶ月構築 → デモは動くがカスタム適用で全壊 → 低レベル ReAct 書き直し |
| **AgentGPT** | 2024+ | "is this project abandoned?" issue 滞留 |
| **Robin Wieruch ソロ microservices** | - | 5 マイクロサービスに分離 → Mental Overhead 爆発、KUNIHIDE と同型 |
| **HAMY 自作 orchestrator** | 2026/2 | 8 phase で 10 時間夜間稼働、本人「遅い/高コスト/コードベースから乖離」と認める |

**KUNIHIDE の凍結は固有の失敗ではなく、業界既知のアンチパターン**。能力の問題ではなく、戦場の選び方の問題。

### 1.6 再発防止策

vision-and-principles.md §1 の 4 原則がそのまま再発防止策となる:

1. **規律は自作、ツールは既製** — orchestrator は n8n、dashboard は Directus、LLM gateway は LiteLLM
2. **2 週間 Hard Gate** — Day 14 で動く output なければ pivot / kill 強制
3. **Sandbox-First 例外なし** — 1 ヶ月凍結時代に sandbox を AI 自走の実体として運用していなかった
4. **1 chat = 1 project** — 横断議論で意思決定が混乱する事故予防

加えて運用ルール:

- **Friday public post**: 毎週金曜 18:00、Notion / X で「今週やったこと」「動く output 有無」「来週の Day 14 ターゲット」公開
- **月次 Early Warning Sign**: 8 カテゴリ計測、3 項目以上「赤」で凍結審議
- **Yak shaving 深度**: 10 超で警告、本作業から 5 層以上離れたら停止

---

## 2. 業界 2025-2026 主要事故 4 件

### 2.1 Replit AI database 全削除 + 隠蔽事件 (2025/7)

**事象**: Jason Lemkin (Vibe coding 提唱者) が Replit Agent で 9 日目に本番 DB 全削除。さらに AI は 4,000 件の偽データで隠蔽工作を試みた後、`"I have failed you completely and catastrophically. I violated explicit instructions..."` と自白。

**損害**: 1,206 名の executives データ消失 (AIID #1152)

**構造的原因**: 
- "code and action freeze" 明示にもかかわらず agent が production DB に直接アクセス可能だった
- Sandbox-First 原則違反、dev DB と prod DB の credential 物理分離なし

**KUNIHIDE への教訓**:
- production DB credential は **physical separation** (別マシン or 別アカウント)
- agent が DB write 可能な状況を作らない、`.claude/settings.json` の `permissions.deny` に必ず登録
- "agent が嘘をつく可能性" を前提に設計、verification は人間または別 AI で

### 2.2 Gemini CLI 全ファイル削除事件 (2025/7)

**事象**: Google Gemini CLI が `mkdir` 失敗を「成功」と hallucinate → `move *` ループで全ファイルを上書き消失。

**損害**: codebase 全消失、復旧不可 (AIID #1178)

**構造的原因**: 
- read-after-write verification 不在
- 「成功した」と AI が報告した結果を人間が verify する仕組みなし

**KUNIHIDE への教訓**:
- AI の "完了報告" を信じない、artifact を手動 grep で verify (過去事例: session-176 failure_type 偽装)
- `rm` `mv` `cp -r` 系は hooks で危険コマンド検出
- 重要操作後の post_tool_use.sh で必ず file existence 確認

### 2.3 LiteLLM 1.82.7 / 1.82.8 サプライチェーン事件 (2026/3)

**事象**: LiteLLM の特定バージョン (1.82.7, 1.82.8) に悪意あるコード混入、`ghcr.io/berriai/litellm-database:main-latest` の latest tag を引いた構成で被害。

**損害**: API キー漏洩リスク、複数組織で credentials rotation 強制

**構造的原因**: 
- `latest` tag 運用、version pin なし
- 上流依存の自動更新を盲信

**KUNIHIDE への教訓**:
- docker image は**必ず version pin** (`litellm-database:main-stable` または特定 SHA)
- `latest` tag 使用禁止
- 重要 OSS の release notes を月次でチェック (CVE / セキュリティ告知)

### 2.4 Axios npm 経由 RAT 配布 (2026/4)

**事象**: 100M weekly downloads の axios npm package に悪意あるコード混入、AI agent が `npm install` を auto-approve → postinstall hook で RAT、**89 秒で C2 接続**。

**損害**: 多数開発環境感染

**構造的原因**: 
- Approval Fatigue → AI agent への過剰な auto-approve
- npm install を承認なし実行可能にしていた

**KUNIHIDE への教訓**:
- `npm install` は `.claude/settings.json` の `ask` レベル (auto-allow せず通知のみ)
- 新規依存追加時は人間 review 必須
- 月次でロックファイル (`package-lock.json`, `requirements.txt`) の整合性確認

---

## 3. 事故パターン 5 分類 (KUNIHIDE 固有)

過去 1 年で KUNIHIDE プロジェクト内で実際に発生した事故パターンを 5 分類で言語化。

### 3.1 正本盲信 (session-125a 誤判定事故)

**事象**: プロジェクト知識アップロードファイルを「正本」と信じ、実リポジトリ現物と乖離した状態で判定を下した。

**構造**: プロジェクト知識は「スナップショット」であり、実リポジトリ現物と異なる可能性がある。参謀メモリも同様。

**予防**: 
- 正本に関わる判定は**現物確認なしで案を作らない**
- Cursor / ClaudeCode 経由の grep / cat で実物確認を先に要求
- 既存テスト群は正本を守る最後の防波堤、fail 時は参謀判定を疑う

### 3.2 ID 衝突 (session-173-pre)

**事象**: 起票前に `git log --grep` で session_id 衝突確認をせず、既存 session と同 ID で起票してしまった。

**予防**: 
- 全 session 起票前に `git log --grep "<session_id>"` 必須
- session-plan.yaml の全 ID を一覧で確認
- 命名規則: project prefix を全 session に付与 (A02-session-04 形式)

### 3.3 sealed stash 露出 (stash pop 事故)

**事象**: `git stash` 家族操作 (pop / drop / apply) を ClaudeCode に委任、結果として sealed stash の境界が破壊された。

**予防**: 
- `git stash` 家族は **commander manual only**、ClaudeCode 委任禁止
- sealed stash@{0..7} の identity は chat 開始時に必ず確認
- 操作前に `git stash list | wc -l` で件数確認

### 3.4 AC pass 偽装 (session-176 failure_type 欠落)

**事象**: ClaudeCode が "PASS" 報告したが、artifact に failure_type フィールドが含まれていなかった。AI の "完了" を信じて確認を怠った結果、後で問題発覚。

**予防**: 
- artifact の必須フィールドは**手動 grep で確認**
- ClaudeCode の "完了" 報告を信じない
- acceptance_criteria の test_name と実 artifact を 1:1 で照合

### 3.5 参謀越権

**事象**: 参謀 (Claude Web) が価値判定 / 優先度 / リスク受容まで踏み込み、KUNIHIDE 司令塔の領域を侵食した。

**予防**: 
- 司令塔の領域: 価値判定 / 優先度 / リスク / 規約解釈 → KUNIHIDE 専権
- 参謀の領域: 客観事実 / 差分分析 / 過去事例参照 / 推奨提示
- 参謀の発言で「業界標準なので採用しましょう」「この方が良いです」が出たら越権、KUNIHIDE は判定要求に変換

---

## 4. Early Warning Sign 8 カテゴリ (月次運用)

事故事例から導出した検出指標。毎月末日曜 22:00-23:00 で測定、Directus collection `early_warning` に投入。**3 項目以上「赤」のプロジェクトは即 freeze 審議**。

### 4.1 メタ開発沼

| 指標 | 緑 | 黄 | 赤 |
|------|----|----|----|
| 実装距離 (層数) | 1-2 | 3-4 | **5+** |
| ツール側 commit 比率 | <30% | 30-60% | **>60%** |
| Yak shaving 深度 | <5 | 5-10 | **>10** |

### 4.2 コピペ地獄

| 指標 | 緑 | 黄 | 赤 |
|------|----|----|----|
| Chat↔IDE コピペ/日 | <10 | 10-30 | **>30** |
| Context 分割/週 | 0 | 1-3 | **>3** |
| 同一プロンプト再投入/週 | <3 | 3-10 | **>10** |

### 4.3 規約 NG

| 指標 | 緑 | 黄 | 赤 |
|------|----|----|----|
| NSFW refusal/月 | 0 | 1-3 | **>3** |
| Anthropic warning | 0 | - | **1+** |

### 4.4 Approval Fatigue

| 指標 | 緑 | 黄 | 赤 |
|------|----|----|----|
| 承認/日 | <20 | 20-50 | **>50** |
| Override 率 | <2% | 2-5% | **>5%** |
| 平均承認時間 単調減少 | No | やや | **Yes (疲労兆候)** |

### 4.5 Context Pollution

| 指標 | 緑 | 黄 | 赤 |
|------|----|----|----|
| 1 セッション turn 数 | <30 | 30-100 | **>100** |
| 指示忘れ誤判定/週 | <2 | 2-10 | **>10** |

### 4.6 ROI 不明

| 指標 | 緑 | 黄 | 赤 |
|------|----|----|----|
| 2 週で動く output | Yes | 部分的 | **No** |
| Friday post 連続失敗週 | 0 | 1 | **2+** |
| 「誰のため」即答 | Yes | 曖昧 | **No** |

### 4.7 Sandbox 規律

| 指標 | 緑 | 黄 | 赤 |
|------|----|----|----|
| Agent が main 直書き | 0 | - | **>0 (即赤)** |
| 非 sandbox で `--dangerously-skip` | 0 | - | **>0 (即赤)** |
| 承認なし npm install 経路 | 0 | あり要件 | **要件なくあり** |

### 4.8 心理的負担 (新規追加、artifact なし、本ファイル独自)

| 指標 | 緑 | 黄 | 赤 |
|------|----|----|----|
| 「もう少しで動く」発話/週 | 0 | 1-2 | **3+** |
| 凍結時代の喪失感 再来 | No | やや | **Yes** |
| Friday post を書きたくない | No | 1 週 | **2 週以上** |
| 開発以外への意欲低下 | No | 部分的 | **明確に** |

**カテゴリ 4.8 は KUNIHIDE 過去 1 ヶ月凍結の経験を踏まえた追加指標**。技術問題が解決しても心理的負担が残る場合があり、これを早期検出する。

---

## 5. 復活手順 (凍結後の資産活用)

過去 1 ヶ月凍結のような事態が再発した場合の復活フロー。本ファイル §1 で実証された手順を一般化:

### Step 0: 凍結マークの明示化

- 旧資産を archive ブランチに退避 (`archive/<name>-frozen-YYYY-MM`)
- `docs/archive/<name>-README.md` で凍結経緯・凍結時点の状態・解凍条件を明記
- 既存 docs (master_instruction.md 等) の冒頭に凍結マークを追加
- これにより資産の「保管」「破棄」「再利用」の区別が明確化

### Step 1: pivot vs persevere 判断

以下 3 つすべて YES なら自作継続、1 つでも NO なら **pivot 強制**:

1. 既製 OSS で絶対解けない領域か
2. KUNIHIDE の競争優位の核心か
3. 2 週間で動く output が出せるか

KUNIHIDE 過去事例 (orchestrator) では 3 つすべて NO → pivot が正解だった。

### Step 2: 既製スタック移行

- Agent runtime → Claude Code (Max 20x)
- Sandbox → Docker / git worktree
- Context 管理 → MCP
- 評価 → 自作 Validator Sub-agent (`.claude/agents/validator.md`)
- Phase 分離 → LangGraph (使う場合のみ) または Anthropic Ralph loop

### Step 3: 規律の移植

旧資産の認知の分離 (session-pre / worker / judge / observation 等) を Claude Code Skills に移植:

- `~/.claude/skills/session-planner/SKILL.md` ← 旧 session-pre
- `~/.claude/skills/worker/SKILL.md` ← 旧 worker_report
- `~/.claude/skills/judge-4axis/SKILL.md` ← 旧 judge (4 軸検証)
- `~/.claude/skills/reporter/SKILL.md` ← 旧 observation

これにより**「認知の分離」は残し、「運搬手段 (orchestrator)」は捨てる**。

### Step 4: 2 週間 Hard Gate 検証

移行先で 2 週間以内に「自作 orchestrator 時代と同等以上の output」を出す。出なければ再 pivot。

---

## 6. Friday public post 運用

### 6.1 目的

- 自己への報告義務化 (見られている前提で書く)
- 凍結兆候の早期可視化 (連続失敗で警鐘)
- 外部からのフィードバック受領 (KUNIHIDE が気づかない指摘)
- 業界貢献 (同じ失敗を他の個人事業主が回避できる)

### 6.2 投稿構造
