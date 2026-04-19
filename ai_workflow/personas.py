from __future__ import annotations

import subprocess
from typing import Any

from github_api import get_issue, update_issue_body, comment_issue


ISSUE_TEMPLATE = """## Problem Statement
{problem_statement}

## Acceptance Criteria Checklist
- [ ] Implement feature per problem statement
- [ ] All unit tests passing
- [ ] All UI tests passing

## UI Expectations
- Feature should integrate seamlessly with existing UI
- No breaking changes to current interface

## Edge Cases
- Handle all boundary conditions per test cases
- Validate all inputs per existing patterns

## Test Expectations
**Unit tests to add/modify:**
- Add/modify tests in tests/test_app.py for new functionality
- Ensure existing tests still pass

**E2E scenarios:**
- Add/modify Playwright tests in ui-tests/regression/
- Cover positive and negative scenarios
"""


def product_owner_refine_issue(issue_number: int) -> dict[str, Any]:
    """Step 1: Product Owner refines issue to standard template."""
    try:
        issue = get_issue(issue_number)
        body = issue.get("body") or ""
        title = issue.get("title", "Feature implementation")
        
        # Create refined template with original issue as problem statement
        refined_body = ISSUE_TEMPLATE.format(
            problem_statement=(body.strip() or title)
        )
        
        update_issue_body(issue_number, refined_body)
        print(f"[INFO] Issue #{issue_number} template refined")
        return {"issue_updated": True, "template_applied": True}
    except Exception as e:
        raise RuntimeError(f"Failed to refine issue template: {e}")


def developer_create_branch_and_plan(issue_number: int) -> dict[str, Any]:
    """Step 2: Developer creates feature branch."""
    try:
        branch = f"feature/issue-{issue_number}"
        
        # Try to checkout branch if it exists, otherwise create it
        result = subprocess.run(
            ["git", "checkout", branch],
            capture_output=True,
            text=True,
        )
        
        if result.returncode != 0:
            # Branch doesn't exist, create it
            subprocess.run(
                ["git", "checkout", "-b", branch],
                check=True,
                capture_output=True,
                text=True,
            )
            print(f"[INFO] Created new branch: {branch}")
        else:
            print(f"[INFO] Checked out existing branch: {branch}")
        
        # Stage any uncommitted changes and commit them
        # This ensures the branch has commits different from main
        subprocess.run(
            ["git", "add", "-A"],
            capture_output=True,
            text=True,
        )
        
        # Check if there are staged changes
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
        )
        
        if status_result.stdout.strip():
            # There are changes, commit them
            subprocess.run(
                ["git", "commit", "-m", f"[Issue #{issue_number}] Implementation for issue"],
                capture_output=True,
                text=True,
            )
            print(f"[INFO] Committed changes to branch: {branch}")
        else:
            print(f"[INFO] No changes to commit on branch: {branch}")
        
        return {"branch": branch, "planned": True}
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to create/checkout branch: {e.stderr}")


def unit_tester_run_and_fix(issue_number: int) -> dict[str, Any]:
    """Step 3: Unit Tester runs tests and reports results."""
    try:
        result = subprocess.run(
            ["bash", "scripts/run_tests_with_log.sh"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        
        if result.returncode != 0:
            error_msg = result.stdout + "\n" + result.stderr
            raise RuntimeError(f"Unit tests failed:\n{error_msg}")
        
        # Parse test output to count passing tests
        output = result.stdout + result.stderr
        print(f"[INFO] Unit tests completed successfully")
        return {
            "unit_tests_passed": True,
            "test_log": output[-1000:],  # Last 1000 chars of output
        }
    except subprocess.TimeoutExpired:
        raise RuntimeError("Unit test execution timed out (>5 minutes)")
    except Exception as e:
        raise RuntimeError(f"Unit test execution failed: {e}")


def ui_tester_run_and_publish(issue_number: int) -> dict[str, Any]:
    """Step 4: UI Tester runs Playwright tests and publishes results."""
    try:
        result = subprocess.run(
            ["bash", "scripts/run_ui_regression.sh"],
            capture_output=True,
            text=True,
            timeout=600,
        )
        
        if result.returncode != 0:
            error_msg = result.stdout + "\n" + result.stderr
            raise RuntimeError(f"UI regression tests failed:\n{error_msg}")
        
        # Post comment on issue with results
        comment_text = (
            "✅ **UI Regression Tests Passed**\n\n"
            "All Playwright tests executed successfully. "
            "See `playwright-results.json` and `playwright-report/` for details."
        )
        comment_issue(issue_number, comment_text)
        
        print(f"[INFO] UI tests completed and results published")
        return {
            "ui_tests_passed": True,
            "test_log": result.stdout[-1000:],  # Last 1000 chars
        }
    except subprocess.TimeoutExpired:
        raise RuntimeError("UI test execution timed out (>10 minutes)")
    except Exception as e:
        raise RuntimeError(f"UI test execution failed: {e}")


def pr_create(issue_number: int) -> dict[str, Any]:
    """Step 5: Create pull request (requires gh CLI)."""
    try:
        # Get current branch name
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        current_branch = result.stdout.strip()
        
        # Push branch to remote if not already pushed
        print(f"[INFO] Pushing branch {current_branch} to remote...")
        subprocess.run(
            ["git", "push", "-u", "origin", current_branch],
            capture_output=True,
            text=True,
            timeout=60,
        )
        # Note: We ignore errors here because the branch may already be pushed
        
        # Create PR using gh cli
        title = f"Issue #{issue_number}: Automated implementation"
        body = (
            f"Closes #{issue_number}\n\n"
            "This PR is created by the automated AI workflow. "
            "All unit and UI tests passing. Ready for human review."
        )
        
        result = subprocess.run(
            [
                "gh",
                "pr",
                "create",
                "--title",
                title,
                "--body",
                body,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        
        pr_url = result.stdout.strip()
        print(f"[INFO] PR created successfully: {pr_url}")
        return {
            "pr_created": True,
            "pr_url": pr_url,
        }
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to create PR: {e.stderr}")
    except Exception as e:
        raise RuntimeError(f"PR creation failed: {e}")
