from __future__ import annotations

from math import floor, isclose

import numpy  # noqa: F401
import pandas  # noqa: F401
import plotly.graph_objects as go
import streamlit as st


def get_plotly_template() -> str:
    """
    Return a Plotly template that follows the active Streamlit theme.
    """
    base_theme = st.get_option("theme.base")
    return "plotly_dark" if base_theme == "dark" else "plotly_white"


def calculate_compound_balance(
    money_principal: float,
    money_monthly_contribution: float,
    annual_rate_percent: float,
    time_years: float,
    compounds_per_year: int,
) -> float:
    rate_decimal = annual_rate_percent / 100
    total_periods = compounds_per_year * time_years
    if rate_decimal == 0:
        return money_principal + (money_monthly_contribution * time_years)

    periodic_rate = rate_decimal / compounds_per_year
    growth_multiplier = (1 + periodic_rate) ** total_periods
    return money_principal * growth_multiplier + money_monthly_contribution * (
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
                line={"width": 3, "color": "#1f6feb"},
                fill="tozeroy",
                fillcolor="rgba(31, 111, 235, 0.14)",
                hovertemplate="Year %{x:.2f}<br>Balance %{text}<extra></extra>",
            )
        ]
    )
    figure.update_layout(
        title="Compound Growth Over Time",
        xaxis_title="Years",
        yaxis_title=f"Balance ({money_currency_symbol})",
        template=get_plotly_template(),
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

    frequency_options = {
        "Annually": 1,
        "Quarterly": 4,
        "Monthly": 12,
        "Daily": 365,
    }
    frequency_label = st.sidebar.selectbox(
        "Compounding Frequency",
        options=list(frequency_options.keys()),
        index=2,
    )

    return (
        money_principal,
        money_monthly_contribution,
        annual_rate_percent,
        time_years,
        frequency_options[frequency_label],
        frequency_label,
        money_currency_code,
        money_currency_symbol,
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
) -> None:
    money_total_balance = calculate_compound_balance(
        money_principal,
        money_monthly_contribution,
        annual_rate_percent,
        time_years,
        compounds_per_year,
    )
    money_total_contributions = money_monthly_contribution * time_years
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

    st.plotly_chart(
        build_growth_chart(
            money_growth_rows,
            money_currency_symbol,
            money_currency_code,
        ),
        use_container_width=True,
    )

    st.subheader("Year-by-Year Balance")
    money_balance_column = f"Balance ({money_currency_symbol})"
    for money_row in money_summary_rows:
        money_row[money_balance_column] = format_money_value(
            float(money_row.pop("Balance ($)")),
            money_currency_symbol,
            money_currency_code,
        )
    st.dataframe(money_summary_rows, use_container_width=True, hide_index=True)


def main() -> None:
    st.set_page_config(page_title="Compound Interest Calculator", layout="wide")

    (
        money_principal,
        money_monthly_contribution,
        annual_rate_percent,
        time_years,
        compounds_per_year,
        frequency_label,
        money_currency_code,
        money_currency_symbol,
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
    )


if __name__ == "__main__":
    main()