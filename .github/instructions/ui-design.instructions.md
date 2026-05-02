---
applyTo: "app.py"
description: "UI/UX design system for the Compound Interest Calculator — color palette, typography, layout, and component styling rules."
---

# UI/UX Design System — Compound Interest Calculator

## Color Scheme (Axis Bank Brand)

| Role             | Hex       | Used For                                         |
|------------------|-----------|--------------------------------------------------|
| Primary          | `#97144D` | Sidebar bg, metric cards, buttons, table headers, `h1` border |
| Primary Dark     | `#6B0F38` | Hover states, footer background, captions        |
| Primary Light    | `#C41E5B` | Highlights and accents                           |
| Page Background  | `#E8F0F9` | Main content area background                     |
| Text on Dark     | `#F5F5F5` | Labels and text on colored backgrounds           |
| Text on Light    | `#1A1A1A` | Body text on white/grey backgrounds              |
| White            | `#FFFFFF` | Sidebar input fields, button text                |

> Theme follows system default (light → `plotly_white`, dark → `plotly_dark` for Plotly charts).

---

## Typography

- **h1**: `font-weight: 800`, color `#97144D`, `border-bottom: 3px solid #97144D`
- **h2 / h3**: `font-weight: 700`, color `#6B0F38`
- **Metric values**: `font-size: 1.6rem`, `font-weight: 800`, white on `#97144D` card
- **Metric labels**: `font-weight: 600`, color `#F5F5F5`
- **Captions / footer**: `font-weight: 500`, color `#6B0F38`

---

## Layout

- **Sidebar (left)**: all user inputs — principal, monthly contribution, annual rate, time (years), compounding frequency, currency selector
- **Main area** (left → right, top → bottom):
  1. Summary metric cards row (Future Value, Interest Earned, Total Invested)
  2. Interactive Plotly line chart (balance growth over time)
  3. Year-over-year summary data table

---

## Component Styling

### Sidebar inputs
- Background: `#FFFFFF`, text: `#1A1A1A`, `border-radius: 4px`
- Labels: `#F5F5F5`, `font-weight: 600`

### Metric cards
- Background: `#97144D`, `border-radius: 8px`, `padding: 16px 20px`
- Value text: `#FFFFFF`, `font-weight: 800`, `font-size: 1.6rem`

### Buttons
- Default: `background #97144D`, white bold text, no border, `border-radius: 4px`
- Hover: `background #6B0F38`

### Data table
- Header row: `background #97144D`, white bold text

### Plotly chart
- Template: `plotly_white` (light mode) / `plotly_dark` (dark mode) — resolved at runtime via `st.get_option("theme.base")`

---

## Currency & Formatting Rules

| Currency | Symbol | Format Style   | Example           |
|----------|--------|----------------|-------------------|
| INR      | ₹      | Indian commas  | ₹1,00,000.00      |
| USD      | $      | International  | $100,000.00       |
| EUR      | €      | International  | €100,000.00       |
| GBP      | £      | International  | £100,000.00       |
| JPY      | ¥      | International  | ¥100,000.00       |

- All monetary values display **2 decimal places**.
- All currency variable names **must be prefixed with `money_`**.

---

## Constraints

- No global variables — all styling logic encapsulated in functions (e.g., `inject_axis_bank_styles()`, `get_plotly_template()`).
- `FREQUENCY_OPTIONS` dict in `app.py` is the **single source of truth** for compounding frequency dropdown values.
- All inputs must be validated as non-negative before any calculation.
