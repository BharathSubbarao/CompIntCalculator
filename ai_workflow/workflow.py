from __future__ import annotations

from datetime import datetime
from typing import Any

from state_store import save_state
from teams_notify import send_teams_escalation
from personas import (
    product_owner_refine_issue,
    developer_create_branch_and_plan,
    unit_tester_run_and_fix,
    ui_tester_run_and_publish,
    pr_create,
)
from models import WorkflowState


def _mark_step_start(state: WorkflowState, idx: int) -> None:
    """Mark a step as started."""
    step = state.steps[idx]
    step.status = "IN_PROGRESS"
    step.started_at = datetime.utcnow()
    state.current_step = idx + 1
    state.status = "IN_PROGRESS"
    save_state(state)
    print(f"[STEP {idx + 1}] Started: {step.name}")


def _mark_step_done(state: WorkflowState, idx: int, output: dict[str, Any]) -> None:
    """Mark a step as completed."""
    step = state.steps[idx]
    step.status = "COMPLETED"
    step.ended_at = datetime.utcnow()
    step.duration_seconds = (
        (step.ended_at - step.started_at).total_seconds()
        if step.started_at
        else None
    )
    step.output = output
    save_state(state)
    print(
        f"[STEP {idx + 1}] Completed in {step.duration_seconds:.1f}s: {step.name}"
    )


def _mark_blocked(state: WorkflowState, idx: int, err: Exception) -> None:
    """Mark a step as blocked and send escalation."""
    step = state.steps[idx]
    step.status = "BLOCKED"
    step.ended_at = datetime.utcnow()
    step.duration_seconds = (
        (step.ended_at - step.started_at).total_seconds()
        if step.started_at
        else None
    )
    step.error = str(err)
    state.status = "BLOCKED"
    save_state(state)
    
    print(f"[STEP {idx + 1}] BLOCKED: {step.name}")
    print(f"[ERROR] {str(err)}")
    
    # Send Teams escalation
    send_teams_escalation(
        issue_number=state.issue_number,
        step_name=step.name,
        error_text=str(err),
        workflow_id=state.workflow_id,
    )


def run_workflow(state: WorkflowState) -> WorkflowState:
    """Execute the complete workflow sequentially."""
    
    actions: list[Any] = [
        product_owner_refine_issue,
        developer_create_branch_and_plan,
        unit_tester_run_and_fix,
        ui_tester_run_and_publish,
        pr_create,
    ]

    for idx, action in enumerate(actions):
        _mark_step_start(state, idx)
        try:
            output = action(state.issue_number)
            _mark_step_done(state, idx, output)
        except Exception as err:
            _mark_blocked(state, idx, err)
            return state

    # All steps completed successfully
    state.status = "COMPLETED"
    save_state(state)
    print("[WORKFLOW] ✅ All steps completed successfully!")
    return state
