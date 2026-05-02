from __future__ import annotations

from math import floor, isclose

import numpy  # noqa: F401
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def get_plotly_template() -> str:
    """
    Return a Plotly template that follows the active Streamlit theme.
    """
    base_theme = st.get_option("theme.base")
    return "plotly_dark" if base_theme == "dark" else "plotly_white"


# ── Dark Green Fintech color palette ──────────────────────────────────────────
THEME_BG = "#0B1612"           # Very dark green-black page background
THEME_SIDEBAR = "#0D1F16"      # Slightly lighter dark green sidebar
THEME_CARD = "#112218"         # Dark green card / panel background
THEME_GREEN = "#39D353"        # Neon green primary accent
THEME_GREEN_DARK = "#28A745"   # Deeper green for hover / table headers
THEME_GREEN_GLOW = "#39D353"   # Chart line color (bright neon green)
THEME_TEXT_PRIMARY = "#FFFFFF" # Pure white primary text
THEME_TEXT_MUTED = "#6B7280"   # Muted grey secondary text
THEME_INPUT_BG = "#1A2E1F"     # Dark green input field background
THEME_INPUT_TEXT = "#FFFFFF"   # White text inside inputs
THEME_BORDER = "#1E3A27"       # Subtle green-tinted border


def inject_app_styles() -> None:
    """Inject CSS to apply the Dark Green Fintech color scheme across the app UI."""
    css = f"""
    <style>
        /* ── Page background ── */
        .stApp {{
            background-color: {THEME_BG};
        }}

        /* ── Top header bar ── */
        header[data-testid="stHeader"] {{
            background-color: {THEME_BG} !important;
            border-bottom: 1px solid {THEME_BORDER} !important;
        }}

        /* ── App title rendered via st.title ── */
        h1 {{
            color: {THEME_GREEN} !important;
            font-weight: 800 !important;
            border-bottom: 2px solid {THEME_GREEN};
            padding-bottom: 8px;
            letter-spacing: -0.5px;
        }}

        /* ── Section headings (st.subheader) ── */
        h2, h3 {{
            color: {THEME_TEXT_PRIMARY} !important;
            font-weight: 700 !important;
        }}

        /* ── Body text ── */
        p, li, span, label {{
            color: {THEME_TEXT_PRIMARY};
        }}

        /* ── Sidebar background and text ── */
        section[data-testid="stSidebar"] {{
            background-color: {THEME_SIDEBAR} !important;
            border-right: 1px solid {THEME_BORDER} !important;
        }}
        section[data-testid="stSidebar"] * {{
            color: {THEME_TEXT_PRIMARY} !important;
        }}
        section[data-testid="stSidebar"] .stSelectbox label,
        section[data-testid="stSidebar"] .stNumberInput label,
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {{
            color: {THEME_GREEN} !important;
            font-weight: 600 !important;
        }}
        /* Sidebar input fields */
        section[data-testid="stSidebar"] input,
        section[data-testid="stSidebar"] .stSelectbox > div > div {{
            background-color: {THEME_INPUT_BG} !important;
            color: {THEME_INPUT_TEXT} !important;
            border: 1px solid {THEME_BORDER} !important;
            border-radius: 6px;
        }}

        /* ── Metric cards ── */
        div[data-testid="stMetric"] {{
            background-color: {THEME_CARD};
            border: 1px solid {THEME_BORDER};
            border-radius: 10px;
            padding: 16px 20px;
        }}
        div[data-testid="stMetric"] label,
        div[data-testid="stMetric"] div[data-testid="stMetricLabel"] {{
            color: {THEME_TEXT_MUTED} !important;
            font-weight: 500 !important;
            font-size: 0.85rem !important;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        div[data-testid="stMetric"] div[data-testid="stMetricValue"] {{
            color: {THEME_GREEN} !important;
            font-weight: 800 !important;
            font-size: 1.6rem !important;
        }}

        /* ── Primary buttons ── */
        .stButton > button {{
            background-color: {THEME_GREEN} !important;
            color: #0B1612 !important;
            border: none !important;
            border-radius: 6px !important;
            font-weight: 700 !important;
            padding: 8px 20px !important;
            letter-spacing: 0.3px;
        }}
        .stButton > button:hover {{
            background-color: {THEME_GREEN_DARK} !important;
            box-shadow: 0 0 12px rgba(57, 211, 83, 0.4) !important;
        }}

        /* ── Dataframe / table ── */
        thead tr th {{
            background-color: {THEME_CARD} !important;
            color: {THEME_GREEN} !important;
            font-weight: 700 !important;
            border-bottom: 1px solid {THEME_BORDER} !important;
        }}
        tbody tr {{
            background-color: {THEME_BG} !important;
            color: {THEME_TEXT_PRIMARY} !important;
        }}
        tbody tr:nth-child(even) {{
            background-color: {THEME_CARD} !important;
        }}

        /* ── Caption / footer text ── */
        .stCaption, div[data-testid="stCaptionContainer"] p {{
            color: {THEME_TEXT_MUTED} !important;
            font-weight: 400;
        }}

        /* ── Footer banner ── */
        footer {{
            background-color: {THEME_SIDEBAR} !important;
            color: {THEME_TEXT_MUTED} !important;
            border-top: 1px solid {THEME_BORDER} !important;
        }}
        footer a {{
            color: {THEME_GREEN} !important;
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


# Frequency mapping: single source of truth for dropdown and calculations
FREQUENCY_OPTIONS = {
    "Annually": 1,
    "Half Yearly": 2,
    "Quarterly": 4,
    "Monthly": 12,
    "Semi-Monthly": 24,
    "Weekly": 52,
    "Daily": 365,
}


def calculate_compound_balance(
    money_principal: float,
    money_monthly_contribution: float,
    annual_rate_percent: float,
    time_years: float,
    compounds_per_year: int,
) -> float:
    rate_decimal = annual_rate_percent / 100
    total_periods = compounds_per_year * time_years
    # "Monthly Contribution" is always 12 payments/year; convert to the per-compounding-period amount.
    periodic_contribution = money_monthly_contribution * 12 / compounds_per_year
    if rate_decimal == 0:
        return money_principal + (money_monthly_contribution * 12 * time_years)

    periodic_rate = rate_decimal / compounds_per_year
    growth_multiplier = (1 + periodic_rate) ** total_periods
    return money_principal * growth_multiplier + periodic_contribution * (
        (growth_multiplier - 1) / periodic_rate
    )


def format_money_value(
    money_amount: float,
    money_currency_symbol: str,
    money_currency_code: str,
) -> str:
    money_sign = "-" if money_amount < 0 else ""
    money_absolute = abs(money_amount)

    if money_currency_code == "INR":
        money_integer_part, money_decimal_part = f"{money_absolute:.2f}".split(".")
        if len(money_integer_part) <= 3:
            money_grouped = money_integer_part
        else:
            money_last_three = money_integer_part[-3:]
            money_remaining = money_integer_part[:-3]
            money_groups: list[str] = []
            while len(money_remaining) > 2:
                money_groups.insert(0, money_remaining[-2:])
                money_remaining = money_remaining[:-2]
            if money_remaining:
                money_groups.insert(0, money_remaining)
            money_grouped = ",".join([*money_groups, money_last_three])

        return (
            f"{money_sign}{money_currency_symbol}{money_grouped}.{money_decimal_part}"
        )

    return f"{money_sign}{money_currency_symbol}{money_absolute:,.2f}"


def style_summary_dataframe(rows: list[dict], balance_columns: list[str] | None = None) -> pd.io.formats.style.Styler:
    """Apply dark-green fintech styling to the year-by-year summary grid.

    Applies:
    - Dark card background with alternating row shading
    - Neon green color scale on balance column(s) (low → muted, high → bright green)
    - Consistent white text throughout
    """
    df = pd.DataFrame(rows)

    row_even = f"background-color: {THEME_CARD}; color: {THEME_TEXT_PRIMARY};"
    row_odd = f"background-color: {THEME_BG}; color: {THEME_TEXT_PRIMARY};"

    def alternate_rows(row: pd.Series) -> list[str]:
        style = row_even if row.name % 2 == 0 else row_odd
        return [style] * len(row)

    styler = (
        df.style
        .apply(alternate_rows, axis=1)
        .set_table_styles([
            {
                "selector": "thead th",
                "props": [
                    ("background-color", THEME_CARD),
                    ("color", THEME_GREEN),
                    ("font-weight", "700"),
                    ("text-transform", "uppercase"),
                    ("letter-spacing", "0.5px"),
                    ("font-size", "0.8rem"),
                    ("border-bottom", f"2px solid {THEME_GREEN}"),
                    ("padding", "10px 12px"),
                ],
            },
            {
                "selector": "td",
                "props": [
                    ("padding", "8px 12px"),
                    ("border-bottom", f"1px solid {THEME_BORDER}"),
                    ("font-size", "0.9rem"),
                ],
            },
        ])
    )

    # Apply green gradient color scale to each balance column
    balance_cols = balance_columns or [c for c in df.columns if c not in ("Period", "Years")]
    for col in balance_cols:
        if col in df.columns:
            styler = styler.background_gradient(
                cmap="Greens",
                subset=[col],
                vmin=df[col].min() if pd.api.types.is_numeric_dtype(df[col]) else None,
            )

    return styler


def build_growth_series(
    money_principal: float,
    money_monthly_contribution: float,
    annual_rate_percent: float,
    time_years: float,
    compounds_per_year: int,
) -> list[dict[str, float]]:
    point_count = max(2, int(time_years * 12) + 1)
    year_points = [index * time_years / (point_count - 1) for index in range(point_count)]

    money_growth_rows: list[dict[str, float]] = []
    for year_value in year_points:
        money_balance = calculate_compound_balance(
            money_principal,
            money_monthly_contribution,
            annual_rate_percent,
            year_value,
            compounds_per_year,
        )
        money_growth_rows.append(
            {
                "Years": year_value,
                "Balance": money_balance,
            }
        )

    return money_growth_rows


def build_yearly_summary(
    money_principal: float,
    money_monthly_contribution: float,
    annual_rate_percent: float,
    time_years: float,
    compounds_per_year: int,
) -> list[dict[str, str | float]]:
    completed_years = floor(time_years)
    year_markers = [float(year_number) for year_number in range(completed_years + 1)]

    if time_years > 0 and not isclose(year_markers[-1], time_years):
        year_markers.append(time_years)

    money_summary_rows: list[dict[str, str | float]] = []
    for year_value in year_markers:
        money_balance = calculate_compound_balance(
            money_principal,
            money_monthly_contribution,
            annual_rate_percent,
            year_value,
            compounds_per_year,
        )
        period_label = f"Year {int(year_value)}" if year_value.is_integer() else f"Year {year_value:.2f}"
        money_summary_rows.append(
            {
                "Period": period_label,
                "Years": year_value,
                "Balance ($)": round(money_balance, 2),
            }
        )

    return money_summary_rows


def build_growth_chart(
    money_growth_rows: list[dict[str, float]],
    money_currency_symbol: str,
    money_currency_code: str,
) -> go.Figure:
    money_hover_values = [
        format_money_value(
            row["Balance"],
            money_currency_symbol,
            money_currency_code,
        )
        for row in money_growth_rows
    ]
    figure = go.Figure(
        data=[
            go.Scatter(
                x=[row["Years"] for row in money_growth_rows],
                y=[row["Balance"] for row in money_growth_rows],
                text=money_hover_values,
                mode="lines",
                line={"width": 2.5, "color": THEME_GREEN},
                fill="tozeroy",
                fillcolor="rgba(57, 211, 83, 0.10)",
                hovertemplate="Year %{x:.2f}<br>Balance %{text}<extra></extra>",
            )
        ]
    )
    figure.update_layout(
        title="Compound Growth Over Time",
        xaxis_title="Years",
        yaxis_title=f"Balance ({money_currency_symbol})",
        template="plotly_dark",
        paper_bgcolor=THEME_CARD,
        plot_bgcolor=THEME_BG,
        font={"color": THEME_TEXT_PRIMARY},
        margin={"l": 24, "r": 24, "t": 56, "b": 24},
    )
    return figure


# Colors and fill colors for multi-rate variance lines (dark green fintech palette)
_VARIANCE_LINE_STYLES = [
    {"color": "#F59E0B", "fill": "rgba(245, 158, 11, 0.10)"},   # lower rate — amber
    {"color": "#39D353", "fill": "rgba(57, 211, 83, 0.10)"},    # base rate  — neon green
    {"color": "#60A5FA", "fill": "rgba(96, 165, 250, 0.10)"},   # higher rate — soft blue
]


def build_multi_rate_growth_chart(
    rate_series: list[dict],
    money_currency_symbol: str,
    money_currency_code: str,
) -> go.Figure:
    """Build a compound growth chart with one line per interest rate scenario.

    Args:
        rate_series: list of dicts, each with keys:
            - ``label``: legend label, e.g. "5.00% (base)"
            - ``growth_rows``: list[dict[str, float]] from build_growth_series()
        money_currency_symbol: currency symbol for hover formatting
        money_currency_code: ISO currency code for formatting
    """
    traces = []
    for idx, series in enumerate(rate_series):
        style = _VARIANCE_LINE_STYLES[idx % len(_VARIANCE_LINE_STYLES)]
        hover_values = [
            format_money_value(row["Balance"], money_currency_symbol, money_currency_code)
            for row in series["growth_rows"]
        ]
        traces.append(
            go.Scatter(
                x=[row["Years"] for row in series["growth_rows"]],
                y=[row["Balance"] for row in series["growth_rows"]],
                name=series["label"],
                text=hover_values,
                mode="lines",
                line={"width": 3, "color": style["color"]},
                fill="tozeroy",
                fillcolor=style["fill"],
                hovertemplate=f"{series['label']}<br>Year %{{x:.2f}}<br>Balance %{{text}}<extra></extra>",
            )
        )

    figure = go.Figure(data=traces)
    figure.update_layout(
        title="Compound Growth Over Time — Interest Rate Variance",
        xaxis_title="Years",
        yaxis_title=f"Balance ({money_currency_symbol})",
        template="plotly_dark",
        paper_bgcolor=THEME_CARD,
        plot_bgcolor=THEME_BG,
        font={"color": THEME_TEXT_PRIMARY},
        legend={"title": "Rate Scenario"},
        margin={"l": 24, "r": 24, "t": 56, "b": 24},
    )
    return figure


def render_sidebar_inputs() -> tuple[
    float,
    float,
    float,
    float,
    int,
    str,
    str,
    str,
    float,
]:
    st.sidebar.header("Inputs")

    money_currency_options = {
        "INR (₹)": ("INR", "₹"),
        "USD ($)": ("USD", "$"),
        "EUR (€)": ("EUR", "€"),
        "GBP (£)": ("GBP", "£"),
        "JPY (¥)": ("JPY", "¥"),
    }
    selected_currency_label = st.sidebar.selectbox(
        "Currency",
        options=list(money_currency_options.keys()),
        index=0,
    )
    money_currency_code, money_currency_symbol = money_currency_options[
        selected_currency_label
    ]

    money_principal = st.sidebar.number_input(
        f"Principal Amount ({money_currency_symbol})",
        min_value=0.0,
        value=10000.0,
        step=500.0,
        key="money_principal_input",
    )
    money_monthly_contribution = st.sidebar.number_input(
        f"Monthly Contribution ({money_currency_symbol})",
        min_value=0.0,
        value=0.0,
        step=50.0,
        key="money_monthly_contribution_input",
    )
    annual_rate_percent = st.sidebar.number_input(
        "Annual Interest Rate (%)",
        min_value=0.0,
        value=5.0,
        step=0.25,
        key="annual_rate_percent_input",
    )
    time_years = st.sidebar.number_input(
        "Time (Years)",
        min_value=0.0,
        value=10.0,
        step=0.5,
        key="time_years_input",
    )

    # Streamlit number inputs can temporarily contain invalid typed text.
    # Clamp values to non-negative and sync UI state back to validated values.
    if money_principal < 0:
        money_principal = 0.0
        st.session_state["money_principal_input"] = 0.0

    if money_monthly_contribution < 0:
        money_monthly_contribution = 0.0
        st.session_state["money_monthly_contribution_input"] = 0.0

    if annual_rate_percent < 0:
        annual_rate_percent = 0.0
        st.session_state["annual_rate_percent_input"] = 0.0

    if time_years < 0:
        time_years = 0.0
        st.session_state["time_years_input"] = 0.0

    frequency_label = st.sidebar.selectbox(
        "Compounding Frequency",
        options=list(FREQUENCY_OPTIONS.keys()),
        index=3,
    )

    rate_variance_percent = st.sidebar.number_input(
        "Interest Rate Variance Range (%)",
        min_value=0.0,
        value=0.0,
        step=0.25,
        key="rate_variance_input",
        help="Optional: enter a variance to see growth for (rate − variance), base rate, and (rate + variance).",
    )

    return (
        money_principal,
        money_monthly_contribution,
        annual_rate_percent,
        time_years,
        FREQUENCY_OPTIONS[frequency_label],
        frequency_label,
        money_currency_code,
        money_currency_symbol,
        rate_variance_percent,
    )


def render_results(
    money_principal: float,
    money_monthly_contribution: float,
    annual_rate_percent: float,
    time_years: float,
    compounds_per_year: int,
    frequency_label: str,
    money_currency_code: str,
    money_currency_symbol: str,
    rate_variance_percent: float = 0.0,
) -> None:
    money_total_balance = calculate_compound_balance(
        money_principal,
        money_monthly_contribution,
        annual_rate_percent,
        time_years,
        compounds_per_year,
    )
    money_total_contributions = money_monthly_contribution * 12 * time_years
    money_interest_earned = (
        money_total_balance - money_principal - money_total_contributions
    )
    money_growth_rows = build_growth_series(
        money_principal,
        money_monthly_contribution,
        annual_rate_percent,
        time_years,
        compounds_per_year,
    )
    money_summary_rows = build_yearly_summary(
        money_principal,
        money_monthly_contribution,
        annual_rate_percent,
        time_years,
        compounds_per_year,
    )

    st.title("Compound Interest Calculator")
    st.caption(
        f"Projected using {frequency_label.lower()} compounding over {time_years:.2f} years in {money_currency_code}."
    )

    metric_column_1, metric_column_2, metric_column_3 = st.columns(3)
    metric_column_1.metric(
        "Future Value",
        format_money_value(
            money_total_balance,
            money_currency_symbol,
            money_currency_code,
        ),
    )
    metric_column_2.metric(
        "Total Contributions",
        format_money_value(
            money_total_contributions,
            money_currency_symbol,
            money_currency_code,
        ),
    )
    metric_column_3.metric(
        "Interest Earned",
        format_money_value(
            money_interest_earned,
            money_currency_symbol,
            money_currency_code,
        ),
    )

    # ── Chart ──────────────────────────────────────────────────────────────────
    if rate_variance_percent > 0:
        rate_lower = max(0.0, annual_rate_percent - rate_variance_percent)
        rate_upper = annual_rate_percent + rate_variance_percent
        rate_scenarios = [
            (rate_lower, f"{rate_lower:.2f}% (−{rate_variance_percent:.2f}%)"),
            (annual_rate_percent, f"{annual_rate_percent:.2f}% (base)"),
            (rate_upper, f"{rate_upper:.2f}% (+{rate_variance_percent:.2f}%)"),
        ]
        rate_series = [
            {
                "label": label,
                "growth_rows": build_growth_series(
                    money_principal,
                    money_monthly_contribution,
                    rate,
                    time_years,
                    compounds_per_year,
                ),
            }
            for rate, label in rate_scenarios
        ]
        st.plotly_chart(
            build_multi_rate_growth_chart(rate_series, money_currency_symbol, money_currency_code),
            use_container_width=True,
        )
    else:
        st.plotly_chart(
            build_growth_chart(
                money_growth_rows,
                money_currency_symbol,
                money_currency_code,
            ),
            use_container_width=True,
        )

    # ── Year-by-Year Summary ───────────────────────────────────────────────────
    st.subheader("Year-by-Year Balance")
    if rate_variance_percent > 0:
        rate_lower = max(0.0, annual_rate_percent - rate_variance_percent)
        rate_upper = annual_rate_percent + rate_variance_percent
        variance_rate_configs = [
            (rate_lower, f"Balance at {rate_lower:.2f}% ({money_currency_symbol})"),
            (annual_rate_percent, f"Balance at {annual_rate_percent:.2f}% ({money_currency_symbol})"),
            (rate_upper, f"Balance at {rate_upper:.2f}% ({money_currency_symbol})"),
        ]
        # Build the base summary rows using the base rate for period labels
        base_summary = build_yearly_summary(
            money_principal, money_monthly_contribution, annual_rate_percent, time_years, compounds_per_year
        )
        combined_rows = []
        for row in base_summary:
            combined_row: dict[str, str | float] = {"Period": row["Period"]}
            for rate, col_name in variance_rate_configs:
                balance = calculate_compound_balance(
                    money_principal, money_monthly_contribution, rate, row["Years"], compounds_per_year
                )
                combined_row[col_name] = format_money_value(balance, money_currency_symbol, money_currency_code)
            combined_rows.append(combined_row)
        st.dataframe(
            style_summary_dataframe(combined_rows, balance_columns=[]),
            use_container_width=True,
            hide_index=True,
        )
    else:
        money_balance_column = f"Balance ({money_currency_symbol})"
        numeric_rows = []
        for money_row in money_summary_rows:
            money_row[money_balance_column] = float(money_row.pop("Balance ($)"))
            numeric_rows.append(money_row)
        st.dataframe(
            style_summary_dataframe(numeric_rows, balance_columns=[money_balance_column]),
            use_container_width=True,
            hide_index=True,
        )


def main() -> None:
    st.set_page_config(page_title="Compound Interest Calculator", layout="wide")
    inject_app_styles()

    (
        money_principal,
        money_monthly_contribution,
        annual_rate_percent,
        time_years,
        compounds_per_year,
        frequency_label,
        money_currency_code,
        money_currency_symbol,
        rate_variance_percent,
    ) = render_sidebar_inputs()

    render_results(
        money_principal,
        money_monthly_contribution,
        annual_rate_percent,
        time_years,
        compounds_per_year,
        frequency_label,
        money_currency_code,
        money_currency_symbol,
        rate_variance_percent,
    )


if __name__ == "__main__":
    main()