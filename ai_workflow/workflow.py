from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .models import WorkflowState
from .personas import (
    developer_create_branch_and_plan,
    pr_create,
    product_owner_refine_issue,
    ui_tester_run_and_publish,
    unit_tester_run_and_fix,
)
from .state_store import save_state
from .teams_notify import send_teams_escalation


def _mark_step_start(state: WorkflowState, idx: int) -> None:
    step = state.steps[idx]
    step.status = "IN_PROGRESS"
    step.started_at = datetime.now(timezone.utc)
    state.current_step = idx + 1
    state.status = "IN_PROGRESS"
    save_state(state)


def _mark_step_done(state: WorkflowState, idx: int, output: dict[str, Any]) -> None:
    step = state.steps[idx]
    step.status = "COMPLETED"
    step.ended_at = datetime.now(timezone.utc)
    step.duration_seconds = (step.ended_at - step.started_at).total_seconds() if step.started_at else None
    step.output = output
    save_state(state)


def _mark_blocked(state: WorkflowState, idx: int, error: Exception) -> None:
    step = state.steps[idx]
    step.status = "BLOCKED"
    step.ended_at = datetime.now(timezone.utc)
    step.duration_seconds = (step.ended_at - step.started_at).total_seconds() if step.started_at else None
    step.error = str(error)
    state.status = "BLOCKED"
    save_state(state)
    send_teams_escalation(state.issue_number, step.name, str(error), state.workflow_id)


def run_workflow(state: WorkflowState) -> WorkflowState:
    actions = [
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
        except Exception as error:
            _mark_blocked(state, idx, error)
            return state

    state.status = "COMPLETED"
    save_state(state)
    return state