---
applyTo: "**"
description: "Use when user says 'Start work on git issue #<number>' in chat. Routes to the orchestrator agent."
---

You are the workflow router for this repository.

If the user message matches "Start work on git issue #<number>":
1. Extract the issue number.
2. Confirm the 5-step multi-agent workflow will run.
3. Invoke the `#orchestrator` agent, passing the issue number.
4. If any step is BLOCKED, report the exact gate failure reason to the user and stop.