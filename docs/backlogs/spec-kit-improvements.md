# BACKLOG: Spec Kit 比較分析から生まれた改善候補

**作成日**: 2026-04-24  
**参照元**: DL/spec-kit-analysis/improvement_proposals.md  
**ステータス**: BACKLOG（session 起票・実装は未着手）

---

## BACKLOG-SPEC-KIT-01
**タイトル**: session JSON への `background` / `user_scenarios` フィールド任意追加  
**優先度**: 中  
**対応する Spec Kit 要素**: `spec-template.md > Assumptions` / `User Scenarios & Testing`

### 概要
session-XX.json に以下の任意フィールドを追加する。省略時は既存の動作を維持。

- `background.context`: セッションが必要になった経緯（1〜3文）
- `background.preconditions`: 前提条件リスト
- `background.assumptions`: 仮定リスト
- `user_scenarios[]`: Given-When-Then 形式のユーザーシナリオ（優先度 P1/P2/P3 付き）

### 前提条件（着手ブロッカー）
**Pydantic 型付けの導入が先決**。Instructor による session JSON の型バリデーション導入後に、新フィールドの型定義を schema に追加する形で実施する。オーケストレーター側（`run_session.py`）の SessionContext 変更が必要。

### 影響範囲
- `docs/sessions/session-XX.json`（追加のみ、後方互換）
- `orchestration/run_session.py`（SessionContext dataclass への任意フィールド追加）

---

## BACKLOG-SPEC-KIT-02
**タイトル**: `global_rules.md` への version frontmatter 追加  
**優先度**: 低  
**対応する Spec Kit 要素**: `constitution-template.md > Governance > Version/Ratified/Amended`

### 概要
`global_rules.md` の先頭に YAML frontmatter または Markdown メタデータブロックとして以下を追加する。

```markdown
<!-- version: 1.2.0 | last_amended: 2026-04-24 | status: canonical -->
```

または YAML frontmatter 形式（対応ツールがあれば）:

```yaml
---
version: "1.2.0"
ratified: "2025-XX-XX"
last_amended: "2026-04-24"
status: canonical
---
```

### 方針メモ
- `constitution.md` の新規作成は**しない**（正本の分散を防ぐため）
- `global_rules.md` と `master_instruction.md` が正本のまま、version 情報のみ付加
- git log で履歴を追える現状でも十分。このタスクは「Spec Kit との形式的な互換性確保」が目的

### 前提条件
なし。ただし `global_rules.md` の改変には KUNIHIDE の明示的な承認が必要。

---

## BACKLOG-SPEC-KIT-03
**タイトル**: `session_schema.json` 新規作成（JSON Schema 形式）  
**優先度**: 中  
**対応する Spec Kit 要素**: `tasks-template.md` の構造化・型定義の明示

### 概要
`docs/sessions/` 配下に JSON Schema ファイルを新規作成する。  
`_template.json`（記入例）ではなく、**機械検証可能な JSON Schema 形式**で session 定義の型・必須フィールドを定義する。

```
docs/config/session_schema.json   # ← 新規作成対象
```

想定するスキーマ構造:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SessionDefinition",
  "required": ["session_id","phase_id","title","goal","scope","acceptance_criteria","completion_criteria","review_points"],
  "properties": {
    "session_id":   { "type": "string", "pattern": "^session-[0-9]+" },
    "phase_id":     { "type": "string" },
    "review_points":{ "type": "array", "items": {"type": "string"}, "minItems": 4, "maxItems": 4 },
    "acceptance_criteria": {
      "type": "array",
      "items": {
        "required": ["id","description"],
        "properties": {
          "id": { "type": "string", "pattern": "^AC-" },
          "test_name": { "type": "string" }
        }
      }
    },
    "background":          { "type": "object" },
    "user_scenarios":      { "type": "array" },
    "tech_context":        { "type": "object" },
    "constitution_check":  { "type": "array" },
    "design_decisions":    { "type": "array" },
    "implementation_phases":{ "type": "array" }
  }
}
```

### 用途
- CI での `jsonschema` コマンドによる session 定義の自動バリデーション
- エディタの JSON Schema 補完機能との統合（VS Code 等）
- BACKLOG-SPEC-KIT-01 の任意フィールドをスキーマ上で型安全に定義

### 前提条件
なし。ただし `docs/config/` への追加であり、`project_registry.json` / `queue_policy.yaml` の改変は行わない。
