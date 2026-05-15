# Terminal Short Verification Template v0

## 1. Document Identity

- Document type: template (canonical)
- Version: v0
- Status: frozen
- Session: [`docs/sessions/session-196.json`](../sessions/session-196.json)
- Related: [`docs/specs/next_action_artifact_contract.md`](../specs/next_action_artifact_contract.md)

## 2. Purpose

This template defines the deterministic short verification format for session completion checks.
It is restricted to short-text, binary-outcome verification only.

Prose explanation, partial results, and ambiguous states are prohibited in verification output.

## 3. Verification Format

### 3.1 Per-Criterion Line

```
[PASS|FAIL] <criterion_id>: <one-line description>
```

Rules:
- Exactly one `[PASS]` or `[FAIL]` per criterion.
- `<criterion_id>` must match the `id` field in `completion_criteria`.
- `<one-line description>` is the `condition` field verbatim or a deterministic abbreviation.
- No multi-line output per criterion.

### 3.2 Summary Line

```
GO|HOLD|FAIL  session: <session_id>  criteria: <pass_count>/<total_count>
```

Rules:
- Exactly one summary line at the end of the verification output.
- Outcome is determined by GO/HOLD/FAIL routing semantics defined in
  `docs/specs/next_action_artifact_contract.md` Section 4.
- `<pass_count>` is the count of PASS results.
- `<total_count>` is the total count of evaluated criteria.

## 4. Filesystem-First Check Sequence

The following sequence is fixed and must not be reordered:

1. For each `completion_criteria` item with `type: artifact`: check existence on filesystem.
2. For each existing artifact: verify content condition if specified in `condition`.
3. Check for `forbidden_changes` violations (`git diff --name-only`).
4. For each `completion_criteria` item with `type: document_rule`: verify the stated rule holds.
5. For each `completion_criteria` item with `type: side_effect_free`: verify no unintended changes.
6. For each `completion_criteria` item with `type: non_regression`: verify no regression.
7. For each `completion_criteria` item with `type: state_transition_consistent`: verify state consistency.
8. Record each result as PASS or FAIL.
9. Apply GO/HOLD/FAIL routing and emit summary line.

Relay artifact presence does not alter this sequence. Filesystem audit takes precedence.

## 5. Constraints

- This template is documentation only. No executable code is defined here.
- Output format is fixed. Extension requires a new session.
- Relay artifact absence is not a FAIL unless the artifact is a required `completion_criteria` condition.
- Verification is reproducible: the same filesystem state must produce the same output.

## 6. Examples

### 6.1 Full Pass (GO)

```
[PASS] CC-196-01: docs/sessions/session-196.json が保存されている
[PASS] CC-196-02: docs/acceptance/session-196.yaml が保存されている
[PASS] CC-196-03: docs/specs/next_action_artifact_contract.md が保存されている
[PASS] CC-196-04: docs/templates/terminal_short_verification.md が保存されている
[PASS] CC-196-05: artifact relay を mandatory にしない旨が明記されている
[PASS] CC-196-06: filesystem-first audit が primary と明記されている
GO  session: session-196  criteria: 6/6
```

### 6.2 Partial Fail (FAIL)

```
[PASS] CC-196-01: docs/sessions/session-196.json が保存されている
[FAIL] CC-196-02: docs/acceptance/session-196.yaml が保存されていない
FAIL  session: session-196  criteria: 1/2
```

### 6.3 Human Decision Required (HOLD)

```
[PASS] CC-196-01: docs/sessions/session-196.json が保存されている
[PASS] CC-196-02: docs/acceptance/session-196.yaml が保存されている
[HOLD] CC-196-07: GO/HOLD/FAIL routing semantics の人間確認が未完了
HOLD  session: session-196  criteria: 2/3
```
