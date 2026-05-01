---
name: issue-workflow
description: "Run end-to-end Git issue workflow with PO, Developer, Unit Tester, UI Tester, and PR creation for CompIntCalculator."
---

## Workflow State Tracking — NON-NEGOTIABLE RULES

State writes are **blocking requirements**. You MUST run the state update command and confirm it prints `[OK]` before proceeding with any step's work. If the command exits non-zero or does not print `[OK]`, STOP and report the error.

**State updater**: `scripts/update_workflow_state.py`
**State file location**: `.workflow/state/<workflow_id>.json`
**Workflow ID format**: `issue-<N>-<YYYYMMDDHHMMSS>` (use current UTC time)

### State update command reference

```bash
# 1. Create initial state file (run ONCE before Step 1)
python3 scripts/update_workflow_state.py \
  --init --workflow-id <workflow_id> --issue-number <N>

# 2. Mark step IN_PROGRESS (run BEFORE starting any step's work)
python3 scripts/update_workflow_state.py \
  --workflow-id <workflow_id> --step <1-5> --status IN_PROGRESS

# 3. Mark step COMPLETED (run AFTER step's work succeeds)
python3 scripts/update_workflow_state.py \
  --workflow-id <workflow_id> --step <1-5> --status COMPLETED

# 4. Mark step BLOCKED (run on any gate failure — then STOP)
python3 scripts/update_workflow_state.py \
  --workflow-id <workflow_id> --step <1-5> --status BLOCKED \
  --error "<exact gate failure reason>"

# 5. Mark entire workflow COMPLETED (run after Step 5 COMPLETED)
python3 scripts/update_workflow_state.py \
  --workflow-id <workflow_id> --complete
```

### Verification rule
Every command above prints `[OK] State updated → ...` on success.
**You MUST confirm `[OK]` appears in the output before continuing.**
If the output shows `[ERROR]` instead, stop immediately and report it.

---

Run these steps in order and stop on any unresolved blocker:

## Step 1 — Product Owner

```bash
# INIT — create state file (run first, before any work)
python3 scripts/update_workflow_state.py \
  --init --workflow-id issue-<N>-<YYYYMMDDHHMMSS> --issue-number <N>
```
✅ Confirm `[OK]` before continuing.

```bash
# Mark Step 1 IN_PROGRESS
python3 scripts/update_workflow_state.py \
  --workflow-id <workflow_id> --step 1 --status IN_PROGRESS
```
✅ Confirm `[OK]` before continuing.

1. Read the issue title and body **literally** — do not assume, infer, or supplement from project conventions.
2. Derive a **Specific Change Required** statement answering: *"What exact named element must be added, removed, or changed, and to what value?"* — using only words present in the issue.
3. If too ambiguous to answer without assumptions:
   ```bash
   python3 scripts/update_workflow_state.py \
     --workflow-id <workflow_id> --step 1 --status BLOCKED \
     --error "Gate 0 BLOCKED: Issue body is too ambiguous — cannot derive a specific change without assumptions. Please clarify the issue."
   ```
   ✅ Confirm `[OK]`, then **STOP**.

4. Write the refined issue body:
   ```
   ## Summary
   <one-sentence description of the requirement>

   ## Specific Change Required
   <exact named element(s) to add/remove/change, using only words from the issue>

   ## Acceptance Criteria
   - [ ] <criterion 1>
   - [ ] <criterion 2>
   ```
5. Run: `gh issue edit <N> --body "<refined body>"` — mandatory.

```bash
# Mark Step 1 COMPLETED
python3 scripts/update_workflow_state.py \
  --workflow-id <workflow_id> --step 1 --status COMPLETED
```
✅ Confirm `[OK]` before continuing to Step 2.

The `## Specific Change Required` section is now the **sole authoritative spec** for the Developer step.

---

## Step 2 — Developer (Gate 1 required)

```bash
# Mark Step 2 IN_PROGRESS
python3 scripts/update_workflow_state.py \
  --workflow-id <workflow_id> --step 2 --status IN_PROGRESS
```
✅ Confirm `[OK]` before continuing.

1. Read ONLY the `## Specific Change Required` section from the refined issue.
2. Read `app.py` to understand the current implementation.
3. Implement **exactly and only** what the spec states — make the change in `app.py` NOW.
4. Run `git diff --name-only` to inspect changed files.
5. If `app.py` has NOT been modified (feature issue):
   ```bash
   python3 scripts/update_workflow_state.py \
     --workflow-id <workflow_id> --step 2 --status BLOCKED \
     --error "Gate 1 BLOCKED: No product file (app.py) was changed."
   ```
   ✅ Confirm `[OK]`, then **STOP**.

6. If only infra files changed (`scripts/`, `workflow_dashboard.py`, `playwright.config.ts`):
   ```bash
   python3 scripts/update_workflow_state.py \
     --workflow-id <workflow_id> --step 2 --status BLOCKED \
     --error "Gate 1 BLOCKED: Only infrastructure files were changed. At least one product file (app.py) must be modified."
   ```
   ✅ Confirm `[OK]`, then **STOP**.

