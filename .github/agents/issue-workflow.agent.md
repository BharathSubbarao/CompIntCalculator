---
name: issue-workflow
description: "Run end-to-end Git issue workflow with PO, Developer, Unit Tester, UI Tester, and PR creation for CompIntCalculator."
---

## Workflow State Tracking (MANDATORY)

Before starting any step, create a workflow state file so the dashboard can display live progress.

**State file location**: `.workflow/state/<workflow_id>.json`
**Workflow ID format**: `issue-<N>-<YYYYMMDDHHMMSS>`

### State file schema
```json
{
  "workflow_id": "issue-16-20260429102500",
  "issue_number": 16,
  "status": "IN_PROGRESS",
  "current_step": 1,
  "created_at": "2026-04-29T10:25:00",
  "updated_at": "2026-04-29T10:25:00",
  "steps": [
    { "step_id": 1, "name": "Product Owner Issue Refinement", "persona": "product_owner", "status": "PENDING", "started_at": null, "ended_at": null, "duration_seconds": null, "output": null, "error": null },
    { "step_id": 2, "name": "Developer Implementation",        "persona": "developer",      "status": "PENDING", "started_at": null, "ended_at": null, "duration_seconds": null, "output": null, "error": null },
    { "step_id": 3, "name": "Unit Testing",                   "persona": "unit_tester",    "status": "PENDING", "started_at": null, "ended_at": null, "duration_seconds": null, "output": null, "error": null },
    { "step_id": 4, "name": "UI Regression Testing",          "persona": "ui_tester",      "status": "PENDING", "started_at": null, "ended_at": null, "duration_seconds": null, "output": null, "error": null },
    { "step_id": 5, "name": "Pull Request Creation",          "persona": "pr_creator",     "status": "PENDING", "started_at": null, "ended_at": null, "duration_seconds": null, "output": null, "error": null }
  ]
}
```

### State update rules
At each step boundary, update the JSON file using `python3 -c` or a bash heredoc:
- **Before a step starts**: set that step's `status` to `"IN_PROGRESS"`, set `started_at` to current UTC time, set top-level `current_step` to that step's `step_id`, set top-level `status` to `"IN_PROGRESS"`.
- **After a step succeeds**: set that step's `status` to `"COMPLETED"`, set `ended_at` to current UTC time, compute `duration_seconds`.
- **If a step is BLOCKED**: set that step's `status` to `"BLOCKED"`, set `ended_at`, set `error` to the block reason, set top-level `status` to `"BLOCKED"`.
- **After all steps succeed**: set top-level `status` to `"COMPLETED"`.
- Always update the top-level `updated_at` on every write.

Use this Python snippet pattern to update the state file (replace values as needed):
```bash
python3 - <<'EOF'
import json, re
from datetime import datetime
from pathlib import Path

STATE_FILE = Path(".workflow/state/<workflow_id>.json")
state = json.loads(STATE_FILE.read_text())
now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")

# Example: mark step 1 as IN_PROGRESS
step = next(s for s in state["steps"] if s["step_id"] == 1)
step["status"] = "IN_PROGRESS"
step["started_at"] = now
state["current_step"] = 1
state["status"] = "IN_PROGRESS"
state["updated_at"] = now
STATE_FILE.write_text(json.dumps(state, indent=2))
EOF
```

---

Run these steps in order and stop on any unresolved blocker:

## Step 1 — Product Owner
1. **Create the initial state file** now (before doing any work):
   - Generate `workflow_id` as `issue-<N>-<YYYYMMDDHHMMSS>` using the current UTC time.
   - Create `.workflow/state/` directory if it doesn't exist.
   - Write the full state JSON with all 5 steps as `"PENDING"`, top-level `status` = `"PENDING"`, `current_step` = `0`.
