# Playwright UI Test Setup Guide

## Current Status
✅ **Completed:**
- playwright.config.ts created with browser detection
- 36 UI test specs created (12 positive scenarios, 24 negative scenarios)
- Browser filtering configured (Firefox & WebKit skipped by default)
- JSON & HTML reporters configured

⚠️ **Blocked:**
- Node.js not installed on system
- npm/npx not available in shell environment

## Prerequisites
You need **Node.js 18+** and **npm** to run Playwright tests.

### Installation Options

#### Option 1: Using Homebrew (macOS)
```bash
brew install node
```

#### Option 2: Using nvm (Node Version Manager) - Recommended
This is better if you manage multiple Node versions:
```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.zshrc  # or ~/.bashrc depending on your shell
nvm install 20
nvm use 20
```

#### Option 3: Download from nodejs.org
Visit https://nodejs.org and download the LTS version for macOS.

### Verify Installation
```bash
node --version
npm --version
```

## Running Playwright Tests

### Browser Detection
The playwright.config.ts includes smart browser detection:
- **Default:** Runs only on Chromium (Firefox & WebKit skipped)
- **Skip specific browsers:** `SKIP_BROWSERS="firefox" npm test`
- **Run all:** `SKIP_BROWSERS="" npm test`

### Run All Tests
```bash
cd /Users/bsubbarao/MYDATA/CompIntCalculator
./node_modules/.bin/playwright test
```

### Run Specific Test Suite
```bash
./node_modules/.bin/playwright test ui-tests/regression/positive/
```

### Run Tests in Headed Mode (See Browser)
```bash
./node_modules/.bin/playwright test --headed --workers=1
```

### View HTML Report
```bash
./node_modules/.bin/playwright show-report
```

## Test Structure

### Positive Test Scenarios (12 tests)
Located in `ui-tests/regression/positive/`:
1. **happy-path.spec.ts** - Basic calculator flow (4 tests)
2. **currency-format.spec.ts** - Currency selection & formatting (4 tests)
3. **frequency.spec.ts** - Compounding frequency selection (4 tests)

### Negative Test Scenarios (24 tests)
Located in `ui-tests/regression/negative/`:
1. **input-guards.spec.ts** - Input validation (12 tests)
2. **boundary-behavior.spec.ts** - Edge cases & boundary conditions (12 tests)

## Test Selectors
The tests use Streamlit's element selectors:
```javascript
// Currency selector
page.getByRole('combobox').first()

// Principal amount input
page.getByLabel(/Principal Amount/)

// Contribute button (if exists) or run calculation trigger
page.getByLabel(/Monthly Contribution/)

// Results section
page.locator('[data-testid="stMetricValue"]')

// Chart
page.locator('.plotly-graph-div')
```

## Configuration Details

### playwright.config.ts
- **baseURL:** http://127.0.0.1:8501 (Streamlit default)
- **Timeout:** 60 seconds per test
- **Retries:** 1 (auto-retry failed tests)
- **Report formats:** List + HTML + JSON
- **webServer:** Auto-starts Streamlit before tests (no manual Streamlit run needed)

### Environment Variables
```bash
# Skip Firefox and WebKit, run only Chromium
export SKIP_BROWSERS="firefox,webkit"

# Run all browsers
export SKIP_BROWSERS=""

# Run tests
./node_modules/.bin/playwright test
```

## Troubleshooting

### "command not found: playwright"
```bash
# Use the full path to the executable
./node_modules/.bin/playwright test

# Or install globally
npm install -g @playwright/test
playwright test
```

### Streamlit port already in use
```bash
# Kill process on port 8501
lsof -ti:8501 | xargs kill -9

# Or change port in playwright.config.ts
baseURL: "http://127.0.0.1:8502"
```

### Browser not found
```bash
# Install browser binaries
./node_modules/.bin/playwright install chromium
```

### Tests hang or timeout
Check if Streamlit is already running on 8501:
```bash
ps aux | grep streamlit
```

## Next Steps

1. **Install Node.js** (choose one option from Prerequisites above)
2. **Verify installation** with `node --version && npm --version`
3. **Run tests** with `./node_modules/.bin/playwright test`
4. **View results** with `./node_modules/.bin/playwright show-report`

## Comparison: Unit Tests vs UI Tests

| Aspect | Pytest (Unit) | Playwright (UI) |
|--------|---------------|-----------------|
| Tests | 62 | 36 |
| Coverage | Core math, formatting, charting logic | User interactions, element visibility |
| Speed | ~0.5 seconds | ~30 seconds |
| Status | ✅ All passing | ⏳ Awaiting Node.js installation |
| Run Command | `python3 -m pytest tests/` | `./node_modules/.bin/playwright test` |

Together, these ~100 tests provide comprehensive coverage of both business logic and UI/UX.
