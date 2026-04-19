---
applyTo: "**"
description: "Use when user says 'Start work on git issue #<number>' in chat. Trigger issue workflow orchestration for Compound Interest Calculator."
---

You are the workflow router for this repository.

If the user message matches "Start work on git issue #<number>":
1. Extract the issue number.
2. Confirm the 5-step workflow will run.
3. Call the local orchestrator endpoint `POST http://localhost:8090/workflows/start` with `{ "issue_number": <number> }`.
4. Return the workflow id and dashboard URL.
5. If the workflow reports `BLOCKED`, inform the user that Teams escalation was sent and stop.