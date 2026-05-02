---
applyTo: "app.py"
description: "UI/UX design system for the Compound Interest Calculator — color palette, typography, layout, and component styling rules."
---

# UI/UX Design System — Compound Interest Calculator

## Color Scheme (Dark Teal Wealth)

| Role              | Hex       | Constant            | Used For                                              |
|-------------------|-----------|---------------------|-------------------------------------------------------|
| Page Background   | `#1A1F2E` | `THEME_BG`          | Main content area background, header bar              |
| Sidebar Background| `#222836` | `THEME_SIDEBAR`     | Sidebar bg, footer background                         |
| Primary Teal      | `#0D9488` | `THEME_TEAL`        | Metric cards, buttons, `h2`/`h3`, `h1` border         |
| Teal Dark         | `#0F766E` | `THEME_TEAL_DARK`   | Button hover, table header                            |
| Emerald Highlight | `#34D399` | `THEME_TEAL_LIGHT`  | `h1` color, footer links, highlights                  |
| Primary Text      | `#E8EAF0` | `THEME_TEXT_PRIMARY`| Body text, sidebar labels, metric labels              |
| Muted Text        | `#9BA3B2` | `THEME_TEXT_MUTED`  | Captions, footer text                                 |
| White             | `#FFFFFF` | `THEME_WHITE`       | Sidebar input fields, button text, metric values      |
| Input Text        | `#1A1A1A` | `THEME_INPUT_TEXT`  | Dark text inside input fields                         |

> Plotly chart template is always `plotly_dark` to match the dark background.

---

## Typography

- **h1**: `font-weight: 800`, color `#34D399` (emerald), `border-bottom: 3px solid #0D9488`
- **h2 / h3**: `font-weight: 700`, color `#0D9488` (teal)
- **Body text**: color `#E8EAF0`
- **Metric values**: `font-size: 1.6rem`, `font-weight: 800`, white on `#0D9488` card
- **Metric labels**: `font-weight: 600`, color `#E8EAF0`
- **Captions / footer**: `font-weight: 500`, color `#9BA3B2`

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
- Labels: `#E8EAF0`, `font-weight: 600`

### Metric cards
- Background: `#0D9488`, `border-radius: 8px`, `padding: 16px 20px`
- Value text: `#FFFFFF`, `font-weight: 800`, `font-size: 1.6rem`

### Buttons
- Default: `background #0D9488`, white bold text, no border, `border-radius: 4px`
- Hover: `background #0F766E`

### Data table
- Header row: `background #0F766E`, white bold text

### Plotly chart
- Template: always `plotly_dark` to match the dark background

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
