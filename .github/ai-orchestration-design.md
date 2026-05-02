# AI Workflow Design — Multi-Agent Architecture

## Overview

The CompIntCalculator project uses a **VS Code Copilot Chat multi-agent pipeline** to automate the full lifecycle of a GitHub issue — from refinement through code, tests, and PR creation — with no manual steps required.

Trigger phrase: `Start work on git issue #<N>`

---

## Architecture

```
User Chat
    │
    ▼
┌─────────────────────────┐
│  orchestrator.agent     │  ← Orchestrator (coordinates only, implements nothing)
└────────────┬────────────┘
             │
     ┌───────▼────────┐
     │  product-owner │  Step 1 — Refine issue, define acceptance criteria (Gate 0)
     └───────┬────────┘
             │
     ┌───────▼────────┐
     │   developer    │  Step 2 — Implement feature in app.py (Gate 1)
     └───────┬────────┘
             │
     ┌───────▼────────┐
     │  unit-tester   │  Step 3 — Write & commit pytest tests ONLY (Gate 2 delta check)
     └───────┬────────┘
             │
     ┌───────▼────────┐
     │   ui-tester    │  Step 4 — Write & commit Playwright specs ONLY (Gate 3 delta check)
     └───────┬────────┘
             │
     ┌───────┴────────────────────────────────┐
     │  run_parallel_testing.sh               │  Execute both suites simultaneously
     │  ├── pytest        & → PID A (Step 3)  │
     │  └── playwright    & → PID B (Step 4)  │
     └───────┬────────────────────────────────┘
             │  (both must be COMPLETED)
     ┌───────▼────────┐
     │   pr-creator   │  Step 5 — Push branch, create traceable PR (Gate 4)
     └────────────────┘
```

---

## Agents

| File | Role | Gate |
|------|------|------|
| `orchestrator.agent.md` | **Orchestrator** — manages pipeline, state, BLOCK propagation | — |
| `product-owner.agent.md` | Refines raw issue into structured template with acceptance criteria | Gate 0 |
| `developer.agent.md` | Implements feature change in `app.py` | Gate 1 |
| `unit-tester.agent.md` | **Writes & commits** pytest unit tests in `tests/test_app.py` (does NOT run them) | Gate 2 |
| `ui-tester.agent.md` | **Writes & commits** Playwright regression specs in `ui-tests/regression/` (does NOT run them) | Gate 3 |
| `pr-creator.agent.md` | Pushes branch and creates PR with full traceability checklist | Gate 4 |

---

## Parallelism

VS Code Copilot Chat is single-threaded — it cannot run two subagents simultaneously. The solution is a **write/execute split**:

### Write phase (sequential subagents)
Steps 3 and 4 run as sequential subagent calls. Each agent **only writes and commits** tests/specs — no execution. This is inherently sequential because LLM work cannot be parallelized within a single agent context.

```
#unit-tester  →  writes & commits tests/test_app.py
#ui-tester    →  writes & commits ui-tests/regression/*.spec.ts
```

### Execution phase (true OS-level parallel)
Once both write phases are committed, the orchestrator runs a single shell command that launches both test suites as background OS processes simultaneously:

```
bash scripts/run_parallel_testing.sh <workflow_id>
    ├── pytest      &   → PID A  →  .workflow/logs/<wid>-unit-tester.log
    └── playwright  &   → PID B  →  .workflow/logs/<wid>-ui-tester.log
                wait
    exit 0 = both COMPLETED
    exit 1 = at least one BLOCKED
```

Step 5 only starts after this script exits 0.

> ⚠️ **The orchestrator must never call #unit-tester or #ui-tester to run tests.** Doing so forces ui-tester to wait for unit-tester to finish, defeating the parallelism.

---

## State Machine

State is persisted to `.workflow/state/<workflow_id>.json` after every transition.

```
PENDING → IN_PROGRESS → COMPLETED
                      ↘ BLOCKED  (stops the pipeline)
```

Managed by `scripts/update_orchestration_state.py`:

| Command | Purpose |
|---------|---------|
| `--init` | Create state file for a new workflow |
| `--step N --status S` | Transition a step to IN_PROGRESS / COMPLETED / BLOCKED |
| `--check-parallel-complete` | Gate check: exits 0 only when Steps 3+4 are both COMPLETED |
| `--complete` | Mark the whole workflow done |

---

## Quality Gates

Every gate is enforced inside the owning subagent. A failure raises a BLOCKED status; the orchestrator stops the pipeline immediately.

| Gate | Owner | Check |
|------|-------|-------|
| Gate 0 | product-owner | Issue has structured template + acceptance criteria |
| Gate 1 | developer | `app.py` was changed (infra-only changes are rejected) |
| Gate 2 | unit-tester (write) + parallel script (run) | New/modified test in `tests/test_app.py` referencing the feature; all tests pass |
| Gate 3 | ui-tester (write) + parallel script (run) | New/modified Playwright spec in `ui-tests/regression/`; all specs pass |
| Gate 4 | pr-creator | PR body maps every acceptance criterion to code change + test evidence |

---

## Dashboard

`scripts/ai_orchestration_dashboard.py` (Streamlit) reads state JSON files and renders the live pipeline.

- **Left panel** — pipeline visualization with parallel lane (Steps 3+4 side-by-side)
- **Right panel** — step detail inspector, blocked error messages, collapsible log viewers
- **Status icons** — ⬜ PENDING · 🟡 IN_PROGRESS · ✅ COMPLETED · 🔴 BLOCKED
- **Auto-refresh** — JavaScript `setTimeout`, default every 5 seconds

Run: `python3 -m streamlit run scripts/ai_orchestration_dashboard.py`
