---
applyTo: "ai_workflow/**,scripts/**"
description: "Developer gate enforcement rules for issue workflows. Prevents committing without app.py changes, test deltas, and UI regression coverage."
---

# Developer Gate — Enforcement Rules

These rules apply to every AI persona that executes issue workflow steps.
Violations MUST raise a `RuntimeError` that triggers workflow BLOCK.

## Gate 1 — Functional Coverage

Before committing, verify that at least one **product source file** has changed.

**Product source files** (must have at least one change for feature issues):
- `app.py`

**Infrastructure-only files** (changes here alone DO NOT satisfy Gate 1):
- `ai_workflow/`
- `scripts/`
- `workflow_dashboard.py`
- `playwright.config.ts`
- `playwright-results.json`
- `playwright-report/`
- `test-results/`

**Check logic:**
```python
changed = git diff --cached --name-only
if no product file in changed and issue_is_feature:
    BLOCK("Gate 1 FAILED: No product file (app.py) was changed.")
```

## Gate 2 — Unit Test Delta

Before marking unit tests as passed, verify a new or modified test exists.

**Required evidence:**
- At least one test function in `tests/test_app.py` that was added or modified in this branch.
- The test name must reference the feature keyword (e.g., "weekly", "bi_weekly", "biweekly").

**Check logic:**
```python
diff = git diff origin/main -- tests/test_app.py
if diff is empty:
    BLOCK("Gate 2 FAILED: No unit test was added or modified for this feature.")
```

## Gate 3 — UI Regression Test Delta

Before marking UI tests as passed, verify new Playwright coverage exists.

**Required evidence:**
- At least one `.spec.ts` file in `ui-tests/regression/` was added or modified in this branch.
- The spec must contain the new UI option label text (e.g., `"Bi-Weekly"`, `"Weekly"`).

**Check logic:**
```python
diff = git diff origin/main -- ui-tests/
if diff is empty:
    BLOCK("Gate 3 FAILED: No Playwright regression test was added or modified for this feature.")
```

## Gate 4 — PR Traceability

The PR body must include these sections:
```
## Implementation
- Changed: <file(s)> — <why>

## Unit Tests
- Added/updated: <test names>

## UI Regression Tests  
- Added/updated: <spec file and scenario names>

## Acceptance Criteria
- [x] <criterion 1 from issue>
- [x] <criterion 2 from issue>
```

If any acceptance criterion checkbox is unchecked, **BLOCK** PR creation.
