from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi import FastAPI, HTTPException

from .github_api import IssueNotFoundError, get_issue
from .models import StartWorkflowRequest
from .state_store import create_workflow_state, load_state
from .workflow import run_workflow

app = FastAPI(title="Issue Workflow Orchestrator")


@app.post("/workflows/start")
def start_workflow(req: StartWorkflowRequest) -> dict:
    try:
        try:
            issue = get_issue(req.issue_number)
        except IssueNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

        issue_state = str(issue.get("state", "")).upper()
        if issue_state != "OPEN":
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Issue #{req.issue_number} is {issue_state or 'UNKNOWN'}. "
                    "Workflow can start only for OPEN issues."
                ),
            )

        workflow_id = f"issue-{req.issue_number}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"
        state = create_workflow_state(workflow_id, req.issue_number)
        final_state = run_workflow(state)
        return {
            "workflow_id": workflow_id,
            "issue_number": req.issue_number,
            "status": final_state.status,
            "current_step": final_state.current_step,
        }
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@app.get("/workflows/{workflow_id}")
def get_workflow(workflow_id: str) -> dict:
    try:
        state = load_state(workflow_id)
        return {
            "workflow_id": state.workflow_id,
            "issue_number": state.issue_number,
            "status": state.status,
            "current_step": state.current_step,
            "created_at": state.created_at.isoformat(),
            "updated_at": state.updated_at.isoformat(),
            "steps": [
                {
                    "step_id": step.step_id,
                    "name": step.name,
                    "status": step.status,
                    "started_at": step.started_at.isoformat() if step.started_at else None,
                    "ended_at": step.ended_at.isoformat() if step.ended_at else None,
                    "duration_seconds": step.duration_seconds,
                    "error": step.error,
                }
                for step in state.steps
            ],
        }
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found") from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "Issue Workflow Orchestrator"}