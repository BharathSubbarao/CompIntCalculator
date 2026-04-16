#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if [ ! -d node_modules ]; then
  echo "Installing Playwright dependencies..."
  npm install
fi

echo "Running Playwright UI regression suite..."
npx playwright test

echo "UI regression completed. Open the web report with:"
echo "npx playwright show-report"