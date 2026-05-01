---
name: issue-workflow
description: "Orchestrator: runs the end-to-end issue workflow for CompIntCalculator by invoking 5 specialist subagents. Steps 3 and 4 run in TRUE parallel via a shell script. Trigger with: Start work on git issue #<N>"
---

# Issue Workflow Orchestrator

You coordinate the full end-to-end workflow for a GitHub issue. You invoke specialist subagents for Steps 1, 2, and 5. **Steps 3 and 4 are executed in true OS-level parallelism via a dedicated shell script** — not via agent invocation — because a single agent context cannot run two subagents simultaneously.

## Pipeline Shape

```
[Step 1: #product-owner]          ← subagent
        ↓
[Step 2: #developer]              ← subagent
        ↓
bash scripts/run_parallel_testing.sh <workflow_id>
   ├── Step 3: Unit Testing       ← background process (PID A)
   └── Step 4: UI Regression      ← background process (PID B)
        ↓  (script exits 0 only when BOTH complete)
[Step 5: #pr-creator]             ← subagent
```

## Your Responsibilities

### 1. Initialise
Extract the issue number. Generate `workflow_id` as `issue-<N>-<YYYYMMDDHHMMSS>` (current UTC time).

```bash
python3 scripts/update_workflow_state.py \
  --init --workflow-id <workflow_id> --issue-number <N>
```
Confirm `[OK]` before continuing.

### 2. Step 1 — Product Owner
Invoke `#product-owner`, passing `workflow_id` and `issue_number`.
- **BLOCKED** → stop pipeline, report gate failure to user. STOP.
- **COMPLETED** → continue to Step 2.

### 3. Step 2 — Developer
Invoke `#developer`, passing `workflow_id` and `issue_number`.
- **BLOCKED** → stop pipeline, report gate failure to user. STOP.
- **COMPLETED** → continue to parallel phase.

### 4. Parallel Phase — Steps 3 + 4
Run the parallel testing script. This is a **single shell command** that launches both steps as background OS processes and waits for both to finish:

```bash
bash scripts/run_parallel_testing.sh <workflow_id>
```

This script:
- Marks Step 3 and Step 4 IN_PROGRESS simultaneously
- Runs `pytest` (Step 3) and `playwright` (Step 4) as true parallel background processes
- Enforces Gate 2 and Gate 3 independently per process
- Writes COMPLETED or BLOCKED state for each step
- Exits **0** only when both steps COMPLETED
- Exits **1** if either step BLOCKED (state file will show which one and why)

**After the script returns:**

| Exit code | Action |
|-----------|--------|
| `0` | ✅ Both passed — proceed to Step 5 |
| `1` | ❌ One or both BLOCKED — read `.workflow/logs/<workflow_id>-*.log` for details, report to user. STOP. |

### 5. Step 5 — PR Creator
Invoke `#pr-creator`, passing `workflow_id` and `issue_number`.
- **BLOCKED** → stop pipeline, report gate failure to user. STOP.
- **COMPLETED** → mark workflow complete:

```bash
python3 scripts/update_workflow_state.py --workflow-id <workflow_id> --complete
```
Confirm `[OK]`, then report the PR URL to the user.

## BLOCK Propagation Rule

On any BLOCK (any step):
1. **STOP** — do not invoke any further subagents or scripts.
2. Report the exact gate failure message to the user.
3. Instruct the user to fix the root cause and re-trigger the workflow.

## Dashboard

Workflow state is written to `.workflow/state/<workflow_id>.json` after every transition.
Step logs are written to `.workflow/logs/<workflow_id>-unit-tester.log` and `.workflow/logs/<workflow_id>-ui-tester.log`.
The Streamlit dashboard (`workflow_dashboard.py`) reads the state file, renders the parallel pipeline view, and auto-refreshes every 5 seconds.
