# Playwright UI Regression Testing Infrastructure

## Overview
A complete Playwright-based UI regression testing suite with **36 test scenarios** covering both positive (happy path) and negative (validation/boundary) use cases.

## Architecture

### Configuration: `playwright.config.ts`
```typescript
Key Features:
  • Browser Detection: Automatically skips unavailable browsers (Firefox, WebKit)
  • Only Chromium runs by default (environmentally aware)
  • webServer: Auto-starts Streamlit on port 8501
  • Reporters: List + HTML + JSON outputs
  • Timeouts: 60s per test, 10s per assertion
  • Auto-retry: 1 retry on failure
  • Screenshots: Captured on failure only
  • Trace: Full trace on retry for debugging
```

**Environment Variables:**
```bash
# Default: Run only Chromium (Firefox and WebKit skipped)
SKIP_BROWSERS="firefox,webkit"

# Run all browsers
SKIP_BROWSERS=""

# Skip single browser
SKIP_BROWSERS="firefox"
```

## Test Suite Structure

### Positive Testing (12 tests)
Tests the happy path where user inputs are valid.

#### File: `ui-tests/regression/positive/calculator.happy-path.spec.ts` (4 tests)
1. **Initial Load**
   - Verifies app loads without errors
   - Checks sidebar presence
   - Validates default currency is INR

2. **Calculate with Defaults**
   - Uses default inputs
   - Clicks "Run" or auto-calculates
   - Verifies total future value is displayed

3. **Calculate with Custom Inputs**
   - Principal: 50,000
   - Monthly: 500
   - Rate: 7.5%
   - Time: 15 years
   - Frequency: Quarterly
   - Verifies all metrics appear

4. **Chart Rendering**
   - Verifies Plotly chart renders
   - Checks chart title and axis labels
   - Validates hover tooltips show formatted currency

#### File: `ui-tests/regression/positive/calculator.currency-format.spec.ts` (4 tests)
1. **INR Formatting (Indian Style)**
   - Select INR from currency dropdown
   - Input: 1000000
   - Expected display: ₹10,00,000.00
   - Verify 2-2-2-3 grouping pattern

2. **USD Formatting (International Style)**
   - Select USD
   - Input: 1000000
   - Expected display: $1,000,000.00
   - Standard comma grouping

3. **EUR Formatting**
   - Select EUR
   - Input: 1000000
   - Expected display: €1,000,000.00

4. **Currency Switch**
   - Start with INR
   - Calculate with 50,000
   - Switch to USD
   - Verify all values reformat instantly
   - Switch to GBP, JPY - verify formatting

#### File: `ui-tests/regression/positive/calculator.frequency.spec.ts` (4 tests)
1. **Annually Compounding**
   - Select "Annually" from dropdown
   - Verify calculation changes

2. **Quarterly Compounding**
   - Select "Quarterly"
   - Verify higher result than annual

3. **Monthly Compounding**
   - Select "Monthly"
   - Verify higher result than quarterly

4. **Daily Compounding**
   - Select "Daily"
   - Verify highest result among all frequencies

### Negative Testing (24 tests)
Tests error handling, input validation, and boundary conditions.

#### File: `ui-tests/regression/negative/calculator.input-guards.spec.ts` (12 tests)
1. **Principal Validation**
   - Negative input should be rejected
   - Field prevents entry of negative values
   - Empty field defaults to 0

2. **Monthly Contribution Validation**
   - Negative input should be rejected
   - Field prevents entry of negative values
   - Empty field defaults to 0

3. **Annual Rate Validation**
   - Negative rate should be rejected
   - Zero rate is allowed (no growth)
   - Very high rates (>100%) are allowed but calculated correctly

4. **Time Validation**
   - Negative time should be rejected
   - Zero time returns principal only
   - Fractional years (e.g., 2.5) are supported

5. **Non-numeric Input**
   - Letters rejected
   - Special characters rejected
   - Field shows error state

6. **Boundary: Very Small Values**
   - Principal = 0.01
   - Monthly = 0.001
   - Rate = 0.01%
   - Time = 0.1 years
   - Calculation should not error

#### File: `ui-tests/regression/negative/calculator.boundary-behavior.spec.ts` (12 tests)
1. **Extreme Principal Values**
   - Principal = 0 (edge case)
   - Verify calculation returns monthly contributions only
   
2. **Extreme Contribution Values**
   - Monthly = 0 (no contributions)
   - Verify calculation is pure compound interest
   - Monthly = 10,000 (high contribution)
   - Verify calculation handles large sums

3. **Extreme Interest Rates**
   - Rate = 0% (no growth)
   - Verify linear growth from contributions
   - Rate = 500% (unrealistic but valid)
   - Verify calculation doesn't error

4. **Extreme Time Periods**
   - Time = 0.001 years (very short)
   - Time = 500 years (very long)
   - Verify no overflow/precision errors

5. **Stress: All Max Values**
   - Principal = 1,000,000
   - Monthly = 100,000
   - Rate = 100%
   - Time = 100 years
   - Verify calculation completes without timeout

6. **Stress: All Min Values**
   - Principal = 0
   - Monthly = 0
   - Rate = 0
   - Time = 0
   - Result should be 0

## Running Tests