7. Create branch and commit only meaningful source changes:
   ```bash
   git checkout -b feature/issue-<N>
   git add app.py tests/ ui-tests/
   git commit -m "[Issue #N] Implementation"
   ```

```bash
# Mark Step 2 COMPLETED
python3 scripts/update_workflow_state.py \
  --workflow-id <workflow_id> --step 2 --status COMPLETED
```
✅ Confirm `[OK]` before continuing to Step 3.

---

## Step 3 — Unit Tester (Gate 2 required)

```bash
# Mark Step 3 IN_PROGRESS
python3 scripts/update_workflow_state.py \
  --workflow-id <workflow_id> --step 3 --status IN_PROGRESS
```
✅ Confirm `[OK]` before continuing.

1. Read `tests/test_app.py` and identify existing test patterns.
2. Write new test(s) directly covering the new behavior. Test names must reference the feature keyword (e.g., `test_weekly_frequency_compounds_correctly`).
3. Check: `git diff origin/main -- tests/test_app.py` — if empty:
   ```bash
   python3 scripts/update_workflow_state.py \
     --workflow-id <workflow_id> --step 3 --status BLOCKED \
     --error "Gate 2 BLOCKED: No unit test was added or modified for this feature."
   ```
   ✅ Confirm `[OK]`, then **STOP**.

4. Run tests:
   ```bash
   bash scripts/run_tests_with_log.sh
   ```
   If any test fails:
   ```bash
   python3 scripts/update_workflow_state.py \
     --workflow-id <workflow_id> --step 3 --status BLOCKED \
     --error "Gate 2 BLOCKED: Unit tests failed. Fix failures before proceeding."
   ```
   ✅ Confirm `[OK]`, then **STOP**.

```bash
# Mark Step 3 COMPLETED
python3 scripts/update_workflow_state.py \
  --workflow-id <workflow_id> --step 3 --status COMPLETED
```
✅ Confirm `[OK]` before continuing to Step 4.

---

## Step 4 — UI Tester (Gate 3 required)

```bash
# Mark Step 4 IN_PROGRESS
python3 scripts/update_workflow_state.py \
  --workflow-id <workflow_id> --step 4 --status IN_PROGRESS
```
✅ Confirm `[OK]` before continuing.

1. Read relevant Playwright spec files in `ui-tests/regression/`.
2. Add or update a scenario that verifies the new UI element or behavior by its exact label name.
3. Check: `git diff origin/main -- ui-tests/` — if empty:
   ```bash
   python3 scripts/update_workflow_state.py \
     --workflow-id <workflow_id> --step 4 --status BLOCKED \
     --error "Gate 3 BLOCKED: No Playwright regression test was added or modified for this feature."
   ```
   ✅ Confirm `[OK]`, then **STOP**.

4. Run regression:
   ```bash
   bash scripts/run_ui_regression.sh
   ```
   If any Playwright test fails:
   ```bash
   python3 scripts/update_workflow_state.py \
     --workflow-id <workflow_id> --step 4 --status BLOCKED \
     --error "Gate 3 BLOCKED: UI regression tests failed. Fix failures before proceeding."
   ```
   ✅ Confirm `[OK]`, then **STOP**.

```bash
# Mark Step 4 COMPLETED
python3 scripts/update_workflow_state.py \
  --workflow-id <workflow_id> --step 4 --status COMPLETED
```
✅ Confirm `[OK]` before continuing to Step 5.

---

## Step 5 — Pull Request (Gate 4 required)

```bash
# Mark Step 5 IN_PROGRESS
python3 scripts/update_workflow_state.py \
  --workflow-id <workflow_id> --step 5 --status IN_PROGRESS
```
✅ Confirm `[OK]` before continuing.

1. Push branch: `git push -u origin feature/issue-<N>`
2. Read acceptance criteria from the refined issue body.
3. If no `- [ ]` checkboxes exist in the issue body:
   ```bash
   python3 scripts/update_workflow_state.py \
     --workflow-id <workflow_id> --step 5 --status BLOCKED \
     --error "Gate 4 BLOCKED: Issue has no acceptance criteria checkboxes."
   ```
   ✅ Confirm `[OK]`, then **STOP**.

4. Build PR body with full traceability:
   ```
   Closes #N

   ## Implementation
   - Changed: <file(s)> — <why>

   ## Unit Tests
   - Added/updated: <test function names>

   ## UI Regression Tests
   - Added/updated: <spec file and scenario names>

   ## Acceptance Criteria
   - [x] <criterion 1>
   - [x] <criterion 2>
   ```
5. Create the PR:
   ```bash
   gh pr create --base main --head feature/issue-<N> \
     --title "Issue #N: <feature description>" \
     --body "<pr body above>"
   ```

```bash
# Mark Step 5 COMPLETED
python3 scripts/update_workflow_state.py \
  --workflow-id <workflow_id> --step 5 --status COMPLETED

# Mark entire workflow COMPLETED
python3 scripts/update_workflow_state.py \
  --workflow-id <workflow_id> --complete
```
✅ Confirm both print `[OK]`. Workflow is now COMPLETED.

---

**On any blocker**: run the BLOCKED state command, confirm `[OK]`, then STOP. Do not proceed to the next step.