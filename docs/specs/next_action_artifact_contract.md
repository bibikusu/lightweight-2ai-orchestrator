# next_action Artifact Contract v0

## 1. Document Identity

- Document type: spec (contract freeze)
- Version: v0
- Status: frozen
- Session: [`docs/sessions/session-196.json`](../sessions/session-196.json)
- Related:
  - Schema: [`docs/schemas/next_action_v0.json`](../schemas/next_action_v0.json)
  - Contract: [`docs/contracts/orchestration_contract_v0.md`](../contracts/orchestration_contract_v0.md)
  - Enums: [`docs/contracts/orchestration_enums_v0.md`](../contracts/orchestration_enums_v0.md)
  - Verification template: [`docs/templates/terminal_short_verification.md`](../templates/terminal_short_verification.md)

## 2. Purpose

This document freezes the following contracts as canonical:

- next_action artifact contract
- filesystem-first relay contract
- Terminal short verification contract
- GO/HOLD/FAIL routing semantics

It is descriptive only. Runtime implementation of any routing logic is out of scope.

## 3. next_action Artifact Contract

### 3.1 Structural Reference

The structural definition of `next_action` is the canonical source at `docs/schemas/next_action_v0.json`.
This document does not duplicate that definition.

The variant enum canonical values are:

- `next_session_id`
- `next_human_action`
- `next_prompt_for_ai`
- `next_sandbox_op`

These values are structural invariants defined in `docs/schemas/next_action_v0.json`
and described in `docs/contracts/orchestration_contract_v0.md`.

### 3.2 Relay Contract (filesystem-first)

- **Artifact relay is NOT mandatory.** A session may complete without producing a relay artifact.
- **Filesystem-first audit is the PRIMARY verification method.**
- Relay artifact, if present, is supplementary evidence only. It does not take precedence over filesystem state.
- Absence of a relay artifact is not a verification failure unless the artifact is listed as a required `completion_criteria` condition.

### 3.3 Filesystem-First Audit (Primary)

Primary verification proceeds in the following fixed sequence:

1. For each `completion_criteria` item with `type: artifact`, check existence on filesystem (`ls` / `find` / `cat`).
2. For each existing artifact, verify content condition against the `condition` field.
3. Check for `forbidden_changes` violations (`git diff --name-only`).
4. Record each criterion result as PASS or FAIL.
5. Apply GO/HOLD/FAIL routing per Section 4.

Filesystem audit takes precedence over relay artifact in all cases.

## 4. GO/HOLD/FAIL Routing Semantics

### 4.1 Definitions (canonical, one-to-one)

| Outcome | Condition |
|---|---|
| **GO** | All `completion_criteria` are satisfied AND no `forbidden_changes` violation detected AND no regression |
| **HOLD** | One or more `completion_criteria` are incomplete OR human decision is required to proceed |
| **FAIL** | Any of: `forbidden_changes` violation / regression detected / `spec_missing` / required artifact existence check failed |

These three outcomes are mutually exclusive. A session result is exactly one of GO, HOLD, or FAIL.

### 4.2 Routing Rules

- **GO** → session closes; handoff to next session or human as specified in `next_action`.
- **HOLD** → session pauses; human or commander decision required before proceeding.
- **FAIL** → session stops immediately; `failure_type` is recorded; no handoff proceeds.

### 4.3 Constraints

- Routing is deterministic given the criterion result set.
- No ambiguous state is permitted between GO, HOLD, and FAIL.
- A session cannot simultaneously produce GO and HOLD.
- FAIL takes precedence over HOLD when both conditions are present.

## 5. Terminal Short Verification Contract

Terminal short verification is limited to deterministic short-text checks. The canonical template is
at `docs/templates/terminal_short_verification.md`.

Constraints on short verification:

- Each check produces exactly one binary result: PASS or FAIL.
- No prose explanation is required in the verification output itself.
- Verification is reproducible given the same filesystem state.
- The verification sequence is defined in Section 3.3 (filesystem-first).

## 6. Out of Scope

The following are explicitly not covered by this document:

- Runtime implementation of GO/HOLD/FAIL routing logic.
- Queue or scheduler behavior triggered by routing outcomes.
- Dashboard UI representation of routing state.
- Provider behavior.
- Sandbox autonomy implementation.
- Variant-to-shape selection rule (deferred to 198-pre).
- Projection and PCC semantics (deferred to 197-pre).