2. **Mark Step 1 IN_PROGRESS** in the state file.
3. Refine the issue into the required template following these rules strictly:
   - Read the issue title and body **literally**. Do not assume, infer, or supplement the requirement from project conventions, canonical tables, or codebase knowledge.
   - Derive a **Specific Change Required** statement by answering: *"What exact named element (dropdown option, field, formula, label) must be added, removed, or changed, and to what value?"* — using only words present in the issue title/body.
   - If the issue body is too ambiguous to answer without making assumptions, **BLOCK** with: `"Gate 0 BLOCKED: Issue body is too ambiguous — cannot derive a specific change without assumptions. Please clarify the issue."` Mark Step 1 as `"BLOCKED"` in the state file. Do NOT proceed.
4. Write the refined issue body using the following template:
   ```
   ## Summary
   <one-sentence description of the requirement>

   ## Specific Change Required
   <exact named element(s) to add/remove/change, using only words from the issue title/body>

   ## Acceptance Criteria
   - [ ] <criterion 1>
   - [ ] <criterion 2>
   ```
5. **Update the GitHub issue** by running `gh issue edit <N> --body "<refined body>"`. This is mandatory.
6. **Mark Step 1 COMPLETED** in the state file (set `ended_at`, `duration_seconds`).
7. The `## Specific Change Required` section becomes the **sole authoritative specification** for the Developer step.

## Step 2 — Developer (Gate 1 required)
1. **Mark Step 2 IN_PROGRESS** in the state file.
2. Read the `## Specific Change Required` section from the refined issue. This is the **only** specification you may implement.
3. Read `app.py` to understand the current implementation.
4. Implement **exactly and only** what is stated in `## Specific Change Required`.
5. Make the code change in `app.py` (or the relevant file) NOW — before branch creation or commits.
6. **BLOCK** (mark Step 2 `"BLOCKED"` in state file) if the issue is a product feature but `app.py` has not been modified.
7. **BLOCK** if the only changed files are infra/workflow: `ai_workflow/`, `scripts/`, `workflow_dashboard.py`, `playwright.config.ts`.
8. After making the change, create branch and commit only the meaningful source changes.
9. **Mark Step 2 COMPLETED** in the state file.

## Step 3 — Unit Tester (Gate 2 required)
1. **Mark Step 3 IN_PROGRESS** in the state file.
2. Open `tests/test_app.py` and identify the existing test patterns.
3. Add new test(s) or update existing ones to directly cover the new behavior.
4. Test function names must reference the feature (e.g., `test_weekly_frequency_compounds_correctly`).
5. **BLOCK** (mark Step 3 `"BLOCKED"` in state file) if no test in `tests/test_app.py` covers the implemented change.
6. Run `bash scripts/run_tests_with_log.sh` and assert all pass.
7. **Mark Step 3 COMPLETED** in the state file.

## Step 4 — UI Tester (Gate 3 required)
1. **Mark Step 4 IN_PROGRESS** in the state file.
2. Open the relevant Playwright spec files in `ui-tests/regression/`.
3. Add or update a scenario that verifies the new UI element or behavior is visible and functional.
4. **BLOCK** (mark Step 4 `"BLOCKED"` in state file) if no Playwright test references the new UI option by name.
5. Run `bash scripts/run_ui_regression.sh` and assert all pass.
6. **Mark Step 4 COMPLETED** in the state file.

## Step 5 — Pull Request (Gate 4 required)
1. **Mark Step 5 IN_PROGRESS** in the state file.
2. PR title: `Issue #N: <feature description>`.
3. PR body must contain a traceability checklist:
   - `app.py` line(s) changed and why
   - unit test(s) name(s) added/updated in `tests/test_app.py`
   - Playwright test(s) name(s) added/updated in `ui-tests/regression/`
4. **BLOCK** (mark Step 5 `"BLOCKED"` in state file) if any acceptance criterion from the issue is not covered.
5. Create the PR.
6. **Mark Step 5 COMPLETED** in the state file and set top-level `status` to `"COMPLETED"`.

On blocker, mark workflow blocked and stop.