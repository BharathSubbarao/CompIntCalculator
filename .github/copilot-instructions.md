# Project: Python Compound Interest Calculator (Web App)

## 🎯 Role
You are an expert Python developer specializing in clean, mathematical web applications. Your goal is to build a high-performance, single-page compound interest calculator.

## 🛠 Tech Stack
- **Language**: Python 3.10+
- **Web Framework**: Streamlit (Preferred for rapid single-page apps)
- **Data Visualization**: Plotly (For interactive charts)
- **Formatting**: PEP 8 standards

## 🏗 Project Structure
- `app.py`: Main application file containing the logic and UI.
- `requirements.txt`: Project dependencies.
- `README.md`: Human-readable setup instructions.

## 📋 Core Features & Logic
1. **User Inputs**:
   - Principal Amount ($P$)
   - Monthly Contribution (optional) ($C$)
   - Annual Interest Rate ($r$ in %)
   - Time ($t$ in years)
   - Compounding Frequency ($n$, e.g., Monthly, Quarterly, Annually)
2. **Formula**: 
   - $A = P(1 + r/n)^{nt} + C \frac{(1 + r/n)^{nt} - 1}{r/n}$
3. **Visuals**:
   - A dynamic line chart showing growth over time.
   - A summary table showing year-over-year balance.
4. **Summary Metrics**:
   - Total Future Value ($A$)
   - Total Interest Earned ($A - P - C \cdot t$)
5. **Currency**:
   - Default currency is INR, but allow users to select from a dropdown (e.g., USD, EUR, GBP, JPY).
   - Display all monetary values with the appropriate currency symbol.
   - Display INR values with the '₹' symbol, USD with '$', EUR with '€', GBP with '£', and JPY with '¥'.
   - Display all monetary values with two decimal places for consistency and clarity.
   - Display all monetary values in INR with comma separators in Indian style (e.g., 1,00,000.00 for one lakh) and in international style for other currencies (e.g., 100,000.00 for one hundred thousand).

## 🎨 UI & Styling
- **Default State**: Set the default theme to match the user's system settings.
- **Design System**: Full color palette, typography, layout, and component styling rules are defined in
  [`.github/instructions/ui-design.instructions.md`](.github/instructions/ui-design.instructions.md).
  Always consult that file before making any UI changes.


## ⚠️ Boundaries & Rules
- **Modern Syntax**: Use type hinting for all functions.
- **Error Handling**: Validate that inputs are non-negative.
- **Clean UI**: Use a sidebar for inputs and the main area for results and graphs.
- **No Global Variables**: Encapsulate logic within functions.
- **Currency Variables**: All variable names for currency must start with the prefix 'money_'.

## 🚦 Issue Workflow — Mandatory Implementation Gates

These rules are **blocking requirements** for every automated issue workflow. A workflow MUST NOT proceed to PR creation unless ALL gates pass.

### Gate 1 — Functional Coverage (Developer Step)
- Read the issue title and body to extract the exact functional requirement.
- Identify which file(s) in the app must change (e.g., `app.py` for UI features).
- Make the code change **before** running tests or creating a commit.
- **BLOCK** if: the issue is a product feature but no `app.py` change has been made.
- **BLOCK** if: the only changed files are workflow/infra files (`ai_workflow/`, `scripts/`, `playwright.config.ts`).

### Gate 2 — Unit Test Delta (Unit Tester Step)
- For every new feature or changed behavior, add or update tests in `tests/test_app.py`.
- New test names must directly reference the new feature (e.g., `test_weekly_frequency_...`).
- **BLOCK** if: no new or modified test covers the implemented feature.
- Run tests with `bash scripts/run_tests_with_log.sh` and assert all pass.

### Gate 3 — UI Regression Test Delta (UI Tester Step)
- For every new UI option or visible change, add or update Playwright tests in `ui-tests/regression/`.
- New scenario must verify the new UI element exists and behaves correctly.
- **BLOCK** if: no Playwright test references the new UI option (e.g., a new dropdown item).
- Run regression with `bash scripts/run_ui_regression.sh` and assert all pass.

### Gate 4 — Traceability (PR Step)
- PR body must include a checklist mapping each acceptance criterion to:
  - the changed file(s)
  - the unit test(s) added/updated
  - the Playwright test(s) added/updated
- **BLOCK** if: acceptance criteria are not fully covered by code and test changes.

### Compounding Frequency Reference
The `frequency_options` dict in `app.py` is the single source of truth for dropdown values.
Valid compounds_per_year mappings to maintain consistency:
- Annually = 1, Quarterly = 4, Monthly = 12, Bi-Weekly = 26, Weekly = 52, Daily = 365


## 🚀 Commands
- **Install**: `pip3 install streamlit plotly`
- **Run**: `python3 -m streamlit run app.py`
