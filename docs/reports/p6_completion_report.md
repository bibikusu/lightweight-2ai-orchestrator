# P6 Completion Report

**Phase**: P6 — Execution baseline (queue + scheduler)
**Status**: ✅ completed
**Completion date**: 2026-04-19

---

## 1. サブフェーズ完了状況

| Phase | 内容 | Session | main commits |
|---|---|---|---|
| P6A | project_registry + queue_policy 正本化 | session-134 | d2d19bd |
| P6B | run_session 統合(loader + DSL + 4 decisions + CLI) | session-135 | de288bf, c6efc16 |
| P6C-pre | queue engine 責務正本化 | session-136, 136a | 987fbcf, c9c136a |
| P6C | 最小 queue 実行エンジン実装 | session-137 | d05c938, 692529c |
| P6D | 最小 scheduler 実装 | session-138 (+fix) | 834bfc5, 08d3141, d4c796e |

---

## 2. 責務分離(3層)
┌──────────────────────────────────────────────┐
│ Layer: trigger(scheduler)                     │
│   - 時刻評価(JST, ISO weekday 1-7)            │
│   - plan マッチング                           │
│   - CLI: --now / --plan-id                   │
│   - QueueEngine を直接 import(同一プロセス)    │
└──────────────────────────────────────────────┘
│
▼
┌──────────────────────────────────────────────┐
│ Layer: control(queue engine)                 │
│   - dispatch(実行対象の選択)                  │
│   - concurrency 制御                          │
│   - routing(failure_type → next state)       │
│   - persistence(queue_state.json)            │
│   - run_session は subprocess で呼ぶ           │
└──────────────────────────────────────────────┘
│ subprocess.run
▼
┌──────────────────────────────────────────────┐
│ Layer: execution(run_session.py)             │
│   - 1 セッション実行                          │
│   - acceptance 検証                           │
│   - retry(v1: max 1)                         │
│   - artifacts / state.json 生成               │
└──────────────────────────────────────────────┘

### 境界ルール(不変)

- scheduler は run_session を直接 import してはならない
- queue engine は run_session を直接 import してはならない
- queue engine から run_session への呼び出しは subprocess 経由のみ
- scheduler から queue engine への呼び出しは直接 import(同一プロセス)
- scheduler は QueueEngine の公開 API のみを使用する(private メンバー禁止)

---

## 3. main 上の成果物

### コード(orchestration/)

- `orchestration/queue/` (4 files: `__init__.py`, `state.py`, `store.py`, `engine.py`)
- `orchestration/scheduler/` (3 files: `__init__.py`, `plan_loader.py`, `cron_runner.py`)

### テスト(tests/)

- `tests/queue/test_queue_engine.py` (6 tests passed)
- `tests/scheduler/test_scheduler.py` (5 tests passed)

### 設定(docs/config/)

- `docs/config/project_registry.json`
- `docs/config/queue_policy.yaml`
- `docs/config/scheduler_plans.yaml`

### 仕様(docs/specs/)

- `docs/specs/queue_engine_spec.md`

### セッション定義(docs/sessions/)

- session-134, 135, 136, 136a, 137, 138, 139

### acceptance 定義(docs/acceptance/)

- session-134, 135, 136, 136a, 137, 138, 139

---

## 4. 検証 gate(main 上)

| Gate | 結果 |
|---|---|
| ruff | ✅ All checks passed |
| pytest | ✅ 11 tests passed(queue: 6, scheduler: 5) |
| mypy | ✅ no issues found |
| compileall | ✅ passed |

---

## 5. Open Issues(技術未解決)

| ID | カテゴリ | 内容 | 持ち越し先 |
|---|---|---|---|
| OI-P6-01 | technical | queue_policy DSL の完全評価未実装(db_touch_allowed など) | P7 or later |
| OI-P6-02 | technical | failure_type 抽出が subprocess stdout 前提(artifacts/report.json 経路は未) | P7 or scheduler 実 cron 統合時 |
| OI-P6-03 | technical | queue priority 未実装(現状 created_at/id 順) | v2 以降 |
| OI-P6-04 | technical | `force_plan_id` が内部 API 扱い(公式公開 API 判定未) | P7 |

---

## 6. Operational Backlog(運用改善、技術以外)

| ID | 内容 | 対応予定 |
|---|---|---|
| BACKLOG-CURSOR-COMMIT-GUARD-001 | Cursor commit 忘れ対策(session-137/138 で 2 回発生) | P7(Claude Code Hooks) |
| BACKLOG-QUEUE-TEST-SPEC-MISSING-001 | scheduler test に spec_missing 明示ケース追加 | 10 分 BACKLOG、低優先度 |

---

## 7. P7 への入力条件(固定済)

### QueueEngine 公開 API(変更禁止)
QueueEngine.init(store, registry_path, policy_path, max_parallel=1)
QueueEngine.enqueue(session_id, project_id) -> QueueItem
QueueEngine.dispatch_ready() -> list[QueueItem]
QueueEngine.run_next() -> QueueItem | None
QueueEngine.route_after_run(item, exit_code, failure_type) -> QueueItem

### scheduler 責務(変更禁止)

- scheduler は「いつ・何を enqueue するか」だけ担当する
- routing / retry / failure は queue engine の責務
- 時刻は JST + ISO weekday(1-7)
- CLI は `--now` (ISO8601) と `--plan-id` を受け付ける

### run_session.py CLI 契約(変更禁止)

- 起動: `python orchestration/run_session.py`
- 必須: `--session-id <id>`
- 任意: `--project <id>`
- failure_type 出力: stdout JSON 契約(v1 現行)
- exit code: 0=success, non-zero=failure

---

## 8. 次フェーズ

- **P7(Claude Code Hooks + MCP 統合)**: 着手可能状態
- **起点セッション**: session-140(P7-pre 責務正本化)
- **期待効果**: Cursor 依頼の自動化、commit guard、4-gate 自動実行

---

## 9. 最終判定

- **結果**: completed
- **根拠**: P6A〜P6D すべてが completed、main 上の gate 全 pass、責務分離文書化済、open issues 分類済、P7 入力条件固定済
- **署名**: Cursor(実装)/ Claude(参謀)/ GPT(司令塔)
