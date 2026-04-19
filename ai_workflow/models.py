from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Literal, Optional, Any
from datetime import datetime

StepStatus = Literal["PENDING", "IN_PROGRESS", "COMPLETED", "FAILED", "BLOCKED"]
WorkflowStatus = Literal["PENDING", "IN_PROGRESS", "COMPLETED", "BLOCKED", "FAILED"]


class StartWorkflowRequest(BaseModel):
    """Request to start a new workflow for an issue."""
    issue_number: int = Field(ge=1, description="GitHub issue number")


class StepRecord(BaseModel):
    """Individual step in a workflow."""
    step_id: int
    name: str
    persona: str
    status: StepStatus = "PENDING"
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    output: Optional[dict[str, Any]] = None
    error: Optional[str] = None


class WorkflowState(BaseModel):
    """Complete workflow state for an issue."""
    workflow_id: str
    issue_number: int
    status: WorkflowStatus = "PENDING"
    current_step: int = 0
    created_at: datetime
    updated_at: datetime
    steps: list[StepRecord]
