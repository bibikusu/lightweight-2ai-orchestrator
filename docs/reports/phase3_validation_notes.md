# Phase3 Validation Notes

## 1. Live-run sessions handling

session-88 and session-92 are NOT judged by standard success criteria.

- session-88:
  - status: dry_run
  - completion_status: conditional_pass
  - accepted as manual verification session

- session-92:
  - status: failed
  - completion_status: stopped
  - accepted because forbidden path guard correctly triggered

## 2. API usage behavior

- api_usage may be empty depending on provider response
- acceptance is based on:
  - api_call_count recorded
  - cost_summary generated
  - integration path verified

## 3. Completion evaluation integration

- evaluate_completion_decision is NOT replacing decide_completion_status
- result is stored in:
  - phase2_completion_eval

## 4. Prompt hardening effects

- unified diff requirement enforced
- patch_status constrained to valid enum
- retry_instruction expanded into:
  - fix_instructions
  - do_not_change

## 5. Acceptance philosophy

Phase3 acceptance criteria:

- Guard effectiveness > success status
- Integration correctness > output success
- Runtime safety > patch success

## 6. Scope clarification

- session-90 was removed (merged into session-89)
- no unused session definitions remain

