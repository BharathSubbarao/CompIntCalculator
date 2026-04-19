---
name: issue-workflow
description: "Run end-to-end Git issue workflow with PO, Developer, Unit Tester, UI Tester, and PR creation for CompIntCalculator."
tools: ["read_file", "grep_search", "get_errors", "run_in_terminal", "semantic_search"]
---

Run these steps in order and stop on any unresolved blocker:
1. Product Owner: refine issue into the required template.
2. Developer: understand current app, create branch, implement changes.
3. Unit Tester: update or add unit tests and run them.
4. UI Tester: update or add Playwright tests and run them.
5. Pull Request: only after all prior steps succeed.

On blocker, mark workflow blocked and escalate through the orchestrator.