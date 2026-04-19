from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

StepStatus = Literal["PENDING", "IN_PROGRESS", "COMPLETED", "FAILED", "BLOCKED"]
WorkflowStatus = Literal["PENDING", "IN_PROGRESS", "COMPLETED", "BLOCKED", "FAILED"]


class StartWorkflowRequest(BaseModel):
    issue_number: int = Field(ge=1, description="GitHub issue number")


class StepRecord(BaseModel):
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
    workflow_id: str
    issue_number: int
    status: WorkflowStatus = "PENDING"
    current_step: int = 0
    created_at: datetime
    updated_at: datetime
    steps: list[StepRecord]