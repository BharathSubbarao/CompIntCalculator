from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ai_workflow.github_api import IssueNotFoundError
from ai_workflow.main import start_workflow
from ai_workflow.models import StartWorkflowRequest


class _State:
    def __init__(self, status: str, current_step: int) -> None:
        self.status = status
        self.current_step = current_step


def test_start_workflow_allows_open_issue(monkeypatch) -> None:
    monkeypatch.setattr("ai_workflow.main.get_issue", lambda issue_number: {"number": issue_number, "state": "OPEN"})
    monkeypatch.setattr("ai_workflow.main.create_workflow_state", lambda workflow_id, issue_number: object())
    monkeypatch.setattr("ai_workflow.main.run_workflow", lambda state: _State(status="COMPLETED", current_step=5))

    payload = start_workflow(StartWorkflowRequest(issue_number=2))
    assert payload["issue_number"] == 2
    assert payload["status"] == "COMPLETED"
    assert payload["current_step"] == 5


def test_start_workflow_blocks_closed_issue(monkeypatch) -> None:
    monkeypatch.setattr("ai_workflow.main.get_issue", lambda issue_number: {"number": issue_number, "state": "CLOSED"})

    with pytest.raises(HTTPException) as exc:
        start_workflow(StartWorkflowRequest(issue_number=2))

    assert exc.value.status_code == 409
    assert "only for OPEN issues" in str(exc.value.detail)


def test_start_workflow_returns_404_when_issue_missing(monkeypatch) -> None:
    def _raise_not_found(issue_number: int) -> dict:
        raise IssueNotFoundError(f"Issue #{issue_number} not found")

    monkeypatch.setattr("ai_workflow.main.get_issue", _raise_not_found)

    with pytest.raises(HTTPException) as exc:
        start_workflow(StartWorkflowRequest(issue_number=999999))

    assert exc.value.status_code == 404
    assert str(exc.value.detail) == "Issue #999999 not found"
