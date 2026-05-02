#!/usr/bin/env bash
# run_parallel_testing.sh — Steps 3 (unit) + 4 (UI) in true OS-level parallelism.
#
# Usage:  bash scripts/run_parallel_testing.sh <workflow_id>
#
# Exit codes:
#   0  — both Step 3 and Step 4 COMPLETED
#   1  — one or both steps BLOCKED (check state file + log files for details)

set -uo pipefail

WORKFLOW_ID="${1:?Usage: $0 <workflow_id>}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

LOG_DIR=".workflow/logs"
mkdir -p "${LOG_DIR}"

UNIT_LOG="${LOG_DIR}/${WORKFLOW_ID}-unit-tester.log"
UI_LOG="${LOG_DIR}/${WORKFLOW_ID}-ui-tester.log"

STATE_SCRIPT="python3 scripts/update_orchestration_state.py"

ts() { date '+%Y-%m-%d %H:%M:%S'; }

# ---------------------------------------------------------------------------
# Mark both parallel execution runs IN_PROGRESS simultaneously
# ---------------------------------------------------------------------------
echo "[$(ts)] Marking unit_test_run IN_PROGRESS..."
${STATE_SCRIPT} --workflow-id "${WORKFLOW_ID}" --parallel-step unit_test_run --status IN_PROGRESS
echo "[$(ts)] Marking ui_test_run IN_PROGRESS..."
${STATE_SCRIPT} --workflow-id "${WORKFLOW_ID}" --parallel-step ui_test_run --status IN_PROGRESS

# ---------------------------------------------------------------------------
# Step 3 — Unit Testing (background process)
# ---------------------------------------------------------------------------
run_unit_tests() {
  local wf_id="${1}"
  local log_file="${2}"

  {
    echo "===== STEP 3 UNIT TESTING START $(ts) ====="

    # Gate 2: verify tests were added / modified for this feature
    UNIT_DIFF="$(git diff origin/main -- tests/test_app.py 2>&1)"
    if [ -z "${UNIT_DIFF}" ]; then
      MSG="Gate 2 BLOCKED: No unit test was added or modified for this feature in tests/test_app.py."
      echo "[GATE 2 FAIL] ${MSG}"
      python3 scripts/update_orchestration_state.py \
        --workflow-id "${wf_id}" --parallel-step unit_test_run --status BLOCKED \
        --error "${MSG}"
      echo "===== STEP 3 BLOCKED $(ts) ====="
      exit 1
    fi
    echo "[GATE 2 OK] Unit test diff found."

    # Run the full pytest suite (exclude infra tests that require optional ai_workflow module)
    echo "[$(ts)] Running pytest..."
    bash scripts/run_tests_with_log.sh "${log_file}.pytest.log" tests/test_app.py
    PYTEST_EXIT=$?

    if [ "${PYTEST_EXIT}" -ne 0 ]; then
      MSG="Gate 2 BLOCKED: Unit tests failed (exit ${PYTEST_EXIT}). Fix all failures before proceeding."
      echo "[GATE 2 FAIL] ${MSG}"
      python3 scripts/update_orchestration_state.py \
        --workflow-id "${wf_id}" --parallel-step unit_test_run --status BLOCKED \
        --error "${MSG}"
      echo "===== STEP 3 BLOCKED $(ts) ====="
      exit 1
    fi

    echo "[GATE 2 OK] All unit tests passed."
    python3 scripts/update_orchestration_state.py \
      --workflow-id "${wf_id}" --parallel-step unit_test_run --status COMPLETED
    echo "===== STEP 3 COMPLETED $(ts) ====="
    exit 0
  } 2>&1 | tee -a "${log_file}"
}

# ---------------------------------------------------------------------------
# Step 4 — UI Regression Testing (background process)
# ---------------------------------------------------------------------------
run_ui_tests() {
  local wf_id="${1}"
  local log_file="${2}"

  {
    echo "===== STEP 4 UI REGRESSION START $(ts) ====="

    # Gate 3: verify Playwright specs were added / modified for this feature
    UI_DIFF="$(git diff origin/main -- ui-tests/ 2>&1)"
    if [ -z "${UI_DIFF}" ]; then
      MSG="Gate 3 BLOCKED: No Playwright regression spec was added or modified for this feature in ui-tests/."
      echo "[GATE 3 FAIL] ${MSG}"
      python3 scripts/update_orchestration_state.py \
        --workflow-id "${wf_id}" --parallel-step ui_test_run --status BLOCKED \
        --error "${MSG}"
      echo "===== STEP 4 BLOCKED $(ts) ====="
      exit 1
    fi
    echo "[GATE 3 OK] Playwright spec diff found."

    # Run the full Playwright regression suite
    echo "[$(ts)] Running Playwright regression suite..."
    bash scripts/run_ui_regression.sh
    PLAYWRIGHT_EXIT=$?

    if [ "${PLAYWRIGHT_EXIT}" -ne 0 ]; then
      MSG="Gate 3 BLOCKED: UI regression tests failed (exit ${PLAYWRIGHT_EXIT}). Fix all failures before proceeding."
      echo "[GATE 3 FAIL] ${MSG}"
      python3 scripts/update_orchestration_state.py \
        --workflow-id "${wf_id}" --parallel-step ui_test_run --status BLOCKED \
        --error "${MSG}"
      echo "===== STEP 4 BLOCKED $(ts) ====="
      exit 1
    fi

    echo "[GATE 3 OK] All UI regression tests passed."
    python3 scripts/update_orchestration_state.py \
      --workflow-id "${wf_id}" --parallel-step ui_test_run --status COMPLETED
    echo "===== STEP 4 COMPLETED $(ts) ====="
    exit 0
  } 2>&1 | tee -a "${log_file}"
}

# ---------------------------------------------------------------------------
# Launch both steps as TRUE parallel background processes
# ---------------------------------------------------------------------------
echo "[$(ts)] Launching Step 3 (unit tests) and Step 4 (UI regression) in parallel..."

run_unit_tests "${WORKFLOW_ID}" "${UNIT_LOG}" &
UNIT_PID=$!

run_ui_tests "${WORKFLOW_ID}" "${UI_LOG}" &
UI_PID=$!

echo "[$(ts)] Step 3 PID=${UNIT_PID}  |  Step 4 PID=${UI_PID}"

# ---------------------------------------------------------------------------
# Wait for both background processes and capture exit codes
# ---------------------------------------------------------------------------
wait "${UNIT_PID}"
UNIT_EXIT=$?

wait "${UI_PID}"
UI_EXIT=$?

echo ""
echo "===== PARALLEL PHASE SUMMARY ====="
echo "Step 3 (Unit Testing)      exit=${UNIT_EXIT}"
echo "Step 4 (UI Regression)     exit=${UI_EXIT}"
echo "=================================="

# ---------------------------------------------------------------------------
# Evaluate and exit
# ---------------------------------------------------------------------------
if [ "${UNIT_EXIT}" -eq 0 ] && [ "${UI_EXIT}" -eq 0 ]; then
  echo "[$(ts)] ✅ Both Step 3 and Step 4 COMPLETED. Proceeding to Step 5."
  exit 0
else
  echo "[$(ts)] ❌ One or both steps BLOCKED. Check logs:"
  echo "  Unit log : ${UNIT_LOG}"
  echo "  UI log   : ${UI_LOG}"
  exit 1
fi
