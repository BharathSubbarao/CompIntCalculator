# UI Regression Test Plan (Playwright)

## Objective
Create and run a dedicated UI regression suite for the Compound Interest Calculator, with **both positive and negative test outcomes visible in a web page report**.

## Scope
Covers end-to-end UI validation for:
- Sidebar inputs and labels
- Currency behavior and formatting
- Frequency selection behavior
- Metrics, chart, and summary table consistency
- Theme-aware chart rendering
- Validation behavior for disallowed input patterns

## Tools
- Playwright Test (`@playwright/test`)
- Playwright HTML Report (`npx playwright show-report`)

## Suggested Test Layout
```text
ui-tests/
  regression/
    positive/
      calculator.happy-path.spec.ts
      calculator.currency-format.spec.ts
      calculator.frequency.spec.ts
      calculator.theme-chart.spec.ts
    negative/
      calculator.input-guards.spec.ts
      calculator.boundary-behavior.spec.ts
```

## Browser Coverage
Run on:
- Chromium
- Firefox
- WebKit

## Base URL
Use the running Streamlit app URL as `baseURL` in Playwright config, for example:
- `http://localhost:8501`

## Positive UI Scenarios

### 1) App Smoke
1. App loads successfully.
2. Title `Compound Interest Calculator` is visible.
3. Sidebar `Inputs` section is visible.

### 2) Currency Selector and Dynamic Labels
1. Default currency is INR.
2. Change currency to USD/EUR/GBP/JPY.
3. Verify labels update dynamically:
   - `Principal Amount (<symbol>)`
   - `Monthly Contribution (<symbol>)`
4. Verify table balance header uses selected symbol.

### 3) Frequency Options
1. Verify options exist: Annually, Quarterly, Monthly, Daily.
2. Select each frequency and verify caption text reflects current selection.
3. For same P/C/r/t, verify future value remains stable with deterministic behavior per implementation.

### 4) Metrics Validation
1. Verify all three metrics are shown:
   - Future Value
   - Total Contributions
   - Interest Earned
2. Verify values are formatted with two decimals.
3. Verify metric values are not blank/NaN.

### 5) Currency Formatting Rules
1. INR uses Indian grouping (example: `₹1,00,000.00`).
2. Non-INR currencies use international grouping (example: `$100,000.00`).
3. Verify formatting consistency across:
   - Metrics
   - Chart hover text
   - Summary table balance column

### 6) Chart Validation
1. Chart is visible.
2. X-axis is `Years`.
3. Y-axis title includes selected symbol.
4. Hover tooltip shows `Year` and formatted `Balance`.
5. Line appears non-decreasing for non-negative inputs.

### 7) Summary Table Validation
1. Table is visible.
2. Contains Year 0 row.
3. Integer time gives rows `0..t`.
4. Fractional time includes `Year X.XX` terminal row.

### 8) Theme/Template Behavior
1. With Streamlit light theme, chart template appears light.
2. With Streamlit dark theme, chart template appears dark.

## Negative UI Scenarios

### 1) Non-Negative Guardrails
1. Attempt to decrement principal below 0 using spinner controls.
2. Attempt to decrement contribution below 0.
3. Attempt to decrement rate below 0.
4. Attempt to decrement time below 0.
5. Expected: values remain at `0` minimum, no app crash.

### 2) Boundary Stress Inputs
1. Very large values (for example principal `1e9`, contribution `1e7`, time `50`, rate `20`).
2. Minimal positive values (for example `0.01`).
3. Expected: UI remains responsive and values still render with correct formatting.

### 3) Rapid User Changes
1. Rapidly change currency and frequency multiple times.
2. Expected: labels, metrics, chart axis, and table column stay synchronized.

### 4) Fractional and Zero-Time Edge Cases
1. Time `0` should show Year 0 only.
2. Fractional time (for example `7.5`) should include terminal fractional row.
3. Expected: no rendering errors.

## Result Presentation in a Web Page

### Option A (Recommended): Built-in Playwright HTML Report
This naturally shows both pass and fail results in a browser.

Run sequence:
```bash
python3 -m streamlit run app.py
# in another terminal
npx playwright test
npx playwright show-report
```

### Option B: Custom Summary Web Page
Generate JSON and render a custom page with pass/fail counters.

```bash
npx playwright test --reporter=json > playwright-results.json
```

Then transform `playwright-results.json` into an `ui-regression-report.html` page with:
- Total tests
- Passed tests
- Failed tests
- Skipped tests
- Failed test names + error snippets

## Evidence to Capture per Scenario
- Screenshot on failure
- Optional trace/video for flaky behavior
- Step-level assertion messages

## CI Recommendation
Use CI to publish HTML report artifact per run so regressions are reviewable from the browser.

## Exit Criteria
1. All critical positive scenarios pass on Chromium, Firefox, and WebKit.
2. Negative guardrail tests confirm non-crashing behavior and input boundaries.
3. HTML report is generated and reviewable in a web page for each run.
