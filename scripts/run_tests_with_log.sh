#!/usr/bin/env bash

set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

LOG_FILE="${1:-test-results.log}"
shift $(( $# > 0 ? 1 : 0 ))

TIMESTAMP_FORMAT='+%Y-%m-%d %H:%M:%S %Z'

TMP_OUTPUT_FILE="$(mktemp)"
RUN_EXIT_CODE=0

{
  echo "===== TEST RUN START $(date "${TIMESTAMP_FORMAT}") ====="
  if [ "$#" -gt 0 ]; then
    python3 -m pytest "$@"
  else
    python3 -m pytest -vv -ra
  fi
  RUN_EXIT_CODE=$?
  echo "===== TEST RUN END   $(date "${TIMESTAMP_FORMAT}") (exit=${RUN_EXIT_CODE}) ====="
} >"${TMP_OUTPUT_FILE}" 2>&1

while IFS= read -r line; do
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$line"
done <"${TMP_OUTPUT_FILE}" | tee -a "${LOG_FILE}"

rm -f "${TMP_OUTPUT_FILE}"
exit "${RUN_EXIT_CODE}"
