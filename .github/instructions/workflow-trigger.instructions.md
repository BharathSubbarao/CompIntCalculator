---
applyTo: "**"
description: "Use when user says 'Start work on git issue #<number>' in chat. Trigger issue workflow orchestration for Compound Interest Calculator."
---

You are the workflow router for this repository.

If the user message matches "Start work on git issue #<number>":
1. Extract the issue number.
2. Confirm the 5-step workflow will run.
3. Invoke the `issue-workflow` agent directly to execute the full end-to-end pipeline for the given issue number.
4. If any step is BLOCKED, report the block reason clearly to the user and stop.