# Queue Execution Engine Specification (P6C canonical)

本仕様は P6C 実装(session-137 以降)の前提となる queue 実行エンジンの責務、状態モデル、ルーティングを正本化する。

---

## 1. 責務分離(queue engine vs run_session.py)

queue engine と run_session.py は、**制御レイヤー** と **実行レイヤー** に分離する。両者は互いに内部関数を呼ばず、subprocess 境界のみで接続する。

### 1.1 run_session.py の責務(不変・既存)

- 1 セッションの実行
- 仕様検証(acceptance)
- retry(同一セッション内で最大 1 回)
- artifacts / state.json / retry_history.json の生成

### 1.2 queue engine の責務(新規・P6C)

- dispatch(実行対象の選択と起動指示)
- concurrency 制御(parallel / serial の判定)
- routing(run_session 結果を受けた次状態の決定)
- persistence(queue 状態の永続化)

### 1.3 接続契約

queue engine から run_session.py への呼び出しは **subprocess 経由のみ**とする。
subprocess.run([
"python", "orchestration/run_session.py",
"--session-id", <session_id>,
"--project", <project_id>,
])

queue engine は `from orchestration.run_session import ...` を禁止する。これにより run_session.py の内部実装変更が queue engine に波及しない。

---

## 2. Queue 状態モデル(7状態 enum)

queue item が取りうる状態は以下の 7 値のみとする。

| value | 意味 |
|---|---|
| `pending` | 新規 enqueue 直後、policy 判定待ち |
| `ready` | policy 判定 pass、concurrency slot 待ち |
| `running` | run_session.py を subprocess で実行中 |
| `retry_waiting` | retry 対象の failure、再 ready 待ち |
| `blocked_human` | human gate 発動、人間承認待ち |
| `completed` | success 終了 |
| `failed` | retry 上限到達、または復帰不能 failure |

状態遷移図:
[pending]
│ policy 判定 pass
▼
[ready]
│ concurrency slot 空き
▼
[running] ── subprocess: run_session.py ──
│
├── success ────────────────────────► [completed]
│
├── retry 対象 failure_type
│   + retry_count < max_retry
│                                     ▼
│                              [retry_waiting]
│                                     │ 次 dispatch
│                                     ▼
│                                  [ready]
│
├── retry 対象 failure_type
│   + retry_count >= max_retry ────► [failed]
│
└── human gate 対象 failure_type
or deploy_risk == critical ────► [blocked_human]
│ 人間承認
▼
[ready] or [failed]

---

## 3. Parallel / Serial 制御対応表(deploy_risk 基準)

`docs/config/project_registry.json` の `deploy_risk` と、`docs/config/queue_policy.yaml` の `execution_rules`(例: `isolation` による parallel / serial)、`night_batch`、`blocked_queue` / `waiting_human_queue` の route 条件を解釈し、実行モードを決定する。

| deploy_risk | 実行モード | 同時実行可否 |
|---|---|---|
| `low` | parallel | 他の low / medium と同時可 |
| `medium` | parallel(制限付き) | 同プロジェクト内 serial、他プロジェクトとは parallel 可 |
| `high` | serial | 同時 1 件のみ |
| `critical` | serial + human_gate | 実行前に必ず `blocked_human` を経由 |

`max_parallel` は v1 では 1 固定とする(実運用で調整)。

解釈の優先順位: 本表は queue レイヤーの要約である。registry の事実フィールドと `queue_policy.yaml` の条件式が競合する場合は **queue_policy.yaml の正本ルールを優先**する。

---

## 4. Retry Route 対応表(failure_type 基準)

run_session.py が返す failure_type に基づき、queue engine が次状態を決定する。分岐は `docs/config/queue_policy.yaml` の `retry_policy`(`route_to_retry_queue_on` / `route_to_waiting_human_on`)と整合させる。

| failure_type | next state(retry 可否) | 根拠 |
|---|---|---|
| `test_failure` | `retry_waiting`(retry_count < 1) | 一時的失敗の可能性、1回再試行で救済 |
| `type_mismatch` | `retry_waiting`(retry_count < 1) | 同上 |
| `build_error` | `retry_waiting`(retry_count < 1) | 同上 |
| `import_error` | `retry_waiting`(retry_count < 1) | 同上 |
| `scope_violation` | `blocked_human` | 仕様外変更は人間判定必須 |
| `regression` | `blocked_human` | 既存破壊は人間判定必須 |
| `spec_missing` | `blocked_human` | policy 上は waiting_human ルート(`route_to_waiting_human_on` に列挙) |
| その他 / 未分類 | `failed` | 安全側 fallback |

retry 上限は `max_retry = 1` に固定(v1)。retry_count >= max_retry のとき、retry 対象 failure_type であっても `failed` に遷移する。

---

## 5. Human Gate 発動条件

以下のいずれかを満たすとき、queue item は `blocked_human` に遷移する。
human_gate_triggered := (
deploy_risk == "critical"
OR failure_type in {"scope_violation", "regression", "spec_missing"}
)

`deploy_risk == "critical"` は他条件より優先される(critical は常に human_gate 通過)。

補足: `queue_policy.yaml` の `human_gate.required_if` は registry フィールドに対する構造化条件として定義されている。queue engine は当該 YAML を読み取り同一の論理となるよう実装する。

`blocked_human` から復帰するのは人間承認後のみ。承認結果に応じて `ready`(再試行)または `failed`(中止)に遷移する。承認プロセス自体は P6C scope 外(scheduler / dashboard 実装後に追加)。

---

## 6. Persistence

queue 状態は `orchestration/queue/queue_state.json` に JSON 形式で永続化する。

- atomic write: 一時ファイルへ書き出し後 rename
- シングルスレッド前提、排他制御なし
- SQLite は v1 では導入しない(p6c 完了後に検討)

---

## 7. v1 での不採用事項(明示)

本仕様で **v1 の queue engine に含めないもの**:

- scheduler(cron / systemd timer / webhook 起動)
- 並列書き込み対応
- queue 用 CLI エントリポイント
- SQLite 永続化
- dashboard / 管理 UI
- 複数プロジェクト同時実行の本番有効化
- retry 2 回以上
- human gate からの自動復帰

これらは P6D 以降または別フェーズで扱う。

---

## 8. 改訂履歴

- 2026-04-19: 初版(session-136, P6C-pre)。
