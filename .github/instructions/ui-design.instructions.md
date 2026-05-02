---
applyTo: "app.py"
description: "UI/UX design system for the Compound Interest Calculator — color palette, typography, layout, and component styling rules."
---

# UI/UX Design System — Compound Interest Calculator

## Color Scheme (Dark Green Fintech)

Inspired by premium fintech dashboard aesthetics (deep forest green base, neon green accents).

| Role              | Hex       | Constant            | Used For                                              |
|-------------------|-----------|---------------------|-------------------------------------------------------|
| Page Background   | `#0B1612` | `THEME_BG`          | Main content area, chart plot background              |
| Sidebar Background| `#0D1F16` | `THEME_SIDEBAR`     | Sidebar, footer background                            |
| Card Background   | `#112218` | `THEME_CARD`        | Metric cards, chart paper background, table rows      |
| Neon Green        | `#39D353` | `THEME_GREEN`       | h1, metric values, buttons, chart line, sidebar labels|
| Green Dark        | `#28A745` | `THEME_GREEN_DARK`  | Button hover state                                    |
| Primary Text      | `#FFFFFF` | `THEME_TEXT_PRIMARY`| All body text, headings, input text                   |
| Muted Text        | `#6B7280` | `THEME_TEXT_MUTED`  | Metric labels, captions, footer text                  |
| Input Background  | `#1A2E1F` | `THEME_INPUT_BG`    | Sidebar input field backgrounds                       |
| Border            | `#1E3A27` | `THEME_BORDER`      | Card borders, sidebar border, header underline        |

> Plotly template is always `plotly_dark` with `paper_bgcolor=THEME_CARD` and `plot_bgcolor=THEME_BG`.

### Chart Line Colors (Multi-Rate Variance)
| Scenario     | Color     | Usage         |
|--------------|-----------|---------------|
| Lower rate   | `#F59E0B` | Amber line    |
| Base rate    | `#39D353` | Neon green    |
| Higher rate  | `#60A5FA` | Soft blue     |

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
