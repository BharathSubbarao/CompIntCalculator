from __future__ import annotations

import os
import sys
from datetime import datetime
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import StartWorkflowRequest
from state_store import create_workflow_state, load_state
from workflow import run_workflow


app = FastAPI(
    title="Issue Workflow Orchestrator",
    description="Orchestrates multi-persona workflow for CompIntCalculator issues",
)


@app.post("/workflows/start")
def start_workflow(req: StartWorkflowRequest) -> dict:
    """
    Trigger workflow for a GitHub issue.
    
    Returns workflow_id and initial status.
    """
    try:
        # Generate unique workflow ID
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        uuid_part = uuid4().hex[:8]
        workflow_id = f"issue-{req.issue_number}-{timestamp}-{uuid_part}"

        print(f"\n{'='*60}")
        print(f"[WORKFLOW {workflow_id}] Starting for issue #{req.issue_number}")
        print(f"{'='*60}\n")

        # Create workflow state
        state = create_workflow_state(workflow_id, req.issue_number)

        # Execute workflow
        final_state = run_workflow(state)

        print(f"\n{'='*60}")
        print(f"[WORKFLOW {workflow_id}] Status: {final_state.status}")
        print(f"{'='*60}\n")

        return {
            "workflow_id": workflow_id,
            "issue_number": req.issue_number,
            "status": final_state.status,
            "current_step": final_state.current_step,
        }

    except Exception as e:
        print(f"[ERROR] Workflow initialization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workflows/{workflow_id}")
def get_workflow(workflow_id: str) -> dict:
    """Get current status of a workflow."""
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
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "service": "Issue Workflow Orchestrator"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8090)
