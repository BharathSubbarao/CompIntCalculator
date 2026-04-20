#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if [ ! -d node_modules ]; then
  echo "Installing Playwright dependencies..."
  npm install
fi

# Pick an available app port for Playwright unless explicitly overridden.
is_port_free() {
  local port="$1"
  ! lsof -iTCP:"${port}" -sTCP:LISTEN -t >/dev/null 2>&1
}

if [ -z "${PLAYWRIGHT_APP_PORT:-}" ]; then
  for candidate_port in $(seq 8502 8599); do
    if is_port_free "${candidate_port}"; then
      export PLAYWRIGHT_APP_PORT="${candidate_port}"
      break
    fi
  done

  if [ -z "${PLAYWRIGHT_APP_PORT:-}" ]; then
    echo "Could not find a free port in range 8502-8599 for Playwright app server."
    exit 1
  fi
else
  export PLAYWRIGHT_APP_PORT
fi

echo "Using PLAYWRIGHT_APP_PORT=${PLAYWRIGHT_APP_PORT}"

echo "Running Playwright UI regression suite..."
npx playwright test "$@"

echo "UI regression completed. Open the web report with:"
echo "npx playwright show-report"