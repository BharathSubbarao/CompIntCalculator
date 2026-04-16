# Compound Interest Calculator

A single-page Streamlit app for exploring compound interest growth over time.

## Features

- Sidebar inputs for principal, annual interest rate, time, and compounding frequency
- Future value and interest-earned summary metrics
- Interactive Plotly growth chart
- Year-by-year balance table

## Formula

The calculator uses the compound interest formula:

$$
A = P\left(1 + \frac{r}{n}\right)^{nt}
$$

Where:

- $P$ is the principal amount
- $r$ is the annual interest rate
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