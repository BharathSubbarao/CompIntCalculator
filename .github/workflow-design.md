┌─────────────────────────────────────────────────────────────────┐
│                     USER (VS Code Chat)                         │
│           "Start work on git issue #N"                          │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│          workflow-trigger.instructions.md                       │
│          (applyTo: "**/")                                       │
│                                                                 │
│  1. Extract issue number N                                      │
│  2. POST http://localhost:8090/workflows/start                  │
│     { "issue_number": N }                                       │
│                                                                 │
│  ── If endpoint unreachable ──────────────────────────────────► │
│     Fall through to issue-workflow.agent.md directly            │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│        CONTEXT LOADED BY COPILOT (always active)                │
│                                                                 │
│  .github/copilot-instructions.md          ← project rules      │
│  .github/instructions/                                          │
│    developer-gate.instructions.md         ← gate enforcement   │
│    workflow-trigger.instructions.md       ← routing rules      │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              issue-workflow.agent.md                            │
│              (5-step sequential pipeline)                       │
└─────────────────────────┬───────────────────────────────────────┘
                          │
          ┌───────────────▼────────────────────┐
          │                                    │
          │  INIT: Create Workflow State File  │
          │  .workflow/state/                  │
          │  issue-<N>-<YYYYMMDDHHMMSS>.json   │
          │  All 5 steps → PENDING             │
          └───────────────┬────────────────────┘
                          │
                          ▼
╔═════════════════════════════════════════════════════════════════╗
║  STEP 1 — Product Owner                                        ║
║  Guided by: issue-workflow.agent.md §Step 1                    ║
║  Context:   copilot-instructions.md (gate rules)               ║
╠═════════════════════════════════════════════════════════════════╣
║                                                                 ║
║  1. Mark Step 1 → IN_PROGRESS (update JSON)                    ║
║  2. gh issue view N  (read title + body literally)             ║
║  3. AI derives "Specific Change Required"                      ║
║     using ONLY words present in the issue                      ║
║                                                                 ║
║     ┌──────────────────────────────────────┐                   ║
║     │  Too ambiguous to derive?            │                   ║
║     │  → Gate 0 BLOCK                      │                   ║
║     │  → Mark Step 1 BLOCKED               │──► STOP           ║
║     │  → Notify user                       │                   ║
║     └──────────────────────────────────────┘                   ║
║                                                                 ║
║  4. Apply issue template:                                       ║
║     ## Summary                                                  ║
║     ## Specific Change Required   ← authoritative spec         ║
║     ## Acceptance Criteria                                      ║
║       - [ ] criterion 1                                         ║
║       - [ ] criterion 2                                         ║
║                                                                 ║
║  5. gh issue edit N --body "<refined body>"                     ║
║  6. Mark Step 1 → COMPLETED (update JSON)                      ║
╚═════════════════════════════════════════════════════════════════╝
                          │
                          ▼
╔═════════════════════════════════════════════════════════════════╗
║  STEP 2 — Developer                                            ║
║  Guided by: issue-workflow.agent.md §Step 2                    ║
║  Enforced by: developer-gate.instructions.md (Gate 1)          ║
╠═════════════════════════════════════════════════════════════════╣
║                                                                 ║
║  1. Mark Step 2 → IN_PROGRESS                                   ║
║  2. Read ONLY "## Specific Change Required" from refined issue  ║
║  3. Read app.py to understand current implementation           ║
║  4. Implement EXACTLY what spec states (nothing more)          ║
║     in app.py (or relevant product file)                        ║
║                                                                 ║
║     ┌──────────────────────────────────────────────────┐       ║
║     │  Gate 1 checks (developer-gate.instructions.md)  │       ║
║     │  • No app.py changed?          → BLOCK           │       ║
║     │  • Only infra files changed?   → BLOCK           │──►STOP║
║     └──────────────────────────────────────────────────┘       ║
║                                                                 ║
║  5. git checkout -b feature/issue-N                            ║
║  6. git add / git commit (product files only)                  ║
║  7. Mark Step 2 → COMPLETED                                     ║
╚═════════════════════════════════════════════════════════════════╝
                          │
                          ▼
