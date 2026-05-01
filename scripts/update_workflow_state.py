#!/usr/bin/env python3
"""
Workflow state updater for the AI issue workflow (Path B / VS Code agent).

Usage:
  # Create initial state file (all steps PENDING)
  python3 scripts/update_workflow_state.py --init --workflow-id issue-16-20260501102500 --issue-number 16

  # Mark a step IN_PROGRESS (call BEFORE doing the step's work)
  python3 scripts/update_workflow_state.py --workflow-id issue-16-20260501102500 --step 1 --status IN_PROGRESS

  # Mark a step COMPLETED (call AFTER step work succeeds)
  python3 scripts/update_workflow_state.py --workflow-id issue-16-20260501102500 --step 1 --status COMPLETED

  # Mark a step BLOCKED (call on any gate failure; pipeline must stop after this)
  python3 scripts/update_workflow_state.py --workflow-id issue-16-20260501102500 --step 2 --status BLOCKED --error "Gate 1 BLOCKED: no app.py change"

  # Mark entire workflow COMPLETED (call after Step 5 succeeds)
  python3 scripts/update_workflow_state.py --workflow-id issue-16-20260501102500 --complete

Exits with code 0 on success. Prints the updated status line for verification.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

STATE_DIR = Path(".workflow/state")

STEP_NAMES = {
    1: ("Product Owner Issue Refinement", "product_owner"),
    2: ("Developer Implementation", "developer"),
    3: ("Unit Testing", "unit_tester"),
    4: ("UI Regression Testing", "ui_tester"),
    5: ("Pull Request Creation", "pr_creator"),
}

VALID_STEP_STATUSES = {"PENDING", "IN_PROGRESS", "COMPLETED", "BLOCKED", "FAILED"}
VALID_WORKFLOW_STATUSES = {"PENDING", "IN_PROGRESS", "COMPLETED", "BLOCKED", "FAILED"}


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def state_path(workflow_id: str) -> Path:
    return STATE_DIR / f"{workflow_id}.json"


def load_state(workflow_id: str) -> dict:
    path = state_path(workflow_id)
    if not path.exists():
        print(f"[ERROR] State file not found: {path}", file=sys.stderr)
        sys.exit(1)
    return json.loads(path.read_text(encoding="utf-8"))


def save_and_verify(state: dict, workflow_id: str) -> None:
    path = state_path(workflow_id)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")

    # Read back and verify to catch filesystem issues
    written = json.loads(path.read_text(encoding="utf-8"))
    if written["status"] != state["status"]:
        print(
            f"[ERROR] State verification failed: wrote status={state['status']} "
            f"but read back status={written['status']}",
            file=sys.stderr,
        )
        sys.exit(1)
    print(
        f"[OK] State updated → workflow_id={workflow_id} "
        f"status={written['status']} current_step={written['current_step']} "
        f"updated_at={written['updated_at']}"
    )


def cmd_init(workflow_id: str, issue_number: int) -> None:
    path = state_path(workflow_id)
    if path.exists():
        print(f"[INFO] State file already exists: {path} — skipping init")
        state = load_state(workflow_id)
        print(f"[OK] Existing state → status={state['status']}")
        return

    ts = now_utc()
    state: dict = {
        "workflow_id": workflow_id,
        "issue_number": issue_number,
        "status": "PENDING",
        "current_step": 0,
        "created_at": ts,
        "updated_at": ts,
        "steps": [
            {
                "step_id": sid,
                "name": name,
                "persona": persona,
                "status": "PENDING",
                "started_at": None,
                "ended_at": None,
                "duration_seconds": None,
                "output": None,
                "error": None,
            }
            for sid, (name, persona) in STEP_NAMES.items()
        ],
    }
    save_and_verify(state, workflow_id)


def cmd_update_step(workflow_id: str, step_id: int, status: str, error: str | None) -> None:
    if status not in VALID_STEP_STATUSES:
        print(f"[ERROR] Invalid status '{status}'. Must be one of: {VALID_STEP_STATUSES}", file=sys.stderr)
        sys.exit(1)

    state = load_state(workflow_id)
    ts = now_utc()
    step = next((s for s in state["steps"] if s["step_id"] == step_id), None)
    if step is None:
        print(f"[ERROR] Step {step_id} not found in state file.", file=sys.stderr)
        sys.exit(1)

    step["status"] = status

    if status == "IN_PROGRESS":
        step["started_at"] = ts
        step["ended_at"] = None
        step["duration_seconds"] = None
        step["error"] = None
        state["current_step"] = step_id
        state["status"] = "IN_PROGRESS"

    elif status == "COMPLETED":
        step["ended_at"] = ts
        if step.get("started_at"):
            started = datetime.fromisoformat(step["started_at"])
            ended = datetime.fromisoformat(ts)
            step["duration_seconds"] = round((ended - started).total_seconds(), 1)

    elif status == "BLOCKED":
        step["ended_at"] = ts
        if step.get("started_at"):
            started = datetime.fromisoformat(step["started_at"])
            ended = datetime.fromisoformat(ts)
            step["duration_seconds"] = round((ended - started).total_seconds(), 1)
        step["error"] = error or "Blocked — no error message provided"
        state["status"] = "BLOCKED"

    state["updated_at"] = ts
    save_and_verify(state, workflow_id)


def cmd_complete(workflow_id: str) -> None:
    state = load_state(workflow_id)
    state["status"] = "COMPLETED"
    state["updated_at"] = now_utc()
    save_and_verify(state, workflow_id)


def main() -> None:
    parser = argparse.ArgumentParser(description="Update AI workflow state file.")
    parser.add_argument("--workflow-id", required=True, help="Workflow ID (e.g. issue-16-20260501102500)")
    parser.add_argument("--init", action="store_true", help="Create initial state file with all steps PENDING")
    parser.add_argument("--issue-number", type=int, help="Issue number (required with --init)")
    parser.add_argument("--step", type=int, choices=[1, 2, 3, 4, 5], help="Step number to update")
    parser.add_argument("--status", choices=list(VALID_STEP_STATUSES), help="New status for the step")
    parser.add_argument("--error", help="Error message (required when --status BLOCKED)")
    parser.add_argument("--complete", action="store_true", help="Mark top-level workflow as COMPLETED")
    args = parser.parse_args()

    if args.init:
        if not args.issue_number:
            parser.error("--issue-number is required with --init")
        cmd_init(args.workflow_id, args.issue_number)

    elif args.complete:
        cmd_complete(args.workflow_id)

    elif args.step and args.status:
        if args.status == "BLOCKED" and not args.error:
            parser.error("--error is required when --status is BLOCKED")
        cmd_update_step(args.workflow_id, args.step, args.status, args.error)

    else:
        parser.error("Provide --init, --complete, or both --step and --status")


if __name__ == "__main__":
    main()
