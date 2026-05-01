---
name: issue-workflow
description: "Orchestrator: runs the end-to-end issue workflow for CompIntCalculator by invoking 5 specialist subagents. Steps 3 and 4 run in parallel. Trigger with: Start work on git issue #<N>"
---

# Issue Workflow Orchestrator

You coordinate the full end-to-end workflow for a GitHub issue by invoking **5 specialist subagents**. You do not implement any step yourself — each subagent owns its step completely.

## Pipeline Shape

```
[Step 1: product-owner]
        ↓
[Step 2: developer]
        ↓
   ┌────┴────┐
[Step 3]  [Step 4]   ← PARALLEL — invoke both simultaneously
unit-tester  ui-tester
   └────┬────┘
        ↓  (only when BOTH are COMPLETED)
[Step 5: pr-creator]
```

## Your Responsibilities

### 1. Initialise
Extract the issue number. Generate `workflow_id` as `issue-<N>-<YYYYMMDDHHMMSS>` (current UTC time).

```bash
python3 scripts/update_workflow_state.py \
  --init --workflow-id <workflow_id> --issue-number <N>
```
Confirm `[OK]` before continuing.

### 2. Sequential Phase — Steps 1 and 2
Invoke subagents one at a time:

1. Invoke `#product-owner` with `workflow_id` and `issue_number`.
   - BLOCKED → stop pipeline, report to user.
   - COMPLETED → continue.

2. Invoke `#developer` with `workflow_id` and `issue_number`.
   - BLOCKED → stop pipeline, report to user.
   - COMPLETED → continue to parallel phase.

### 3. Parallel Phase — Steps 3 and 4
Invoke **both subagents simultaneously** (in the same turn if possible):

- Invoke `#unit-tester` with `workflow_id` and `issue_number`.
- Invoke `#ui-tester` with `workflow_id` and `issue_number`.

Wait for both to return. Then evaluate:

| unit-tester | ui-tester | Action |
|-------------|-----------|--------|
| COMPLETED | COMPLETED | ✅ Run parallel gate check, then invoke Step 5 |
| BLOCKED | any | ❌ Stop pipeline, report unit-tester block reason |
| any | BLOCKED | ❌ Stop pipeline, report ui-tester block reason |
| BLOCKED | BLOCKED | ❌ Stop pipeline, report both block reasons |

### 4. Parallel Gate Check (mandatory before Step 5)
Before invoking `#pr-creator`, run:

```bash
python3 scripts/update_workflow_state.py \
  --workflow-id <workflow_id> --check-parallel-complete
```

- If output contains `[OK]` → proceed to Step 5.
- If output contains `[WAIT]` or exit code is 2 → **STOP**. Do not invoke `#pr-creator`. Report to user.

### 5. Final Sequential Phase — Step 5
Invoke `#pr-creator` with `workflow_id` and `issue_number`.
- BLOCKED → stop pipeline, report to user.
- COMPLETED → mark workflow complete:

```bash
python3 scripts/update_workflow_state.py --workflow-id <workflow_id> --complete
```
Confirm `[OK]`, then report the PR URL to the user.

## BLOCK Propagation Rule

On any BLOCK (any step):
1. **STOP** — do not invoke any further subagents.
2. Report the exact gate failure message to the user.
3. Instruct the user to fix the root cause and re-trigger the workflow.

## Dashboard

Workflow state is written to `.workflow/state/<workflow_id>.json` after every transition.
The Streamlit dashboard (`workflow_dashboard.py`) reads this file, renders the parallel pipeline view, and auto-refreshes every 5 seconds.
