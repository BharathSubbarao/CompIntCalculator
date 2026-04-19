---
applyTo: "**"
description: "Use when user says 'Start work on git issue #<number>' in chat. Trigger issue workflow orchestration for Compound Interest Calculator."
---

# Issue Workflow Trigger

You are the workflow router for this repository.

## Trigger Condition
If the user message matches this pattern: **"Start work on git issue #<number>"**

## Your Actions (in order)
1. **Extract** the issue number from user message.
2. **Confirm** with the user by stating: "Starting workflow for issue #X. This will: (1) refine issue template, (2) create feature branch, (3) run unit tests, (4) run UI tests, (5) create PR."
3. **Call the local orchestrator service**:
   ```
   POST http://localhost:8090/workflows/start
   Body: {"issue_number": <extracted_number>}
   ```
4. **Return the workflow ID** and dashboard URL to user.
5. **Poll** the orchestrator endpoint `GET http://localhost:8090/workflows/{workflow_id}` every 10 seconds until status is not "IN_PROGRESS".
6. **Report final status**:
   - If **COMPLETED**: "✅ Workflow completed successfully. PR is open."
   - If **BLOCKED**: "🚨 Workflow blocked at step X. Team has been notified via Teams. Please check Microsoft Teams for escalation details."
   - If **FAILED**: "❌ Workflow failed. Check logs."

## Critical Rules
- **Never skip steps.** Execute all 5 steps unless blocked.
- **Never ignore escalations.** If orchestrator reports BLOCKED, Teams has already been notified - inform the user immediately.
- **Assume orchestrator is running** on port 8090. If connection fails, tell user: "Orchestrator service not running. Start with: uvicorn ai_workflow.main:app --reload --port 8090"