### Setup (One-time)
```bash
cd /Users/bsubbarao/MYDATA/CompIntCalculator

# Install Node.js first (see PLAYWRIGHT_SETUP.md)
brew install node

# Or use the setup script
./setup-playwright.sh
```

### Run All Tests
```bash
./node_modules/.bin/playwright test
```

### Run with Reporting
```bash
# Run tests and show list output
./node_modules/.bin/playwright test --reporter=list

# Run tests in headed mode (watch in browser)
./node_modules/.bin/playwright test --headed

# Run single test file
./node_modules/.bin/playwright test ui-tests/regression/positive/calculator.happy-path.spec.ts
```

### View Results
```bash
# HTML report (interactive)
./node_modules/.bin/playwright show-report

# JSON report (programmatic)
cat playwright-results.json | jq '.'

# View test traces
./node_modules/.bin/playwright show-trace
```

## Element Selectors Used

Playwright uses multiple selector strategies for reliability:

```javascript
// Text-based (most reliable for Streamlit)
page.getByLabel(/Principal Amount/)
page.getByRole('combobox')
page.getByText('Calculate')

// Streamlit-specific
page.locator('[data-testid="stMetricValue"]')
page.locator('.plotly-graph-div')

// Fallback: CSS
page.locator('input[type="number"]')
```

## Expected Test Results

When Node.js is installed and tests run successfully:

**Positive Tests:** 12 ✅
- App loads and renders correctly
- Currency formatting works in all locales
- Compounding frequency affects calculations
- Chart and table display properly

**Negative Tests:** 24 ✅
- Invalid inputs are rejected
- Boundary conditions don't crash app
- Extreme values calculate correctly
- Error messages display appropriately

**Total: 36/36 ✅**

## Browser Coverage

| Browser | Status | Skip? | Notes |
|---------|--------|-------|-------|
| Chromium | ✅ Enabled | No | Desktop Chrome engine (recommended) |
| Firefox | ⏸️ Available | Yes (default) | Skipped if not available |
| WebKit | ⏸️ Available | Yes (default) | Safari engine, skipped by default |

To run on all browsers:
```bash
SKIP_BROWSERS="" ./node_modules/.bin/playwright test
```

## Debugging Failed Tests

### Check Streamlit is Running
```bash
ps aux | grep streamlit
```

### View Test Trace
```bash
./node_modules/.bin/playwright show-trace trace.zip
```

### Run Single Test Verbosely
```bash
./node_modules/.bin/playwright test --debug --headed
```

### Check Console Output
```bash
./node_modules/.bin/playwright test --reporter=line
```

## Integration with CI/CD

For GitHub Actions or similar CI systems:

```yaml
- name: Install Node.js
  uses: actions/setup-node@v3
  with:
    node-version: '20'

- name: Install Playwright
  run: npm install

- name: Run Playwright Tests
  run: SKIP_BROWSERS="firefox,webkit" npx playwright test

- name: Upload Report
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: playwright-report
    path: playwright-report/
```

## Relationship to Unit Tests

| Layer | Tool | Tests | Speed | Status |
|-------|------|-------|-------|--------|
| **Unit** | pytest | 62 | 0.5s | ✅ All passing |
| **UI/E2E** | Playwright | 36 | ~30s | ⏳ Awaiting setup |
| **Total** | - | 98 | ~30s | - |

**Unit tests** verify:
- Compound interest calculations
- Currency formatting (all locales)
- Chart data generation
- Summary table generation

**UI tests** verify:
- User interactions with sidebar
- Element visibility and layout
- Real browser rendering
- Form submission and validation

## File Manifest

```
CompIntCalculator/
├── playwright.config.ts                    # Configuration (NEW: browser detection)
├── setup-playwright.sh                     # Setup automation script (NEW)
├── package.json                            # Dependencies
├── package-lock.json                       # Locked versions
├── ui-tests/
│   └── regression/
│       ├── positive/
│       │   ├── calculator.happy-path.spec.ts
│       │   ├── calculator.currency-format.spec.ts
│       │   └── calculator.frequency.spec.ts
│       └── negative/
│           ├── calculator.input-guards.spec.ts
│           └── calculator.boundary-behavior.spec.ts
├── playwright-report/                      # Generated (after first test run)
├── playwright-results.json                 # Generated JSON results
└── .github/
    ├── PLAYWRIGHT_SETUP.md                 # Setup guide (NEW)
    ├── UI_REGRESSION_PLAYWRIGHT.md         # Test documentation
    ├── copilot-instructions.md
    └── TESTING_PERSONA.md
```

## Known Limitations

1. **Requires Node.js Installation** (not pre-installed)
2. **Firefox/WebKit** require additional browser binary installation
3. **Streamlit webServer** auto-starts but may conflict with existing instances on port 8501
4. **Selectors** depend on Streamlit's internal HTML structure (may change between versions)

## Next Steps

1. Install Node.js: `brew install node` or use nvm
2. Run setup script: `./setup-playwright.sh`
3. Execute tests: `./node_modules/.bin/playwright test`
4. View report: `./node_modules/.bin/playwright show-report`
5. Commit results to CI/CD pipeline

## Support

See `.github/PLAYWRIGHT_SETUP.md` for troubleshooting and detailed instructions.
