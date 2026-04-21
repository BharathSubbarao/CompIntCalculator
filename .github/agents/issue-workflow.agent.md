---
name: issue-workflow
description: "Run end-to-end Git issue workflow with PO, Developer, Unit Tester, UI Tester, and PR creation for CompIntCalculator."
---

Run these steps in order and stop on any unresolved blocker:

## Step 1 — Product Owner
Refine the issue into the required template. Extract the exact functional requirement from the issue title and body.

## Step 2 — Developer (Gate 1 required)
1. Read `app.py` to understand current implementation.
2. Identify exactly what must change to satisfy the issue requirement.
3. Make the code change in `app.py` (or the relevant file) NOW — before branch creation or commits.
4. **BLOCK** if the issue is a product feature (e.g., new dropdown option, new calculation mode) but `app.py` has not been modified.
5. **BLOCK** if the only changed files are infra/workflow: `ai_workflow/`, `scripts/`, `workflow_dashboard.py`, `playwright.config.ts`.
6. After making the change, create branch and commit only the meaningful source changes.

## Step 3 — Unit Tester (Gate 2 required)
1. Open `tests/test_app.py` and identify the existing test patterns.
2. Add new test(s) or update existing ones to directly cover the new behavior.
3. Test function names must reference the feature (e.g., `test_weekly_frequency_compounds_correctly`).
4. **BLOCK** if no test in `tests/test_app.py` covers the implemented change.
5. Run `bash scripts/run_tests_with_log.sh` and assert all pass.

## Step 4 — UI Tester (Gate 3 required)
1. Open the relevant Playwright spec files in `ui-tests/regression/`.
2. Add or update a scenario that verifies the new UI element or behavior is visible and functional.
3. **BLOCK** if no Playwright test references the new UI option by name (e.g., "Bi-Weekly" in a selectbox test).
4. Run `bash scripts/run_ui_regression.sh` and assert all pass.

## Step 5 — Pull Request (Gate 4 required)
1. PR title: `Issue #N: <feature description>`.
2. PR body must contain a traceability checklist:
   - `app.py` line(s) changed and why
   - unit test(s) name(s) added/updated in `tests/test_app.py`
   - Playwright test(s) name(s) added/updated in `ui-tests/regression/`
3. **BLOCK** if any acceptance criterion from the issue is not covered by the changes above.

On blocker, mark workflow blocked and escalate through the orchestrator.