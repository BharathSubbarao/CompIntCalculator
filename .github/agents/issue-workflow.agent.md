---
name: issue-workflow
description: "Run end-to-end Git issue workflow with PO, Developer, Unit Tester, UI Tester, and PR creation for CompIntCalculator."
tools: ["read_file", "grep_search", "get_errors", "run_in_terminal", "semantic_search"]
---

# Issue Workflow Agent

This agent orchestrates a multi-persona workflow for Git issues in the CompIntCalculator project.

## Workflow Steps (Strict Sequential Order)

### Step 1: Product Owner Issue Refinement
- **Objective**: Standardize issue documentation
- **Actions**:
  1. Fetch the issue from GitHub using the issue number
  2. Parse current issue body
  3. Rewrite issue body to conform to this template:
     ```
     ## Problem Statement
     [Clear description of the problem]
     
     ## Acceptance Criteria Checklist
     - [ ] Criterion 1
     - [ ] Criterion 2
     - [ ] Criterion 3
     
     ## UI Expectations
     - [Expected UI behavior or visual change]
     - [User interaction expectations]
     
     ## Edge Cases
     - Edge case 1
     - Edge case 2
     
     ## Test Expectations
     **Unit tests to add/modify:**
     - [List specific unit test scenarios]
     
     **E2E scenarios:**
     - [Playwright test scenarios]
     ```
  4. Update issue body with refined template
  5. Post comment: "✅ Issue template refinement complete."
- **Exit Condition**: If this step fails, escalate immediately and STOP.

### Step 2: Developer Implementation & Planning
- **Objective**: Plan and implement feature
- **Actions**:
  1. Read the refined issue
  2. Read [app.py](../../../../app.py) to understand current application structure and functions
  3. Read [tests/test_app.py](../../../../tests/test_app.py) to understand test patterns
  4. Create a plan document in your response outlining:
     - What files will be modified
     - What new functions/changes needed
     - How changes align with acceptance criteria
  5. Create feature branch: `git checkout -b feature/issue-<issue_number>-<short-topic>`
  6. Implement code changes against the acceptance criteria
  7. Commit changes with message: `[Issue #<number>] <description>`
- **Exit Condition**: If unable to parse issue or understand scope, escalate and STOP.

### Step 3: Unit Testing
- **Objective**: Ensure code quality and no regression
- **Actions**:
  1. Review existing tests in [tests/test_app.py](../../../../tests/test_app.py)
  2. Add or modify unit tests for the scope of this issue
  3. Run tests: `bash ./scripts/run_tests_with_log.sh`
  4. **If any test fails**: Fix the implementation and re-run until all pass
  5. Report total tests passed/failed
- **Exit Condition**: If tests do not pass after attempted fixes, escalate with error logs and STOP.

### Step 4: UI Regression Testing
- **Objective**: Ensure no UI regression
- **Actions**:
  1. Review existing Playwright tests in [ui-tests/regression/](../../../../ui-tests/regression/)
  2. Add or modify UI tests for the scope (both positive and negative scenarios)
  3. Run UI tests: `bash ./scripts/run_ui_regression.sh`
  4. **If any test fails**: Fix the implementation and re-run until all pass
  5. Publish results summary
  6. Comment on issue with link to Playwright report
- **Exit Condition**: If UI tests do not pass after attempted fixes, escalate with error logs and STOP.

### Step 5: Pull Request Creation
- **Objective**: Open PR for human review
- **Actions** (only after all previous steps succeed):
  1. Use GitHub CLI to create PR:
     ```bash
     gh pr create --title "Issue #<number>: <short-description>" \
                  --body "Automated workflow PR for review. All unit and UI tests passing."
     ```
  2. Post comment on original issue: "🚀 PR created and ready for human review."
- **Exit Condition**: If PR creation fails, escalate and STOP.

## Escalation Rule
**If ANY step fails and cannot be auto-fixed:**
1. Mark workflow as BLOCKED
2. Post escalation to Teams (orchestrator handles this)
3. Report blocked step and error to user
4. **HALT** - do not proceed to next step

## Key Files to Reference
- [app.py](../../../../app.py) - Main application logic
- [requirements.txt](../../../../requirements.txt) - Dependencies  
- [tests/test_app.py](../../../../tests/test_app.py) - Unit test patterns
- [scripts/run_tests_with_log.sh](../../../../scripts/run_tests_with_log.sh) - Test runner
- [scripts/run_ui_regression.sh](../../../../scripts/run_ui_regression.sh) - UI test runner
- [playwright.config.ts](../../../../playwright.config.ts) - Playwright config
- [.github/copilot-instructions.md](../copilot-instructions.md) - Project standards (type hints, money_ prefix, etc)

## Standards to Maintain
- All functions must have type hints
- Currency-related variables must start with `money_` prefix
- Follow PEP 8 style guidelines
- No global variables; encapsulate in functions
- Validate inputs are non-negative
