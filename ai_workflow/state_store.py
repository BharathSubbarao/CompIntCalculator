from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime

from models import WorkflowState, StepRecord


STATE_DIR = Path(".workflow/state")


def default_steps() -> list[StepRecord]:
    """Create default step records for a new workflow."""
    return [
        StepRecord(step_id=1, name="Product Owner Issue Refinement", persona="product_owner"),
        StepRecord(step_id=2, name="Developer Implementation", persona="developer"),
        StepRecord(step_id=3, name="Unit Testing", persona="unit_tester"),
        StepRecord(step_id=4, name="UI Regression Testing", persona="ui_tester"),
        StepRecord(step_id=5, name="Pull Request Creation", persona="pr_creator"),
    ]


def create_workflow_state(workflow_id: str, issue_number: int) -> WorkflowState:
    """Create and save a new workflow state."""
    now = datetime.utcnow()
    state = WorkflowState(
        workflow_id=workflow_id,
        issue_number=issue_number,
        status="PENDING",
        current_step=0,
        created_at=now,
        updated_at=now,
        steps=default_steps(),
    )
    save_state(state)
    return state


def state_path(workflow_id: str) -> Path:
    """Get the file path for a workflow state."""
    return STATE_DIR / f"{workflow_id}.json"


def save_state(state: WorkflowState) -> None:
    """Save workflow state to disk."""
    state.updated_at = datetime.utcnow()
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_path(state.workflow_id).write_text(
        state.model_dump_json(indent=2),
        encoding="utf-8"
    )


def load_state(workflow_id: str) -> WorkflowState:
    """Load workflow state from disk."""
    raw = state_path(workflow_id).read_text(encoding="utf-8")
    return WorkflowState.model_validate_json(raw)
