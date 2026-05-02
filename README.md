# Compound Interest Calculator

A single-page Streamlit app for exploring compound interest growth over time.

## Features

- Sidebar inputs for principal, optional monthly contribution, annual interest rate, time, and compounding frequency
- Multi-currency support: INR (₹), USD ($), EUR (€), GBP (£), JPY (¥) — INR values use Indian-style comma formatting
- Optional **Interest Rate Variance Range** — overlay lower, base, and upper rate scenarios on a single chart
- Three summary metrics: Future Value, Total Contributions, and Interest Earned
- Interactive Plotly growth chart (single-rate or multi-rate variance view)
- Year-by-year balance table (with per-rate columns when variance is active)

## Compounding Frequencies

| Label | Periods per year |
|---|---|
| Annually | 1 |
| Half Yearly | 2 |
| Quarterly | 4 |
| Monthly | 12 |
| Semi-Monthly | 24 |
| Weekly | 52 |
| Daily | 365 |

## Formula

The calculator uses the compound interest formula with optional periodic contributions:

$$
A = P\left(1 + \frac{r}{n}\right)^{nt} + C \cdot \frac{\left(1 + \frac{r}{n}\right)^{nt} - 1}{\frac{r}{n}}
$$

Where:

- $P$ is the principal amount
- $C$ is the periodic contribution amount
- $r$ is the annual interest rate (decimal)
- $n$ is the number of compounding periods per year
- $t$ is the time in years

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the app:

```bash
streamlit run app.py
```

## Testing

Run unit tests:

```bash
bash scripts/run_tests_with_log.sh
```

Run UI regression tests (requires Playwright):

```bash
bash scripts/run_ui_regression.sh
```

## AI Workflow Framework

This project includes an automated issue workflow orchestration system. When a GitHub issue is opened, the framework runs a multi-step pipeline (Product Owner → Developer → Unit Tester → UI Tester → PR creation) with blocking gates to ensure code quality.

Start a workflow via the local API server (port 8090):

```bash
POST http://localhost:8090/workflows/start
{ "issue_number": <number> }
```

Monitor active workflows with the dashboard:

```bash
streamlit run scripts/ai_orchestration_dashboard.py
```