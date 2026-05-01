#!/usr/bin/env bash
# scripts/run_parallel_testing.sh
#
# Runs Step 3 (Unit Testing) and Step 4 (UI Regression Testing) in TRUE PARALLEL
# using OS-level background processes. Both steps start simultaneously and run
# independently. Step 5 (PR Creator) must not start until this script exits 0.
#
# Usage:
#   bash scripts/run_parallel_testing.sh <workflow_id>
#
# Exit codes:
#   0 — both Step 3 and Step 4 COMPLETED successfully
#   1 — one or both steps BLOCKED or failed
#
# State is written via update_workflow_state.py after each step transition.
# Output from each step is written to:
#   .workflow/logs/<workflow_id>-unit-tester.log
#   .workflow/logs/<workflow_id>-ui-tester.log

set -uo pipefail

WORKFLOW_ID="${1:?Usage: $0 <workflow_id>}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

LOG_DIR=".workflow/logs"
mkdir -p "${LOG_DIR}"

UNIT_LOG="${LOG_DIR}/${WORKFLOW_ID}-unit-tester.log"
UI_LOG="${LOG_DIR}/${WORKFLOW_ID}-ui-tester.log"

STATE_CMD="python3 scripts/update_workflow_state.py --workflow-id ${WORKFLOW_ID}"

echo "[PARALLEL] Starting Step 3 (Unit Testing) and Step 4 (UI Regression) simultaneously..."
echo "[PARALLEL] Logs: ${UNIT_LOG} | ${UI_LOG}"

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Unit Testing (runs in background)
# ─────────────────────────────────────────────────────────────────────────────
run_unit_testing() {
    local log="${UNIT_LOG}"
    echo "[Step 3] Starting Unit Testing at $(date '+%H:%M:%S')" | tee "${log}"

    ${STATE_CMD} --step 3 --status IN_PROGRESS >> "${log}" 2>&1
    if ! grep -q '\[OK\]' "${log}"; then
        echo "[Step 3] ERROR: Failed to mark IN_PROGRESS" | tee -a "${log}"
        exit 1
    fi

    # Gate 2 — test delta check
    TEST_DIFF=$(git diff origin/main -- tests/test_app.py 2>>"${log}")
    if [ -z "${TEST_DIFF}" ]; then
        local err="Gate 2 BLOCKED: No unit test was added or modified for this feature in tests/test_app.py."
        echo "[Step 3] ${err}" | tee -a "${log}"
        ${STATE_CMD} --step 3 --status BLOCKED --error "${err}" >> "${log}" 2>&1
        exit 1
    fi

    # Run the full test suite
    echo "[Step 3] Running pytest..." | tee -a "${log}"
    if ! bash scripts/run_tests_with_log.sh >> "${log}" 2>&1; then
        local err="Gate 2 BLOCKED: Unit tests failed. Fix all failures before proceeding."
        echo "[Step 3] ${err}" | tee -a "${log}"
        ${STATE_CMD} --step 3 --status BLOCKED --error "${err}" >> "${log}" 2>&1
        exit 1
    fi

    ${STATE_CMD} --step 3 --status COMPLETED >> "${log}" 2>&1
    echo "[Step 3] COMPLETED at $(date '+%H:%M:%S')" | tee -a "${log}"
}

# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — UI Regression Testing (runs in background)
# ─────────────────────────────────────────────────────────────────────────────
run_ui_testing() {
    local log="${UI_LOG}"
    echo "[Step 4] Starting UI Regression Testing at $(date '+%H:%M:%S')" | tee "${log}"

    ${STATE_CMD} --step 4 --status IN_PROGRESS >> "${log}" 2>&1
    if ! grep -q '\[OK\]' "${log}"; then
        echo "[Step 4] ERROR: Failed to mark IN_PROGRESS" | tee -a "${log}"
        exit 1
    fi

    # Gate 3 — Playwright spec delta check
    UI_DIFF=$(git diff origin/main -- ui-tests/ 2>>"${log}")
    if [ -z "${UI_DIFF}" ]; then
        local err="Gate 3 BLOCKED: No Playwright regression spec was added or modified for this feature in ui-tests/."
        echo "[Step 4] ${err}" | tee -a "${log}"
        ${STATE_CMD} --step 4 --status BLOCKED --error "${err}" >> "${log}" 2>&1
        exit 1
    fi

    # Run the full Playwright regression suite
    echo "[Step 4] Running Playwright regression..." | tee -a "${log}"
    if ! bash scripts/run_ui_regression.sh >> "${log}" 2>&1; then
        local err="Gate 3 BLOCKED: UI regression tests failed. Fix all failures before proceeding."
        echo "[Step 4] ${err}" | tee -a "${log}"
        ${STATE_CMD} --step 4 --status BLOCKED --error "${err}" >> "${log}" 2>&1
        exit 1
    fi

    ${STATE_CMD} --step 4 --status COMPLETED >> "${log}" 2>&1
    echo "[Step 4] COMPLETED at $(date '+%H:%M:%S')" | tee -a "${log}"
}

# ─────────────────────────────────────────────────────────────────────────────
# LAUNCH BOTH IN PARALLEL
# ─────────────────────────────────────────────────────────────────────────────
run_unit_testing &
UNIT_PID=$!

run_ui_testing &
UI_PID=$!

echo "[PARALLEL] Step 3 PID=${UNIT_PID} | Step 4 PID=${UI_PID}"
echo "[PARALLEL] Waiting for both to complete..."

# Wait for both and capture individual exit codes
wait "${UNIT_PID}"
UNIT_EXIT=$?

wait "${UI_PID}"
UI_EXIT=$?

# ─────────────────────────────────────────────────────────────────────────────
# EVALUATE RESULTS
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "[PARALLEL] Results:"
echo "  Step 3 (Unit Testing)      exit=${UNIT_EXIT}"
echo "  Step 4 (UI Regression)     exit=${UI_EXIT}"

if [ "${UNIT_EXIT}" -ne 0 ] || [ "${UI_EXIT}" -ne 0 ]; then
    echo "[PARALLEL] One or more parallel steps BLOCKED. Checking parallel gate..."
    python3 scripts/update_workflow_state.py \
        --workflow-id "${WORKFLOW_ID}" --check-parallel-complete || true
    echo "[PARALLEL] FAILED — Step 5 must not start. Review logs:"
    echo "  Unit Tester log : ${UNIT_LOG}"
    echo "  UI Tester log   : ${UI_LOG}"
    exit 1
fi

# Both passed — run parallel gate check as final confirmation
echo "[PARALLEL] Both steps completed. Running parallel gate check..."
python3 scripts/update_workflow_state.py \
    --workflow-id "${WORKFLOW_ID}" --check-parallel-complete

echo "[PARALLEL] SUCCESS — Step 3 and Step 4 both COMPLETED. Step 5 (PR Creator) may now start."
exit 0
