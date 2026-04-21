from __future__ import annotations

import re
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


def _build_implementation_prompt(issue_number: int, issue_title: str, issue_body: str) -> str:
    return (
        f"Implement GitHub issue #{issue_number} in this repository.\n\n"
        f"Issue title: {issue_title}\n\n"
        f"Issue body:\n{issue_body}\n\n"
        "Requirements:\n"
        "- Make the required product change in app.py or the relevant product file.\n"
        "- Add or update unit tests in tests/test_app.py for the new behavior.\n"
        "- Add or update Playwright regression coverage in ui-tests/regression/ for the visible behavior.\n"
        "- Follow the repository instructions and workflow gate requirements.\n"
        "- Do not change workflow or infrastructure files unless the issue explicitly requires it.\n"
        "- Do not push, open a PR, or create a git commit; the orchestrator handles that.\n"
        "- End with a short summary of the files changed and the tests added or updated."
    )


def _issue_is_already_refined(issue_body: str) -> bool:
    normalized = issue_body.lower()
    return (
        "## problem statement" in normalized
        and "## acceptance criteria checklist" in normalized
        and "## test expectations" in normalized
    )


def _extract_checklist_items(issue_body: str) -> list[str]:
    items: list[str] = []
    for raw_line in issue_body.splitlines():
        line = raw_line.strip()
        if line.startswith("- [ ]") or line.startswith("- [x]") or line.startswith("- [X]"):
            item = line[5:].strip()
            if item and item not in items:
                items.append(item)
    return items


def _extract_added_python_tests(diff_text: str) -> list[str]:
    return re.findall(r"(?m)^\+def (test_[^(]+)", diff_text)


def _extract_added_playwright_tests(diff_text: str) -> list[str]:
    return re.findall(r'(?m)^\+\s*test\("([^"]+)"', diff_text)


def _build_pr_body(issue_number: int) -> str:
    issue = get_issue(issue_number)
    issue_body = str(issue.get("body") or "")

    changed_files_result = subprocess.run(
        ["git", "diff", "--name-only", "origin/main...HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    changed_files = [line for line in changed_files_result.stdout.splitlines() if line]

    unit_diff = subprocess.run(
        ["git", "diff", "origin/main...HEAD", "--", "tests/test_app.py"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    ui_diff = subprocess.run(
        ["git", "diff", "origin/main...HEAD", "--", "ui-tests/"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout

    unit_tests = _extract_added_python_tests(unit_diff)
    ui_tests = _extract_added_playwright_tests(ui_diff)
    acceptance_criteria = _extract_checklist_items(issue_body)

    if not acceptance_criteria:
        raise RuntimeError(
            f"Gate 4 BLOCKED: Issue #{issue_number} does not contain acceptance criteria checkboxes."
        )

    implementation_files = ", ".join(changed_files) if changed_files else "No changed files detected"
    unit_summary = ", ".join(unit_tests) if unit_tests else "Updated tests/test_app.py"
    ui_summary = ", ".join(ui_tests) if ui_tests else "Updated ui-tests/regression/ coverage"
    checked_criteria = "\n".join(f"- [x] {item}" for item in acceptance_criteria)

    return (
        f"Closes #{issue_number}\n\n"
        "## Implementation\n"
        f"- Changed: {implementation_files} — implemented the requested issue behavior.\n\n"
        "## Unit Tests\n"
        f"- Added/updated: {unit_summary}\n\n"
        "## UI Regression Tests  \n"
        f"- Added/updated: {ui_summary}\n\n"
        "## Acceptance Criteria\n"
        f"{checked_criteria}\n"
    )


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
        if _issue_is_already_refined(body):
            print(f"[INFO] Issue #{issue_number} already uses workflow template")
            return {"issue_updated": False, "template_applied": False}
        refined_body = ISSUE_TEMPLATE.format(problem_statement=(body.strip() or title))
        update_issue_body(issue_number, refined_body)
        print(f"[INFO] Issue #{issue_number} template refined")
        return {"issue_updated": True, "template_applied": True}
    except Exception as error:
        raise RuntimeError(f"Failed to refine issue template: {error}") from error


def developer_create_branch_and_plan(issue_number: int) -> dict[str, Any]:
    try:
        issue = get_issue(issue_number)
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

        implementation_prompt = _build_implementation_prompt(
            issue_number,
            str(issue.get("title") or f"Issue #{issue_number}"),
            str(issue.get("body") or ""),
        )
        implementation_result = subprocess.run(
            [
                "gh",
                "copilot",
                "-p",
                implementation_prompt,
                "--agent",
                "issue-workflow",
                "--allow-all-tools",
                "--no-ask-user",
                "--reasoning-effort",
                "high",
                "--silent",
            ],
            capture_output=True,
            text=True,
            timeout=1200,
            check=True,
        )
        print(f"[INFO] Copilot workflow implementation completed for issue #{issue_number}")

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

        return {
            "branch": branch,
            "planned": True,
            "implementation_summary": implementation_result.stdout.strip(),
        }
    except subprocess.CalledProcessError as error:
        command = " ".join(error.cmd) if isinstance(error.cmd, list) else str(error.cmd)
        raise RuntimeError(
            f"Workflow implementation command failed: {command}\n{error.stderr or error.stdout}"
        ) from error


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
        body = _build_pr_body(issue_number)
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