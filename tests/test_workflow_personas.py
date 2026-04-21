from __future__ import annotations

from subprocess import CompletedProcess

import pytest

from ai_workflow import personas


def test_developer_step_runs_copilot_and_commits_feature_changes(monkeypatch) -> None:
    calls: list[list[str]] = []

    monkeypatch.setattr(
        personas,
        "get_issue",
        lambda issue_number: {
            "number": issue_number,
            "title": 'Add "Half Yearly" compounding frequency',
            "body": "- [ ] Add Half Yearly to the dropdown",
        },
    )

    def fake_run(args: list[str], **kwargs) -> CompletedProcess[str]:
        calls.append(args)

        if args[:2] == ["git", "checkout"] and len(args) == 3:
            return CompletedProcess(args, 0, "", "")
        if args[:2] == ["gh", "copilot"]:
            prompt = args[args.index("-p") + 1]
            assert "Issue title: Add \"Half Yearly\" compounding frequency" in prompt
            assert "Add or update unit tests in tests/test_app.py" in prompt
            assert "Do not push, open a PR, or create a git commit" in prompt
            assert "--allow-all" in args
            assert "--agent" not in args
            return CompletedProcess(args, 0, "changed app.py and tests", "")
        if args[:3] == ["git", "diff", "--cached"]:
            return CompletedProcess(
                args,
                0,
                "app.py\ntests/test_app.py\nui-tests/regression/positive/calculator.frequency.spec.ts\n",
                "",
            )
        if args[:2] == ["git", "commit"]:
            return CompletedProcess(args, 0, "[feature] commit", "")
        return CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(personas.subprocess, "run", fake_run)

    result = personas.developer_create_branch_and_plan(1)

    assert result["branch"] == "feature/issue-1"
    assert result["implementation_summary"] == "changed app.py and tests"
    assert any(call[:2] == ["gh", "copilot"] for call in calls)


def test_developer_step_blocks_when_no_product_file_changes(monkeypatch) -> None:
    monkeypatch.setattr(
        personas,
        "get_issue",
        lambda issue_number: {"number": issue_number, "title": "Issue", "body": "- [ ] Add feature"},
    )

    def fake_run(args: list[str], **kwargs) -> CompletedProcess[str]:
        if args[:2] == ["git", "checkout"] and len(args) == 3:
            return CompletedProcess(args, 0, "", "")
        if args[:2] == ["gh", "copilot"]:
            return CompletedProcess(args, 0, "updated tests only", "")
        if args[:3] == ["git", "diff", "--cached"]:
            return CompletedProcess(args, 0, "tests/test_app.py\n", "")
        return CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(personas.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError) as exc:
        personas.developer_create_branch_and_plan(1)

    assert "Gate 1 BLOCKED" in str(exc.value)


def test_build_pr_body_contains_traceability_sections(monkeypatch) -> None:
    monkeypatch.setattr(
        personas,
        "get_issue",
        lambda issue_number: {
            "number": issue_number,
            "title": "Feature issue",
            "body": "## Acceptance Criteria Checklist\n- [ ] Add Half Yearly\n- [ ] Keep existing behavior\n",
        },
    )

    def fake_run(args: list[str], **kwargs) -> CompletedProcess[str]:
        if args[:4] == ["git", "diff", "--name-only", "origin/main...HEAD"]:
            return CompletedProcess(
                args,
                0,
                "app.py\ntests/test_app.py\nui-tests/regression/positive/calculator.frequency.spec.ts\n",
                "",
            )
        if args[:4] == ["git", "diff", "origin/main...HEAD", "--"]:
            if args[4] == "tests/test_app.py":
                return CompletedProcess(args, 0, "+def test_half_yearly_future_value_matches_formula() -> None:\n", "")
            if args[4] == "ui-tests/":
                return CompletedProcess(args, 0, '+  test("half yearly selection updates summary metrics and table", async ({ page }) => {\n', "")
        raise AssertionError(f"Unexpected command: {args}")

    monkeypatch.setattr(personas.subprocess, "run", fake_run)

    body = personas._build_pr_body(1)

    assert "## Implementation" in body
    assert "## Unit Tests" in body
    assert "## UI Regression Tests" in body
    assert "## Acceptance Criteria" in body
    assert "- [x] Add Half Yearly" in body
    assert "test_half_yearly_future_value_matches_formula" in body
    assert "half yearly selection updates summary metrics and table" in body


def test_build_pr_body_blocks_without_acceptance_criteria(monkeypatch) -> None:
    monkeypatch.setattr(
        personas,
        "get_issue",
        lambda issue_number: {"number": issue_number, "title": "Feature issue", "body": "No checklist here"},
    )

    def fake_run(args: list[str], **kwargs) -> CompletedProcess[str]:
        if args[:4] == ["git", "diff", "--name-only", "origin/main...HEAD"]:
            return CompletedProcess(args, 0, "app.py\n", "")
        if args[:4] == ["git", "diff", "origin/main...HEAD", "--"]:
            return CompletedProcess(args, 0, "", "")
        raise AssertionError(f"Unexpected command: {args}")

    monkeypatch.setattr(personas.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError) as exc:
        personas._build_pr_body(1)

    assert "Gate 4 BLOCKED" in str(exc.value)


def test_product_owner_refine_issue_skips_already_templated_issue(monkeypatch) -> None:
    updated_bodies: list[str] = []

    monkeypatch.setattr(
        personas,
        "get_issue",
        lambda issue_number: {
            "number": issue_number,
            "title": "Feature issue",
            "body": (
                "## Problem Statement\nAlready templated\n\n"
                "## Acceptance Criteria Checklist\n- [ ] A criterion\n\n"
                "## Test Expectations\n- Keep tests passing\n"
            ),
        },
    )
    monkeypatch.setattr(personas, "update_issue_body", lambda issue_number, body: updated_bodies.append(body))

    result = personas.product_owner_refine_issue(1)

    assert result == {"issue_updated": False, "template_applied": False}
    assert updated_bodies == []