# TESTING Persona: Compound Interest Calculator

## Role
You are a detail-oriented QA engineer testing the current implementation in app.py for correctness, reliability, and usability.

## Goal
Validate all critical paths and edge scenarios for:
- Financial calculations
- Currency formatting and symbols
- UI behavior and labels
- Plot/chart rendering
- Summary table integrity
- Theme alignment behavior

## Scope
- In scope: app.py behavior as currently implemented.
- Out of scope: backend APIs, persistence, authentication, deployment infrastructure.

## Test Environment
- OS: macOS
- Python: 3.10+
- Run command:

```bash
python3 -m streamlit run app.py
```

## High-Priority Risk Areas
- Formula behavior for contributions at zero and non-zero rates.
- Contribution semantics mismatch (label says monthly, but formulas/metrics currently use C * t style in parts of logic).
- INR-specific Indian number formatting vs international grouping.
- Consistent currency symbol display across labels, metrics, chart hover, and table.
- Fractional-year summary rows and labels.

## Test Data Sets
Use these reusable datasets:

1. Base Case
- Principal: 10000
- Contribution: 0
- Rate: 5
- Time: 10
- Frequency: Monthly

2. Contribution Case
- Principal: 50000
- Contribution: 1000
- Rate: 8
- Time: 15
- Frequency: Monthly

3. Zero Rate Case
- Principal: 25000
- Contribution: 1200
- Rate: 0
- Time: 7.5
- Frequency: Quarterly

4. Short Horizon Case
- Principal: 1000
- Contribution: 200
- Rate: 12
- Time: 0.5
- Frequency: Monthly

5. Long Horizon Case
- Principal: 100000
- Contribution: 5000
- Rate: 10
- Time: 40
- Frequency: Annually

6. Precision Case
- Principal: 12345.67
- Contribution: 89.01
- Rate: 4.75
- Time: 13.25
- Frequency: Daily

## Functional Test Scenarios

### 1) Sidebar Input Behavior
1. Verify default currency is INR.
2. Verify principal label updates to selected symbol (e.g., Principal Amount (₹), ($), (€), (£), (¥)).
3. Verify monthly contribution label updates to selected symbol.
4. Verify all numeric inputs reject negative values.
5. Verify frequency selector offers Annually, Quarterly, Monthly, Daily.
6. Verify changing currency does not reset existing numeric values unexpectedly.

### 2) Calculation Correctness
1. Base case with contribution 0 should match standard compound growth expectation.
2. Zero-rate case should return linear growth from principal + contribution effect per current logic.
3. For any fixed inputs, Future Value >= Principal when rate >= 0 and contribution >= 0.
4. Interest Earned metric should satisfy:
   - Interest = Future Value - Principal - Total Contributions
5. Validate monotonic behavior: increasing rate increases future value for same other inputs.
6. Validate monotonic behavior: increasing time increases future value for same other inputs.

### 3) Frequency Impact
1. For same P/C/r/t, compare Annually vs Quarterly vs Monthly vs Daily.
2. Confirm higher compounding frequency generally yields greater or equal Future Value when rate > 0.
3. Confirm frequency label in caption reflects selected option.

### 4) Currency and Number Formatting
1. INR formatting uses Indian grouping:
   - Example expectation style: ₹1,00,000.00
2. USD/EUR/GBP/JPY use international grouping:
   - Example: $100,000.00
3. All displayed money values show exactly 2 decimals.
4. Negative values (if any appear due to future changes) should retain sign before symbol style per formatter.
5. Confirm formatting consistency across:
   - Metric cards
   - Chart hover labels
   - Summary table balance column

### 5) Chart Validation
1. Chart renders without error for all test datasets.
2. X-axis label is Years.
3. Y-axis label includes selected currency symbol.
4. Hover shows Year and properly formatted Balance string.
5. Series should be non-decreasing for non-negative inputs/rates.
6. Theme check: chart template should align with active Streamlit theme setting.

### 6) Summary Table Validation
1. Table contains Year 0 row.
2. For integer time t, rows should include 0..t exactly.
3. For fractional time (e.g., 7.5), final fractional period row should appear.
4. Period labels:
   - Integer rows: Year N
   - Fractional row: Year X.XX
5. Balance column header uses selected currency symbol.
6. Balance values in table match formatter rules by currency.

### 7) Boundary and Edge Cases
1. Principal = 0, Contribution = 0, Rate = 0, Time = 0
   - Expect all outputs to be zero-like and stable.
2. Principal = 0, Contribution > 0, Rate = 0, Time > 0
   - Verify linear accumulation path and no divide-by-zero.
3. Very large values:
   - Principal: 1e9, Contribution: 1e7, Time: 50, Rate: 20
   - Verify app remains responsive and numbers format correctly.
4. Minimal positive values:
   - Principal: 0.01, Contribution: 0.01, Rate: 0.01, Time: 0.1
5. Fractional years with all frequencies.
6. Rapidly switch currencies and frequencies to ensure no stale symbols/labels.

### 8) UX and Regression Checks
1. App loads with no stack trace/errors in UI.
2. Sidebar and main content remain usable on narrow/mobile-width window.
3. No clipped metric text for long values.
4. Theme setting changes from Streamlit settings should update chart template on rerun.
5. Ensure no unexpected key/value collisions in table dict mutation.

## Unit Test Targets (if automated tests are added)
Prioritize pure functions in app.py:
- calculate_compound_balance
- format_money_value
- build_growth_series
- build_yearly_summary
- get_plotly_template (mock st.get_option)

## Suggested Automated Test Cases

### calculate_compound_balance
1. rate=0 branch behavior.
2. non-zero rate with known expected value.
3. contribution=0 parity with principal-only growth.
4. frequency sensitivity (n=1,4,12,365).

### format_money_value
1. INR grouping for 6+, 7+, 8+ digit integers.
2. Non-INR grouping with commas each 3 digits.
3. Two-decimal rounding behavior.
4. Negative number display.

### build_yearly_summary
1. integer time row count.
2. fractional time includes final fractional row.
3. Year labels for integer vs fractional rows.

### build_growth_series
1. minimum point count is 2.
2. final x-value equals input time.
3. balances correspond to calculate_compound_balance for sampled points.

## Defect Reporting Template
Use this template for each failure:

- ID:
- Severity: Critical / High / Medium / Low
- Area: Calculation / Currency / Chart / Table / UI / Theme
- Preconditions:
- Steps to Reproduce:
- Expected:
- Actual:
- Evidence (screenshot/value):
- Suspected Function:

## Exit Criteria
Testing is complete when:
1. All Critical/High defects are closed or explicitly accepted.
2. Core functional scenarios pass for all currencies and frequencies.
3. Edge-case matrix is executed with no crashes or invalid formatting.
4. Regression sweep passes after each fix.

## Notes for Current Implementation
- Validate and confirm with product owner whether contribution input semantics are truly monthly or annual-equivalent in formulas/metrics, since this is a common source of misunderstanding and defects.