╔═════════════════════════════════════════════════════════════════╗
║  STEP 3 — Unit Tester                                          ║
║  Guided by: issue-workflow.agent.md §Step 3                    ║
║  Enforced by: developer-gate.instructions.md (Gate 2)          ║
╠═════════════════════════════════════════════════════════════════╣
║                                                                 ║
║  1. Mark Step 3 → IN_PROGRESS                                   ║
║  2. AI reads tests/test_app.py (existing patterns)             ║
║  3. AI writes new test(s) referencing the feature by name      ║
║     e.g. test_weekly_frequency_compounds_correctly             ║
║                                                                 ║
║     ┌──────────────────────────────────────────────────┐       ║
║     │  Gate 2 check                                     │       ║
║     │  • No new test covers the change? → BLOCK        │──►STOP║
║     └──────────────────────────────────────────────────┘       ║
║                                                                 ║
║  4. bash scripts/run_tests_with_log.sh                         ║
║                                                                 ║
║     ┌──────────────────────────────────────────────────┐       ║
║     │  Any test fails? → BLOCK                         │──►STOP║
║     └──────────────────────────────────────────────────┘       ║
║                                                                 ║
║  5. Mark Step 3 → COMPLETED                                     ║
╚═════════════════════════════════════════════════════════════════╝
                          │
                          ▼
╔═════════════════════════════════════════════════════════════════╗
║  STEP 4 — UI Tester                                            ║
║  Guided by: issue-workflow.agent.md §Step 4                    ║
║  Enforced by: developer-gate.instructions.md (Gate 3)          ║
╠═════════════════════════════════════════════════════════════════╣
║                                                                 ║
║  1. Mark Step 4 → IN_PROGRESS                                   ║
║  2. AI reads ui-tests/regression/*.spec.ts                     ║
║  3. AI writes/updates Playwright scenario referencing          ║
║     new UI element by exact label name                         ║
║                                                                 ║
║     ┌──────────────────────────────────────────────────┐       ║
║     │  Gate 3 check                                     │       ║
║     │  • No spec references new UI option? → BLOCK     │──►STOP║
║     └──────────────────────────────────────────────────┘       ║
║                                                                 ║
║  4. bash scripts/run_ui_regression.sh                          ║
║     (auto-selects free port 8502–8599)                         ║
║     (starts Streamlit app + runs Playwright)                   ║
║                                                                 ║
║     ┌──────────────────────────────────────────────────┐       ║
║     │  Any Playwright test fails? → BLOCK              │──►STOP║
║     └──────────────────────────────────────────────────┘       ║
║                                                                 ║
║  5. Mark Step 4 → COMPLETED                                     ║
╚═════════════════════════════════════════════════════════════════╝
                          │
                          ▼
╔═════════════════════════════════════════════════════════════════╗
║  STEP 5 — Pull Request Creator                                 ║
║  Guided by: issue-workflow.agent.md §Step 5                    ║
║  Enforced by: developer-gate.instructions.md (Gate 4)          ║
╠═════════════════════════════════════════════════════════════════╣
║                                                                 ║
║  1. Mark Step 5 → IN_PROGRESS                                   ║
║  2. git push -u origin feature/issue-N                         ║
║  3. Build PR body with traceability:                           ║
║     ## Implementation  → changed files + why                   ║
║     ## Unit Tests      → test function names added/updated     ║
║     ## UI Regression   → spec file + scenario names            ║
║     ## Acceptance Criteria                                      ║
║       - [x] criterion 1                                         ║
║       - [x] criterion 2                                         ║
║                                                                 ║
║     ┌──────────────────────────────────────────────────┐       ║
║     │  Gate 4 check                                     │       ║
║     │  • Any criterion unchecked?  → BLOCK             │──►STOP║
║     │  • No acceptance criteria?   → BLOCK             │       ║
║     └──────────────────────────────────────────────────┘       ║
║                                                                 ║
║  4. gh pr create --base main --head feature/issue-N            ║
║  5. Mark Step 5 → COMPLETED                                     ║
║  6. Set top-level workflow status → COMPLETED                   ║
╚═════════════════════════════════════════════════════════════════╝
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     WORKFLOW COMPLETE                           │
│                                                                 │
│   .workflow/state/issue-N-<ts>.json  → status: COMPLETED       │
│   GitHub PR open and linked to issue                           │
│   workflow_dashboard.py shows all 5 steps green                │
└─────────────────────────────────────────────────────────────────┘


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ON ANY BLOCK (any step)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Step N status → BLOCKED
  JSON error field ← block reason text
  Top-level status → BLOCKED
  AI reports block reason to user in chat
  Pipeline STOPS — no further steps run