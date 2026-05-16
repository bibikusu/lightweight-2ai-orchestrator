# V2-Z2-INVENTORY 分類結果

**作成日**: 2026-05-16  
**作成者**: Builder #2 (Window 2)  
**sandbox branch**: sandbox/window-2-z2  
**対象**: untracked ファイル 31 件の 4 区分分類  
**注意**: 実削除/移動は V2-Z3 で実施。本ドキュメントは分類案の正本。  
**並行作業注記**: Window 1 が本セッション中に `strategy/`（top-level）を `docs/strategy/` へ移動して追跡化済み。また Window 3 が `docs/strategy/skills-template/` を新規作成（Window 3 スコープのため本 Window は不触）。

---

## A. 削除候補（即削除して良いもの） — 3 件

| ファイル/ディレクトリ | 理由 |
|---|---|
| `.pcc.pid` | PID 22026 を格納するランタイム一時ファイル。プロセス管理用で恒久保持の価値なし。 |
| `.playwright-mcp/` | Playwright MCP の実験ログ・スクリーンショット（2026-05-06 のみ）。過去1回の実験痕跡。コンテンツは logs + PNG 計4ファイル。保持価値なし。 |
| `files.zip` | completion_report / diff_summary / run_log のアーカイブ（9KB）。内容は docs/sessions 等に記録済みの成果物と重複する一時パッケージ。 |

---

## B. archive 候補（V2-Z3 で archive/orchestrator-frozen-2026-05 ブランチへ退避） — 5 件

| ファイル/ディレクトリ | 理由 |
|---|---|
| `.claude/settings.json.bak_20260508_governance_pause` | governance pause 時（2026-05-08）の settings.json バックアップ。history 参照用として archive に保持する価値はあるが、運用上 .claude/ 配下に残す必要はない。 |
| `.claude/worktrees/` | 過去セッション（10ディレクトリ）の git worktrees。2026-05-11〜14 に作成。現在は使用されていない残骸。git worktree remove コマンドによる正規クリーンアップが必要（rm -rf 禁止）。 |
| `DL/` | 外部 OSS 参考リポジトリ群（agent-for-debate / collab-ai / Multi-LLM-Orchestration-System / spec-kit）+ 監査レポート txt。旧 orchestrator 設計時の調査資料（37MB）。V2 体制では直接参照しないが、設計の背景として archive 保持。 |
| `docs/DASHBOARD.md` | 旧ダッシュボード（最終更新 2026-05-06、session-179 参照）。V2 体制では新体制のダッシュボードを別途整備するため、旧版として archive 退避。 |
| `docs/handoff/` | session-185 用の ClaudeCode 投入文（claudecode_prompt_session-185.md）。session-185 完了後の残留物。完了済みセッション資料として archive 退避。 |

---

## C. 継承候補（V2 体制でも使い続ける） — 22 件

| ファイル/ディレクトリ | 理由 |
|---|---|
| `docs/strategy/skills-template/` | Window 3（V2-Z5-SKILLS-MIGRATION）が作成した Skills 雛形 4 件（session-planner / worker / judge-4axis / reporter）。V2 体制の中核リソース。**Window 3 スコープ**のため V2-Z3 では不触。git add は Window 3 が担当。 |
| `docs/acceptance/session-196-ops-pre.yaml` | session-196-ops-pre の acceptance YAML 正本。完了セッションの検収記録。 |
| `docs/acceptance/session-198-pre.yaml` | session-198-pre の acceptance YAML 正本。完了セッションの検収記録。 |
| `docs/contracts/session_throughput_fastlane_v0.md` | Fastlane 契約書（session-196-ops-pre 成果物）。現行運用中の canonical contract。 |
| `docs/projects/A01_Card_task/` | A01 プロジェクト state.json。V2 体制で継続追跡するプロジェクト状態。 |
| `docs/projects/A02_fina/state.json` | A02 fina の state.json（parent_spec.md は既追跡済み）。 |
| `docs/projects/A03_mane_bikusu/` | A03 mane.bikusu state.json。 |
| `docs/projects/A04_deli_customer_management/` | A04 deli 顧客管理 state.json。 |
| `docs/projects/A05_CAST_PRO/` | A05 CAST PRO state.json。 |
| `docs/projects/A06_cecare/` | A06 cecare state.json。 |
| `docs/projects/A07_pochadeli_work/` | A07 Pochadeli Work state.json。 |
| `docs/projects/A08_AI_video_creation/` | A08 AI Video Creation state.json。 |
| `docs/projects/A09_AI_movie_production/` | A09 AI Movie Production state.json。 |
| `docs/projects/A10_fina_date/` | A10 fina_date state.json。 |
| `docs/sessions/session-196-ops-pre.json` | session-196-ops-pre の 14-key JSON 正本。完了セッション記録。 |
| `docs/sessions/session-198-pre.json` | session-198-pre の 14-key JSON 正本。完了セッション記録。 |
| `docs/specs/next_action_artifact_contract_v0.md` | next_action artifact 契約（filesystem-first/relay 非必須）。現行運用中の canonical spec。 |
| `docs/specs/sandbox_autonomy_contract.md` | サンドボックス自律境界契約。session-198-pre 成果物。現行運用中の正本。 |
| `docs/templates/terminal_short_verification_v0.md` | Terminal 短文検証テンプレート。現行運用中。 |
| `tests/test_session_validate.py` | tools/session_validate.py のユニットテスト。ツールと一体で継続使用。 |
| `tools/` | session_validate.py（セッション静的バリデーター）。V2 体制で継続使用。 |
| `軽量２AIオーケストレーター.txt` | プロジェクト原点の音声認識テキスト（A01〜A12 の構想ヒアリング記録）。歴史的参考資料として保持。 |

---

## D. KUNIHIDE 判定要請（判断不能なもの） — 1 件

| ファイル/ディレクトリ | 不明点 |
|---|---|
| `docs/proposals/` | session-197-pre / session-198-pre 用の staging artifact を格納（xline/ 境界マトリクス等を含む）。session-198 は完了済みだが、session-197 は V2 session-plan.yaml には対応するセッション ID が見当たらない。旧 orchestrator 体制の197番セッションと V2 体制は連番が異なる可能性がある。**判定依頼**: session-197 に相当する作業が V2 体制でも残っているか。残るなら継承、廃止なら archive。 |

---

## 集計

| 区分 | 件数 |
|---|---|
| A. 削除候補 | 3 |
| B. archive 候補 | 5 |
| C. 継承候補 | 22 |
| D. KUNIHIDE 判定要請 | 1 |
| **合計** | **31** |

---

## V2-Z3 への引き渡し事項

- `.claude/worktrees/` は `git worktree remove` で正規削除（`rm -rf` 不可）
- `DL/` は 37MB あるため archive branch への移動コストに注意
- `strategy/`（top-level）は Window 1 が本セッション中に `docs/strategy/` へ移動・追跡化済み（V2-Z4 作業に向けて解決済み）
- `docs/strategy/skills-template/` は Window 3 スコープのため V2-Z3 では不触、Window 3 が git add する
