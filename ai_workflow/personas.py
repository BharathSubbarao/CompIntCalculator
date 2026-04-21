from __future__ import annotations

import subprocess
from typing import Any

from .github_api import comment_issue, get_issue, update_issue_body

# Infrastructure-only paths — changes to these alone do NOT satisfy Gate 1
_INFRA_PREFIXES = (
    "ai_workflow/",
    "scripts/",
    "workflow_dashboard.py",
    "playwright.config.ts",
    "playwright-results.json",
    "playwright-report/",
    "test-results/",
    ".github/",
)

# Product source files required for feature issues
_PRODUCT_FILES = ("app.py",)


def _is_infra_only(changed_files: list[str]) -> bool:
    """Return True if every changed file is infrastructure-only."""
    if not changed_files:
        return True
    return all(
        any(f.startswith(prefix) or f == prefix.rstrip("/") for prefix in _INFRA_PREFIXES)
        for f in changed_files
    )


def _has_product_change(changed_files: list[str]) -> bool:
    """Return True if at least one product source file was changed."""
    return any(f in _PRODUCT_FILES for f in changed_files)


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
    try:
        issue = get_issue(issue_number)
        body = issue.get("body") or ""
        title = issue.get("title", "Feature implementation")
        refined_body = ISSUE_TEMPLATE.format(problem_statement=(body.strip() or title))
        update_issue_body(issue_number, refined_body)
        print(f"[INFO] Issue #{issue_number} template refined")
        return {"issue_updated": True, "template_applied": True}
    except Exception as error:
        raise RuntimeError(f"Failed to refine issue template: {error}") from error


def developer_create_branch_and_plan(issue_number: int) -> dict[str, Any]:
    try:
        branch = f"feature/issue-{issue_number}"
        result = subprocess.run(["git", "checkout", branch], capture_output=True, text=True)

        if result.returncode != 0:
            subprocess.run(
                ["git", "checkout", "-b", branch],
                check=True,
                capture_output=True,
                text=True,
            )
            print(f"[INFO] Created new branch: {branch}")
        else:
            print(f"[INFO] Checked out existing branch: {branch}")

        subprocess.run(["git", "add", "-A"], capture_output=True, text=True)
        subprocess.run(
            [
                "git",
                "reset",
                "HEAD",
                "--",
                ".workflow",
                "playwright-report",
                "playwright-results.json",
                "test-results.log",
                ".env",
                ".env.local",
                "enhancements",
                "enhacements",
            ],
            capture_output=True,
            text=True,
        )

        staged_changes = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True,
        )

        staged_files = [f for f in staged_changes.stdout.strip().splitlines() if f]

        # Gate 1 — Functional Coverage
        if not staged_files:
            raise RuntimeError(
                f"Gate 1 BLOCKED: No staged changes found for issue #{issue_number}. "
                "The developer must implement the feature in app.py before committing."
            )
        if _is_infra_only(staged_files) or not _has_product_change(staged_files):
            raise RuntimeError(
                f"Gate 1 BLOCKED: Only infrastructure files were changed for issue #{issue_number}. "
                f"Changed: {staged_files}. "
                "At least one product file (app.py) must be modified to satisfy a feature issue."
            )

        subprocess.run(
            ["git", "commit", "-m", f"[Issue #{issue_number}] Implementation for issue"],
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"[INFO] Committed changes to branch: {branch}")

        return {"branch": branch, "planned": True}
    except subprocess.CalledProcessError as error:
        raise RuntimeError(f"Failed to create/checkout branch: {error.stderr}") from error


def unit_tester_run_and_fix(issue_number: int) -> dict[str, Any]:
    try:
        result = subprocess.run(
            ["bash", "scripts/run_tests_with_log.sh"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            error_text = result.stdout + "\n" + result.stderr
            raise RuntimeError(f"Unit tests failed:\n{error_text}")

        output = result.stdout + result.stderr

        # Gate 2 — Unit Test Delta
        test_diff = subprocess.run(
            ["git", "diff", "origin/main", "--", "tests/test_app.py"],
            capture_output=True,
            text=True,
        )
        if not test_diff.stdout.strip():
            raise RuntimeError(
                f"Gate 2 BLOCKED: No unit test changes found for issue #{issue_number}. "
                "Add or update tests in tests/test_app.py that cover the new feature."
            )

        print("[INFO] Unit tests completed successfully")
        return {"unit_tests_passed": True, "test_log": output[-1000:]}
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("Unit test execution timed out (>5 minutes)") from error
    except Exception as error:
        raise RuntimeError(f"Unit test execution failed: {error}") from error


def ui_tester_run_and_publish(issue_number: int) -> dict[str, Any]:
    try:
        result = subprocess.run(
            ["bash", "scripts/run_ui_regression.sh"],
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode != 0:
            error_text = result.stdout + "\n" + result.stderr
            raise RuntimeError(f"UI regression tests failed:\n{error_text}")

        # Gate 3 — UI Regression Test Delta
        ui_diff = subprocess.run(
            ["git", "diff", "origin/main", "--", "ui-tests/"],
            capture_output=True,
            text=True,
        )
        if not ui_diff.stdout.strip():
            raise RuntimeError(
                f"Gate 3 BLOCKED: No Playwright regression test changes found for issue #{issue_number}. "
                "Add or update a .spec.ts file in ui-tests/regression/ that covers the new UI feature."
            )

        comment_issue(
            issue_number,
            "✅ **UI Regression Tests Passed**\n\nAll Playwright tests executed successfully. See `playwright-results.json` and `playwright-report/` for details.",
        )
        print("[INFO] UI tests completed and results published")
        return {"ui_tests_passed": True, "test_log": result.stdout[-1000:]}
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("UI test execution timed out (>10 minutes)") from error
    except Exception as error:
        raise RuntimeError(f"UI test execution failed: {error}") from error


def pr_create(issue_number: int) -> dict[str, Any]:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        current_branch = result.stdout.strip()
        print(f"[INFO] Pushing branch {current_branch} to remote...")
        subprocess.run(
            ["git", "push", "-u", "origin", current_branch],
            capture_output=True,
            text=True,
            timeout=60,
        )

        # If PR already exists for this branch, return it instead of failing.
        existing_pr = subprocess.run(
            [
                "gh",
                "pr",
                "list",
                "--state",
                "open",
                "--head",
                current_branch,
                "--json",
                "url",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        if "https://" in existing_pr.stdout:
            pr_url = existing_pr.stdout.split('"url":"', 1)[1].split('"', 1)[0]
            print(f"[INFO] PR already exists: {pr_url}")
            return {"pr_created": True, "pr_url": pr_url, "existing": True}

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
                "--base",
                "main",
                "--head",
                current_branch,
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
        return {"pr_created": True, "pr_url": pr_url}
    except subprocess.CalledProcessError as error:
        raise RuntimeError(f"Failed to create PR: {error.stderr}") from error
    except Exception as error:
        raise RuntimeError(f"PR creation failed: {error}") from error