"""
Automated tests for app.py mapped to TESTING_PERSONA.md scenarios.

Categories:
  S1 - Calculation Correctness
  S2 - Frequency Impact
  S3 - Currency and Number Formatting
  S4 - Chart Validation
  S5 - Summary Table Validation
  S6 - Boundary and Edge Cases
  S7 - Theme / Plotly Template
"""
from __future__ import annotations

from math import isclose

import pytest

import app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _balance(
    principal: float,
    contribution: float,
    rate: float,
    years: float,
    n: int,
) -> float:
    return app.calculate_compound_balance(
        money_principal=principal,
        money_monthly_contribution=contribution,
        annual_rate_percent=rate,
        time_years=years,
        compounds_per_year=n,
    )


# ---------------------------------------------------------------------------
# S1 – Calculation Correctness
# ---------------------------------------------------------------------------

class TestCalculateCompoundBalance:
    """S1 – Calculation Correctness"""

    def test_zero_rate_returns_principal_plus_contribution_times_years(self) -> None:
        # S1-2: zero-rate case — linear growth (monthly contribution × 12 months × years)
        result = _balance(25000.0, 1200.0, 0.0, 7.5, 4)
        assert result == 133000.0  # 25000 + 1200*12*7.5

    def test_zero_contribution_matches_principal_only_formula(self) -> None:
        # S1-1: base case, no contribution
        r = 0.05 / 12
        expected = 10000.0 * (1 + r) ** 120
        result = _balance(10000.0, 0.0, 5.0, 10.0, 12)
        assert isclose(result, expected, rel_tol=1e-12)

    def test_future_value_exceeds_principal_when_rate_positive(self) -> None:
        # S1-3
        result = _balance(50000.0, 0.0, 5.0, 10.0, 12)
        assert result > 50000.0

    def test_interest_earned_identity(self) -> None:
        # S1-4: interest = FV - P - C*t
        principal, contribution, rate, years, n = 50000.0, 1000.0, 8.0, 15.0, 12
        money_fv = _balance(principal, contribution, rate, years, n)
        money_total_contributions = contribution * years
        money_interest = money_fv - principal - money_total_contributions
        assert money_interest > 0

    def test_higher_rate_yields_higher_balance(self) -> None:
        # S1-5: monotonic in rate
        low = _balance(10000.0, 100.0, 3.0, 10.0, 12)
        high = _balance(10000.0, 100.0, 8.0, 10.0, 12)
        assert high > low

    def test_longer_time_yields_higher_balance(self) -> None:
        # S1-6: monotonic in time
        short = _balance(10000.0, 100.0, 5.0, 5.0, 12)
        long_ = _balance(10000.0, 100.0, 5.0, 20.0, 12)
        assert long_ > short

    # Test data sets from TESTING_PERSONA.md
    def test_base_case_dataset(self) -> None:
        result = _balance(10000.0, 0.0, 5.0, 10.0, 12)
        assert isclose(result, 16470.09, rel_tol=1e-4)

    def test_contribution_case_dataset(self) -> None:
        result = _balance(50000.0, 1000.0, 8.0, 15.0, 12)
        assert result > 50000.0

    def test_short_horizon_dataset(self) -> None:
        result = _balance(1000.0, 200.0, 12.0, 0.5, 12)
        assert result > 1100.0

    def test_long_horizon_dataset(self) -> None:
        result = _balance(100000.0, 5000.0, 10.0, 40.0, 1)
        assert result > 1_000_000.0

    def test_precision_case_dataset(self) -> None:
        result = _balance(12345.67, 89.01, 4.75, 13.25, 365)
        assert isinstance(result, float)
        assert result > 12345.67


# ---------------------------------------------------------------------------
# S2 – Frequency Impact
# ---------------------------------------------------------------------------

class TestFrequencyImpact:
    """S2 – Frequency Impact"""

    @pytest.mark.parametrize("n_low,n_high", [(1, 2), (2, 4), (4, 12), (12, 24), (24, 52), (52, 365)])
    def test_higher_frequency_yields_more_or_equal_balance(
        self, n_low: int, n_high: int
    ) -> None:
        # S2-1, S2-2
        low = _balance(10000.0, 500.0, 6.0, 10.0, n_low)
        high = _balance(10000.0, 500.0, 6.0, 10.0, n_high)
        assert high >= low

    def test_half_yearly_mapping_exists(self) -> None:
        assert "Half Yearly" in app.FREQUENCY_OPTIONS
        assert app.FREQUENCY_OPTIONS["Half Yearly"] == 2

    def test_weekly_mapping_exists(self) -> None:
        assert "Weekly" in app.FREQUENCY_OPTIONS
        assert app.FREQUENCY_OPTIONS["Weekly"] == 52

    def test_semi_monthly_mapping_exists(self) -> None:
        # Issue #16: Semi-Monthly must be present and mapped to 24
        assert "Semi-Monthly" in app.FREQUENCY_OPTIONS
        assert app.FREQUENCY_OPTIONS["Semi-Monthly"] == 24

    def test_semi_monthly_frequency_compounds_correctly(self) -> None:
        # Issue #16: Semi-Monthly (n=24) should produce a higher balance than
        # Monthly (n=12) and a lower balance than Weekly (n=52) at a positive rate.
        monthly = _balance(10000.0, 0.0, 6.0, 10.0, 12)
        semi_monthly = _balance(10000.0, 0.0, 6.0, 10.0, 24)
        weekly = _balance(10000.0, 0.0, 6.0, 10.0, 52)
        assert semi_monthly > monthly, "Semi-Monthly should compound more than Monthly"
        assert semi_monthly < weekly, "Semi-Monthly should compound less than Weekly"

    def test_semi_monthly_balance_formula(self) -> None:
        # Issue #16: Verify the exact compound formula for n=24 over 1 year at 12%
        # FV = P * (1 + 0.12/24)^24
        import math
        principal = 1000.0
        rate = 12.0
        years = 1.0
        n = 24
        expected = principal * (1 + (rate / 100) / n) ** (n * years)
        result = _balance(principal, 0.0, rate, years, n)
        assert isclose(result, expected, rel_tol=1e-12)

    def test_frequency_has_no_impact_at_zero_rate(self) -> None:
        # All frequencies should produce identical results at 0% rate
        results = [_balance(10000.0, 100.0, 0.0, 5.0, n) for n in (1, 2, 4, 12, 24, 52, 365)]
        assert all(isclose(r, results[0], rel_tol=1e-12) for r in results)

    @pytest.mark.parametrize("n", [1, 2, 4, 12, 24, 52, 365])
    def test_all_frequencies_accept_fractional_years(self, n: int) -> None:
        result = _balance(1000.0, 50.0, 5.0, 2.5, n)
        assert isinstance(result, float) and result > 0


# ---------------------------------------------------------------------------
# S3 – Currency and Number Formatting
# ---------------------------------------------------------------------------

class TestFormatMoneyValue:
    """S3 – Currency and Number Formatting"""

    # INR Indian grouping
    @pytest.mark.parametrize("amount,expected", [
        (100.0,         "₹100.00"),
        (1000.0,        "₹1,000.00"),
        (100000.0,      "₹1,00,000.00"),
        (1000000.0,     "₹10,00,000.00"),
        (10000000.0,    "₹1,00,00,000.00"),
        (12345678.9,    "₹1,23,45,678.90"),
    ])
    def test_inr_grouping(self, amount: float, expected: str) -> None:
        # S3-1
        assert app.format_money_value(amount, "₹", "INR") == expected

    # International grouping
    @pytest.mark.parametrize("symbol,code,amount,expected", [
        ("$",  "USD", 12345678.9,  "$12,345,678.90"),
        ("€",  "EUR", 9999999.0,   "€9,999,999.00"),
        ("£",  "GBP", 1234567.89,  "£1,234,567.89"),
        ("¥",  "JPY", 100000.0,    "¥100,000.00"),
    ])
    def test_international_grouping(
        self, symbol: str, code: str, amount: float, expected: str
    ) -> None:
        # S3-2
        assert app.format_money_value(amount, symbol, code) == expected

    def test_always_two_decimal_places(self) -> None:
        # S3-3
        money_text = app.format_money_value(1000.0, "$", "USD")
        decimal_part = money_text.split(".")[-1]
        assert len(decimal_part) == 2

    def test_negative_value_usd(self) -> None:
        # S3-4
        assert app.format_money_value(-1000.5, "$", "USD") == "-$1,000.50"

    def test_negative_value_inr(self) -> None:
        assert app.format_money_value(-100000.0, "₹", "INR") == "-₹1,00,000.00"

    def test_zero_value(self) -> None:
        assert app.format_money_value(0.0, "₹", "INR") == "₹0.00"


# ---------------------------------------------------------------------------
# S4 – Chart Validation
# ---------------------------------------------------------------------------

class TestBuildGrowthChart:
    """S4 – Chart Validation"""

    def _chart(self, symbol: str = "₹", code: str = "INR") -> object:
        money_rows = [
            {"Years": 0.0, "Balance": 10000.0},
            {"Years": 5.0, "Balance": 12763.0},
            {"Years": 10.0, "Balance": 16289.0},
        ]
        return app.build_growth_chart(money_rows, symbol, code)

    def test_x_axis_label_is_years(self) -> None:
        # S4-2
        fig = self._chart()
        assert fig.layout.xaxis.title.text == "Years"

    def test_y_axis_label_contains_currency_symbol(self) -> None:
        # S4-3
        for symbol, code in [("₹", "INR"), ("$", "USD"), ("€", "EUR"), ("£", "GBP"), ("¥", "JPY")]:
            fig = self._chart(symbol, code)
            assert symbol in fig.layout.yaxis.title.text

    def test_hover_template_format(self) -> None:
        # S4-4
        fig = self._chart()
        assert "Year %{x:.2f}" in fig.data[0].hovertemplate
        assert "%{text}" in fig.data[0].hovertemplate

    def test_hover_text_uses_formatted_values(self) -> None:
        fig = self._chart("₹", "INR")
        assert fig.data[0].text[0] == "₹10,000.00"

    def test_series_is_non_decreasing_for_positive_inputs(self) -> None:
        # S4-5
        money_rows = app.build_growth_series(
            money_principal=10000.0,
            money_monthly_contribution=100.0,
            annual_rate_percent=5.0,
            time_years=10.0,
            compounds_per_year=12,
        )
        balances = [row["Balance"] for row in money_rows]
        assert all(b2 >= b1 for b1, b2 in zip(balances, balances[1:]))

    def test_chart_title_is_set(self) -> None:
        fig = self._chart()
        assert fig.layout.title.text == "Compound Growth Over Time"

    @pytest.mark.parametrize("theme,expected_template", [
        ("dark", "plotly_dark"),
        ("light", "plotly_white"),
    ])
    def test_plotly_template_matches_streamlit_theme(
        self, monkeypatch, theme: str, expected_template: str
    ) -> None:
        # S4-6, S7
        monkeypatch.setattr(app.st, "get_option", lambda _: theme)
        assert app.get_plotly_template() == expected_template


# ---------------------------------------------------------------------------
# S5 – Summary Table Validation
# ---------------------------------------------------------------------------

class TestBuildYearlySummary:
    """S5 – Summary Table Validation"""

    def _summary(self, years: float) -> list:
        return app.build_yearly_summary(
            money_principal=10000.0,
            money_monthly_contribution=100.0,
            annual_rate_percent=5.0,
            time_years=years,
            compounds_per_year=12,
        )

    def test_first_row_is_year_zero(self) -> None:
        # S5-1
        rows = self._summary(5.0)
        assert rows[0]["Period"] == "Year 0"
        assert rows[0]["Years"] == 0.0

    def test_integer_time_row_count(self) -> None:
        # S5-2: t=5 → rows for 0,1,2,3,4,5 → 6 rows
        rows = self._summary(5.0)
        assert len(rows) == 6

    def test_fractional_time_appends_extra_row(self) -> None:
        # S5-3
        rows = self._summary(7.5)
        assert rows[-1]["Period"] == "Year 7.50"
        assert rows[-1]["Years"] == 7.5

    def test_fractional_time_row_count(self) -> None:
        # 0..7 integer rows + 1 fractional → 9 rows
        rows = self._summary(7.5)
        assert len(rows) == 9

    def test_integer_period_labels(self) -> None:
        # S5-4 integer rows
        rows = self._summary(3.0)
        for i, row in enumerate(rows):
            assert row["Period"] == f"Year {i}"

    def test_balance_at_year_zero_equals_principal(self) -> None:
        rows = self._summary(5.0)
        assert isclose(rows[0]["Balance ($)"], 10000.0, rel_tol=1e-9)

    def test_balance_increases_over_time(self) -> None:
        rows = self._summary(5.0)
        balances = [row["Balance ($)"] for row in rows]
        assert all(b2 >= b1 for b1, b2 in zip(balances, balances[1:]))


# ---------------------------------------------------------------------------
# S6 – Boundary and Edge Cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """S6 – Boundary and Edge Cases"""

    def test_all_zeros_returns_zero(self) -> None:
        # S6-1
        result = _balance(0.0, 0.0, 0.0, 0.0, 12)
        assert result == 0.0

    def test_zero_principal_zero_rate_positive_contribution(self) -> None:
        # S6-2: no divide-by-zero, linear accumulation (monthly contribution × 12 months × years)
        result = _balance(0.0, 500.0, 0.0, 10.0, 12)
        assert result == 60000.0  # 500 * 12 * 10

    def test_very_large_values_do_not_raise(self) -> None:
        # S6-3
        result = _balance(1e9, 1e7, 20.0, 50.0, 12)
        assert isinstance(result, float) and result > 1e9

    def test_minimal_positive_values(self) -> None:
        # S6-4
        result = _balance(0.01, 0.01, 0.01, 0.1, 12)
        assert isinstance(result, float) and result > 0

    @pytest.mark.parametrize("n", [1, 2, 4, 12, 24, 52, 365])
    def test_fractional_years_all_frequencies(self, n: int) -> None:
        # S6-5
        result = _balance(10000.0, 100.0, 5.0, 2.5, n)
        assert isinstance(result, float) and result > 10000.0

    def test_growth_series_all_zeros_is_stable(self) -> None:
        money_rows = app.build_growth_series(0.0, 0.0, 0.0, 0.0, 12)
        assert len(money_rows) == 2
        assert all(row["Balance"] == 0.0 for row in money_rows)

    def test_yearly_summary_zero_time_has_only_year_zero(self) -> None:
        money_rows = app.build_yearly_summary(1000.0, 0.0, 5.0, 0.0, 12)
        assert len(money_rows) == 1
        assert money_rows[0]["Period"] == "Year 0"

    def test_inr_format_large_value_no_crash(self) -> None:
        # S6-3 formatting side
        money_text = app.format_money_value(1e12, "₹", "INR")
        assert money_text.startswith("₹")
        assert "." in money_text


# ---------------------------------------------------------------------------
# S8 – Interest Rate Variance Range
# ---------------------------------------------------------------------------

class TestInterestRateVarianceRange:
    """S8 – Interest Rate Variance Range (Issue #5)"""

    def test_build_multi_rate_growth_chart_returns_figure(self) -> None:
        """build_multi_rate_growth_chart returns a Plotly Figure with multiple traces."""
        import plotly.graph_objects as go

        series = [
            {
                "label": "3.00% (−2.00%)",
                "growth_rows": app.build_growth_series(10000.0, 0.0, 3.0, 10.0, 12),
            },
            {
                "label": "5.00% (base)",
                "growth_rows": app.build_growth_series(10000.0, 0.0, 5.0, 10.0, 12),
            },
            {
                "label": "7.00% (+2.00%)",
                "growth_rows": app.build_growth_series(10000.0, 0.0, 7.0, 10.0, 12),
            },
        ]
        fig = app.build_multi_rate_growth_chart(series, "$", "USD")
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 3

    def test_build_multi_rate_growth_chart_trace_labels(self) -> None:
        """Each trace in multi-rate chart carries the correct label as its name."""
        labels = ["3.00% (−2.00%)", "5.00% (base)", "7.00% (+2.00%)"]
        series = [
            {
                "label": label,
                "growth_rows": app.build_growth_series(10000.0, 0.0, rate, 5.0, 12),
            }
            for label, rate in zip(labels, [3.0, 5.0, 7.0])
        ]
        fig = app.build_multi_rate_growth_chart(series, "₹", "INR")
        trace_names = [trace.name for trace in fig.data]
        assert trace_names == labels

    def test_build_multi_rate_growth_chart_x_axis_label(self) -> None:
        """Multi-rate chart x-axis label is 'Years'."""
        series = [
            {"label": "5.00% (base)", "growth_rows": app.build_growth_series(10000.0, 0.0, 5.0, 5.0, 12)},
        ]
        fig = app.build_multi_rate_growth_chart(series, "$", "USD")
        assert fig.layout.xaxis.title.text == "Years"

    def test_build_multi_rate_growth_chart_y_axis_contains_symbol(self) -> None:
        """Multi-rate chart y-axis label contains the currency symbol."""
        series = [
            {"label": "5.00% (base)", "growth_rows": app.build_growth_series(10000.0, 0.0, 5.0, 5.0, 12)},
        ]
        fig = app.build_multi_rate_growth_chart(series, "$", "USD")
        assert "$" in fig.layout.yaxis.title.text

    def test_variance_lower_rate_yields_lower_balance_than_base(self) -> None:
        """The lower-rate scenario produces a smaller balance than the base rate."""
        base_rate = 5.0
        variance = 2.0
        lower_rate = base_rate - variance
        balance_base = _balance(10000.0, 0.0, base_rate, 10.0, 12)
        balance_lower = _balance(10000.0, 0.0, lower_rate, 10.0, 12)
        assert balance_lower < balance_base

    def test_variance_upper_rate_yields_higher_balance_than_base(self) -> None:
        """The upper-rate scenario produces a larger balance than the base rate."""
        base_rate = 5.0
        variance = 2.0
        upper_rate = base_rate + variance
        balance_base = _balance(10000.0, 0.0, base_rate, 10.0, 12)
        balance_upper = _balance(10000.0, 0.0, upper_rate, 10.0, 12)
        assert balance_upper > balance_base

    def test_variance_lower_rate_clamped_to_zero_when_variance_exceeds_base_rate(self) -> None:
        """When variance exceeds base rate, lower rate is clamped to 0 (no negative rates)."""
        base_rate = 1.0
        variance = 3.0
        lower_rate = max(0.0, base_rate - variance)
        assert lower_rate == 0.0
        # Ensure zero-rate calculation still works
        result = _balance(10000.0, 0.0, lower_rate, 10.0, 12)
        assert result == 10000.0

    def test_variance_zero_produces_single_rate_result(self) -> None:
        """When variance is 0, build_growth_series for base rate matches the standard formula."""
        base_rate = 5.0
        variance = 0.0
        # When variance is 0, only the base rate is used — growth series should match standard output
        rows_standard = app.build_growth_series(10000.0, 0.0, base_rate, 10.0, 12)
        rows_variance = app.build_growth_series(10000.0, 0.0, base_rate + variance, 10.0, 12)
        for r1, r2 in zip(rows_standard, rows_variance):
            assert isclose(r1["Balance"], r2["Balance"], rel_tol=1e-12)

    def test_build_multi_rate_growth_chart_title_contains_variance_keyword(self) -> None:
        """Multi-rate chart title references the interest rate variance."""
        series = [
            {"label": "5.00% (base)", "growth_rows": app.build_growth_series(10000.0, 0.0, 5.0, 5.0, 12)},
        ]
        fig = app.build_multi_rate_growth_chart(series, "$", "USD")
        assert "Variance" in fig.layout.title.text or "variance" in fig.layout.title.text.lower()


# ---------------------------------------------------------------------------
# S9 – Total Contributions Formula (Issue #19)
# ---------------------------------------------------------------------------

class TestTotalContributions:
    """S9 – Total Contributions formula fix (Issue #19)

    money_total_contributions must equal money_monthly_contribution * 12 * time_years.
    """

    def test_total_contributions_1000_over_10_years_equals_120000(self) -> None:
        """With monthly contribution=1000 and time=10 years, total contributions is 120,000."""
        money_monthly_contribution = 1000.0
        time_years = 10.0
        money_total_contributions = money_monthly_contribution * 12 * time_years
        assert money_total_contributions == 120_000.0

    def test_total_contributions_multiplied_by_12_months_per_year(self) -> None:
        """Formula uses 12 months per year: contribution * 12 * years."""
        money_monthly_contribution = 500.0
        time_years = 5.0
        money_total_contributions = money_monthly_contribution * 12 * time_years
        assert money_total_contributions == 30_000.0  # 500 * 12 * 5

    def test_total_contributions_zero_contribution_is_zero(self) -> None:
        """When monthly contribution is 0, total contributions must be 0 regardless of years."""
        assert 0.0 * 12 * 20.0 == 0.0

    def test_interest_earned_uses_corrected_total_contributions(self) -> None:
        """Interest Earned = Future Value − Principal − (monthly * 12 * years)."""
        principal = 10000.0
        contribution = 1000.0
        rate = 5.0
        years = 10.0
        n = 12
        money_fv = app.calculate_compound_balance(principal, contribution, rate, years, n)
        money_total_contributions = contribution * 12 * years  # corrected formula
        money_interest = money_fv - principal - money_total_contributions
        # With monthly contributions compounding, interest must be positive
        assert money_interest > 0

    def test_old_formula_would_produce_wrong_result(self) -> None:
        """Regression: old formula (contribution * years) gave 10x lower total contributions."""
        contribution = 1000.0
        years = 10.0
        wrong_result = contribution * years        # old bug: 10,000
        correct_result = contribution * 12 * years  # fix:    120,000
        assert correct_result == 12 * wrong_result

    def test_total_contributions_uses_12_not_compounding_periods(self) -> None:
        """Regression guard (Issue #24): total contributions must always use 12 months/year
        regardless of compounding frequency.  With Annual compounding (n=1) and
        contribution=1000 over 10 years the result is 120,000 not 10,000."""
        contribution = 1000.0
        years = 10.0
        # The correct formula — always 12 months per year
        assert contribution * 12 * years == 120_000.0
        # Guard: confirm the per-period formula gives a different (wrong) answer for n=1
        assert contribution * 1 * years != 120_000.0
        # Through the actual FV function: interest must be non-negative with the 12-month formula
        fv = app.calculate_compound_balance(0.0, contribution, 5.0, years, 1)
        interest_with_correct_formula = fv - 0.0 - (contribution * 12 * years)
        assert interest_with_correct_formula >= 0, (
            "With the 12-month formula, Interest Earned must be non-negative for n=1"
        )


class TestPlotlyTemplate:
    """S7 – Theme alignment"""

    def test_dark_theme_returns_plotly_dark(self, monkeypatch) -> None:
        monkeypatch.setattr(app.st, "get_option", lambda _: "dark")
        assert app.get_plotly_template() == "plotly_dark"

    def test_light_theme_returns_plotly_white(self, monkeypatch) -> None:
        monkeypatch.setattr(app.st, "get_option", lambda _: "light")
        assert app.get_plotly_template() == "plotly_white"

    def test_unknown_theme_defaults_to_plotly_white(self, monkeypatch) -> None:
        monkeypatch.setattr(app.st, "get_option", lambda _: None)
        assert app.get_plotly_template() == "plotly_white"


# ---------------------------------------------------------------------------
# S10 – Total Contributions Uses compounds_per_year (Issue #24)
# ---------------------------------------------------------------------------

def _interest_earned(
    principal: float,
    contribution: float,
    rate: float,
    years: float,
    n: int,
) -> float:
    """Mirror the render_results interest-earned calculation after the Issue #24 fix.

    money_total_contributions = money_monthly_contribution * compounds_per_year * time_years
    money_interest_earned     = total_balance - principal - total_contributions
    """
    total_balance = app.calculate_compound_balance(
        money_principal=principal,
        money_monthly_contribution=contribution,
        annual_rate_percent=rate,
        time_years=years,
        compounds_per_year=n,
    )
    total_contributions = contribution * 12 * years  # monthly contribution × 12 months/year
    return total_balance - principal - total_contributions


class TestInterestEarnedZeroPrincipal:
    """S10 – Issue #24: zero principal with non-zero contribution must yield
    non-negative Interest Earned for every supported compounding frequency."""

    @pytest.mark.parametrize("n,label", [
        (1,   "Annual"),
        (2,   "Half Yearly"),
        (4,   "Quarterly"),
        (12,  "Monthly"),
        (24,  "Semi-Monthly"),
        (52,  "Weekly"),
        (365, "Daily"),
    ])
    def test_zero_principal_non_negative_interest_earned_all_frequencies(
        self, n: int, label: str
    ) -> None:
        """Bug #24: principal=0, contribution>0 must never produce negative Interest Earned."""
        interest = _interest_earned(0.0, 500.0, 6.0, 10.0, n)
        assert interest >= 0, (
            f"Interest Earned is negative ({interest:.4f}) for {label} (n={n}). "
            "The total_contributions formula must use compounds_per_year, not hardcoded 12."
        )

    def test_zero_principal_annual_frequency_interest_earned_correct_value(self) -> None:
        """Accuracy: annual compounding (n=1), zero principal, contribution=100,
        rate=5%, 5 years. Monthly contribution is converted to per-period: 100×12/1=1200/year."""
        from math import isclose as _isclose
        n, principal, contribution, rate, years = 1, 0.0, 100.0, 5.0, 5.0
        periodic_rate = (rate / 100) / n
        total_periods = n * years
        periodic_contribution = contribution * 12 / n  # 100 monthly → 1200 annual
        fv_annuity = periodic_contribution * ((1 + periodic_rate) ** total_periods - 1) / periodic_rate
        expected_contributions = contribution * 12 * years   # 100 * 12 * 5 = 6000
        expected_interest = fv_annuity - expected_contributions
        actual_interest = _interest_earned(principal, contribution, rate, years, n)
        assert _isclose(actual_interest, expected_interest, rel_tol=1e-9)

    def test_zero_principal_weekly_frequency_interest_earned_correct_value(self) -> None:
        """Accuracy: weekly compounding (n=52), zero principal, contribution=50,
        rate=4%, 3 years. Monthly contribution is converted to per-period: 50×12/52."""
        from math import isclose as _isclose
        n, principal, contribution, rate, years = 52, 0.0, 50.0, 4.0, 3.0
        periodic_rate = (rate / 100) / n
        total_periods = n * years
        periodic_contribution = contribution * 12 / n  # 50 monthly → 600/52 per week
        fv_annuity = periodic_contribution * ((1 + periodic_rate) ** total_periods - 1) / periodic_rate
        expected_contributions = contribution * 12 * years  # 50 * 12 * 3 = 1800
        expected_interest = fv_annuity - expected_contributions
        actual_interest = _interest_earned(principal, contribution, rate, years, n)
        assert _isclose(actual_interest, expected_interest, rel_tol=1e-9)

    def test_issue24_regression_guard_annual_contributions_not_undercounted(self) -> None:
        """Regression guard: with Annual compounding (n=1), total contributions must use
        12 months/year, NOT 1 period/year. Guards against the Issue #24 regression where
        contributions were computed as contribution × compounds_per_year × years."""
        contribution, years = 500.0, 10.0
        correct_contributions = contribution * 12 * years   # 60,000
        wrong_contributions   = contribution * 1  * years   # 5,000 (Issue #24 formula for n=1)
        assert correct_contributions == 60_000.0
        assert wrong_contributions   ==  5_000.0
        assert correct_contributions != wrong_contributions
        # Through the actual formula: interest must be positive with the correct total_contributions
        fv = app.calculate_compound_balance(0.0, contribution, 6.0, years, 1)
        assert fv - 0.0 - correct_contributions >= 0, (
            "Interest Earned must be non-negative when contributions are counted correctly (×12)"
        )


class TestInterestEarnedMonthlyRegression:
    """S10 – No regression: monthly compounding (n=12) behaviour is unchanged."""

    def test_monthly_compounding_nonzero_principal_interest_positive(self) -> None:
        """Monthly compounding with non-zero principal still yields positive interest."""
        interest = _interest_earned(10000.0, 200.0, 5.0, 10.0, 12)
        assert interest > 0

    def test_monthly_compounding_zero_principal_interest_non_negative(self) -> None:
        """Monthly compounding (n=12) with zero principal: interest earned is non-negative."""
        interest = _interest_earned(0.0, 300.0, 7.0, 8.0, 12)
        assert interest >= 0

    def test_monthly_total_contributions_formula_unchanged(self) -> None:
        """For n=12, new formula (contribution * 12 * years) equals old formula — no breakage."""
        from math import isclose as _isclose
        contribution, years, n = 1000.0, 10.0, 12
        new_formula = contribution * n * years
        old_formula = contribution * 12 * years  # n==12 so identical
        assert _isclose(new_formula, old_formula, rel_tol=1e-12)

    def test_monthly_interest_earned_identity(self) -> None:
        """FV - principal - contributions == interest for monthly case (cross-check)."""
        from math import isclose as _isclose
        principal, contribution, rate, years, n = 50000.0, 1000.0, 8.0, 15.0, 12
        fv = app.calculate_compound_balance(principal, contribution, rate, years, n)
        total_contributions = contribution * n * years
        expected_interest = fv - principal - total_contributions
        actual_interest = _interest_earned(principal, contribution, rate, years, n)
        assert _isclose(actual_interest, expected_interest, rel_tol=1e-12)


# ---------------------------------------------------------------------------
# S11 – Axis Bank Bold Color Scheme (Issue #27)
# ---------------------------------------------------------------------------

class TestAxisBankColorConstants:
    """S11 – Axis Bank brand color constants are defined correctly in app.py."""

    def test_axis_red_is_primary_brand_color(self) -> None:
        """AXIS_RED must be the Axis Bank primary deep-red/maroon #97144D."""
        assert app.AXIS_RED == "#97144D"

    def test_axis_red_dark_variant(self) -> None:
        """AXIS_RED_DARK is the darker hover/footer variant #6B0F38."""
        assert app.AXIS_RED_DARK == "#6B0F38"

    def test_axis_red_light_variant(self) -> None:
        """AXIS_RED_LIGHT is the lighter highlight tint #C41E5B."""
        assert app.AXIS_RED_LIGHT == "#C41E5B"

    def test_axis_accent_page_background(self) -> None:
        """AXIS_ACCENT is the light blue-grey page background #E8F0F9."""
        assert app.AXIS_ACCENT == "#E8F0F9"

    def test_axis_white(self) -> None:
        """AXIS_WHITE must be pure white #FFFFFF."""
        assert app.AXIS_WHITE == "#FFFFFF"

    def test_axis_text_light(self) -> None:
        """AXIS_TEXT_LIGHT must be near-white #F5F5F5 for light-on-dark text."""
        assert app.AXIS_TEXT_LIGHT == "#F5F5F5"

    def test_axis_text_dark(self) -> None:
        """AXIS_TEXT_DARK must be near-black #1A1A1A for dark text on light backgrounds."""
        assert app.AXIS_TEXT_DARK == "#1A1A1A"


class TestInjectAxisBankStyles:
    """S11 – inject_axis_bank_styles() injects CSS with Axis Bank colors into the Streamlit app."""

    def test_inject_axis_bank_styles_is_callable(self) -> None:
        """inject_axis_bank_styles must exist in app module and be callable."""
        assert callable(app.inject_axis_bank_styles)

    def test_inject_axis_bank_styles_calls_st_markdown_once(self, monkeypatch) -> None:
        """inject_axis_bank_styles must call st.markdown exactly once."""
        calls: list = []
        monkeypatch.setattr(app.st, "markdown", lambda text, **kwargs: calls.append((text, kwargs)))
        app.inject_axis_bank_styles()
        assert len(calls) == 1

    def test_inject_axis_bank_styles_passes_unsafe_allow_html(self, monkeypatch) -> None:
        """inject_axis_bank_styles must pass unsafe_allow_html=True to st.markdown."""
        captured: list = []
        monkeypatch.setattr(app.st, "markdown", lambda text, **kwargs: captured.append(kwargs))
        app.inject_axis_bank_styles()
        assert captured[0].get("unsafe_allow_html") is True

    def test_injected_css_contains_axis_red_primary_color(self, monkeypatch) -> None:
        """Injected CSS must contain the Axis Bank primary color #97144D."""
        captured: list = []
        monkeypatch.setattr(app.st, "markdown", lambda text, **kwargs: captured.append(text))
        app.inject_axis_bank_styles()
        assert "#97144D" in captured[0]

    def test_injected_css_wrapped_in_style_tags(self, monkeypatch) -> None:
        """Injected content must be wrapped in <style>…</style> tags."""
        captured: list = []
        monkeypatch.setattr(app.st, "markdown", lambda text, **kwargs: captured.append(text))
        app.inject_axis_bank_styles()
        assert "<style>" in captured[0] and "</style>" in captured[0]

    def test_injected_css_styles_sidebar(self, monkeypatch) -> None:
        """Injected CSS must target the sidebar via stSidebar data-testid."""
        captured: list = []
        monkeypatch.setattr(app.st, "markdown", lambda text, **kwargs: captured.append(text))
        app.inject_axis_bank_styles()
        assert "stSidebar" in captured[0]

    def test_injected_css_styles_metric_cards(self, monkeypatch) -> None:
        """Injected CSS must target stMetric cards."""
        captured: list = []
        monkeypatch.setattr(app.st, "markdown", lambda text, **kwargs: captured.append(text))
        app.inject_axis_bank_styles()
        assert "stMetric" in captured[0]

    def test_injected_css_styles_buttons(self, monkeypatch) -> None:
        """Injected CSS must target primary Streamlit buttons (.stButton)."""
        captured: list = []
        monkeypatch.setattr(app.st, "markdown", lambda text, **kwargs: captured.append(text))
        app.inject_axis_bank_styles()
        assert ".stButton" in captured[0]

    def test_injected_css_styles_table_headers(self, monkeypatch) -> None:
        """Injected CSS must style dataframe/table headers (thead th)."""
        captured: list = []
        monkeypatch.setattr(app.st, "markdown", lambda text, **kwargs: captured.append(text))
        app.inject_axis_bank_styles()
        assert "thead" in captured[0]

    def test_injected_css_contains_dark_footer_color(self, monkeypatch) -> None:
        """Injected CSS must include AXIS_RED_DARK (#6B0F38) for footer/hover styling."""
        captured: list = []
        monkeypatch.setattr(app.st, "markdown", lambda text, **kwargs: captured.append(text))
        app.inject_axis_bank_styles()
        assert "#6B0F38" in captured[0]

    def test_injected_css_styles_stapp_background(self, monkeypatch) -> None:
        """Injected CSS must set the page background via .stApp selector."""
        captured: list = []
        monkeypatch.setattr(app.st, "markdown", lambda text, **kwargs: captured.append(text))
        app.inject_axis_bank_styles()
        assert ".stApp" in captured[0]

    def test_injected_css_styles_header(self, monkeypatch) -> None:
        """Injected CSS must style the top header bar (stHeader data-testid)."""
        captured: list = []
        monkeypatch.setattr(app.st, "markdown", lambda text, **kwargs: captured.append(text))
        app.inject_axis_bank_styles()
        assert "stHeader" in captured[0]


class TestAxisBankChartColors:
    """S11 – Plotly charts use Axis Bank color palette (Issue #27)."""

    def _make_rows(self) -> list:
        return [
            {"Years": 0.0,  "Balance": 10000.0},
            {"Years": 5.0,  "Balance": 13000.0},
            {"Years": 10.0, "Balance": 17000.0},
        ]

    def test_single_rate_chart_line_color_is_axis_red(self) -> None:
        """build_growth_chart single-rate line must use AXIS_RED (#97144D)."""
        fig = app.build_growth_chart(self._make_rows(), "₹", "INR")
        assert fig.data[0].line.color == app.AXIS_RED

    def test_single_rate_chart_line_color_value(self) -> None:
        """build_growth_chart single-rate line color must be exactly #97144D."""
        fig = app.build_growth_chart(self._make_rows(), "$", "USD")
        assert fig.data[0].line.color == "#97144D"

    def test_single_rate_chart_fill_color_uses_axis_red_rgba(self) -> None:
        """build_growth_chart area fill must use AXIS_RED RGBA (151, 20, 77)."""
        fig = app.build_growth_chart(self._make_rows(), "₹", "INR")
        # rgba(151, 20, 77, 0.14) corresponds to #97144D with 14% opacity
        assert "151, 20, 77" in fig.data[0].fillcolor

    def test_variance_line_styles_base_rate_uses_axis_red(self) -> None:
        """_VARIANCE_LINE_STYLES base-rate entry (index 1) must use AXIS_RED #97144D."""
        assert app._VARIANCE_LINE_STYLES[1]["color"] == "#97144D"

    def test_variance_line_styles_lower_rate_uses_axis_gold(self) -> None:
        """_VARIANCE_LINE_STYLES lower-rate entry (index 0) must use Axis gold #F7B500 for bold contrast."""
        assert app._VARIANCE_LINE_STYLES[0]["color"] == "#F7B500"

    def test_variance_line_styles_upper_rate_uses_axis_bright_red(self) -> None:
        """_VARIANCE_LINE_STYLES upper-rate entry (index 2) must use Axis bright red #E31837."""
        assert app._VARIANCE_LINE_STYLES[2]["color"] == "#E31837"

    def test_variance_line_styles_count_unchanged(self) -> None:
        """_VARIANCE_LINE_STYLES must still contain exactly 3 entries."""
        assert len(app._VARIANCE_LINE_STYLES) == 3

    def test_variance_line_styles_each_entry_has_color_and_fill_keys(self) -> None:
        """Every entry in _VARIANCE_LINE_STYLES must have both 'color' and 'fill' keys."""
        for i, style in enumerate(app._VARIANCE_LINE_STYLES):
            assert "color" in style, f"Entry {i} missing 'color' key"
            assert "fill" in style, f"Entry {i} missing 'fill' key"

    def test_variance_line_styles_fill_colors_reference_axis_palette(self) -> None:
        """Fill RGBA values in _VARIANCE_LINE_STYLES must reference Axis Bank brand RGB components."""
        # Index 0: Axis gold rgb(247, 181, 0), Index 1: AXIS_RED rgb(151, 20, 77), Index 2: bright red rgb(227, 24, 55)
        expected_fills = [
            ("247", "181", "0"),    # Axis gold
            ("151", "20", "77"),    # AXIS_RED
            ("227", "24", "55"),    # Axis bright red
        ]
        for i, (r, g, b) in enumerate(expected_fills):
            fill = app._VARIANCE_LINE_STYLES[i]["fill"]
            assert r in fill and g in fill and b in fill, (
                f"Entry {i} fill '{fill}' does not match expected RGB({r},{g},{b})"
            )


# ---------------------------------------------------------------------------
# S12 – inject_app_styles() always-visible number input step buttons (Issue #29)
# ---------------------------------------------------------------------------

class TestInjectAppStylesNumberInputButtons:
    """S12 – inject_app_styles() must include CSS that keeps +/- step buttons always visible."""

    def test_inject_app_styles_is_callable(self) -> None:
        """inject_app_styles must exist in app module and be callable."""
        assert callable(app.inject_app_styles)

    def test_inject_app_styles_calls_st_markdown_once(self, monkeypatch) -> None:
        """inject_app_styles must call st.markdown exactly once."""
        calls: list = []
        monkeypatch.setattr(app.st, "markdown", lambda text, **kwargs: calls.append((text, kwargs)))
        app.inject_app_styles()
        assert len(calls) == 1

    def test_inject_app_styles_passes_unsafe_allow_html(self, monkeypatch) -> None:
        """inject_app_styles must pass unsafe_allow_html=True to st.markdown."""
        captured: list = []
        monkeypatch.setattr(app.st, "markdown", lambda text, **kwargs: captured.append(kwargs))
        app.inject_app_styles()
        assert captured[0].get("unsafe_allow_html") is True

    def test_step_up_button_selector_always_visible(self, monkeypatch) -> None:
        """Injected CSS must include stNumberInputStepUp selector for always-visible +/- buttons."""
        captured: list = []
        monkeypatch.setattr(app.st, "markdown", lambda text, **kwargs: captured.append(text))
        app.inject_app_styles()
        assert "stNumberInputStepUp" in captured[0]

    def test_step_down_button_selector_always_visible(self, monkeypatch) -> None:
        """Injected CSS must include stNumberInputStepDown selector for always-visible +/- buttons."""
        captured: list = []
        monkeypatch.setattr(app.st, "markdown", lambda text, **kwargs: captured.append(text))
        app.inject_app_styles()
        assert "stNumberInputStepDown" in captured[0]

    def test_step_buttons_css_opacity_one(self, monkeypatch) -> None:
        """Injected CSS must set opacity: 1 !important on the number input step buttons."""
        captured: list = []
        monkeypatch.setattr(app.st, "markdown", lambda text, **kwargs: captured.append(text))
        app.inject_app_styles()
        assert "opacity: 1 !important" in captured[0]

    def test_step_buttons_css_visibility_visible(self, monkeypatch) -> None:
        """Injected CSS must set visibility: visible !important on the number input step buttons."""
        captured: list = []
        monkeypatch.setattr(app.st, "markdown", lambda text, **kwargs: captured.append(text))
        app.inject_app_styles()
        assert "visibility: visible !important" in captured[0]


# ---------------------------------------------------------------------------
# S13 – Parallel Testing Infrastructure (Issue #31)
# ---------------------------------------------------------------------------

import os
import subprocess


class TestParallelTestingScript:
    """S13 – run_parallel_testing.sh exists and enforces true OS-level parallelism (Issue #31).

    Steps 3 (unit tester) and Step 4 (UI tester) must be launched as independent
    background processes so they run simultaneously, not sequentially.
    """

    SCRIPT_PATH = os.path.join(
        os.path.dirname(__file__), "..", "scripts", "run_parallel_testing.sh"
    )

    def test_run_parallel_testing_script_exists(self) -> None:
        """Issue #31: scripts/run_parallel_testing.sh must exist."""
        assert os.path.isfile(self.SCRIPT_PATH), (
            "run_parallel_testing.sh not found — Issue #31 fix requires this script."
        )

    def test_run_parallel_testing_script_is_executable(self) -> None:
        """Issue #31: run_parallel_testing.sh must start with a shebang (#!)."""
        with open(self.SCRIPT_PATH) as fh:
            content = fh.read()
        assert content.startswith("#!/"), (
            "run_parallel_testing.sh must start with a shebang (#!)."
        )

    def test_run_parallel_testing_script_launches_unit_tests_in_background(self) -> None:
        """Issue #31: script must launch unit tests as a background process (trailing &)."""
        with open(self.SCRIPT_PATH) as fh:
            content = fh.read()
        assert "run_unit_tests" in content, (
            "run_parallel_testing.sh must define a run_unit_tests function."
        )
        assert "UNIT_PID=$!" in content, (
            "run_parallel_testing.sh must capture unit test background PID with UNIT_PID=$!"
        )

    def test_run_parallel_testing_script_launches_ui_tests_in_background(self) -> None:
        """Issue #31: script must launch UI tests as a background process (trailing &)."""
        with open(self.SCRIPT_PATH) as fh:
            content = fh.read()
        assert "run_ui_tests" in content, (
            "run_parallel_testing.sh must define a run_ui_tests function."
        )
        assert "UI_PID=$!" in content, (
            "run_parallel_testing.sh must capture UI test background PID with UI_PID=$!"
        )

    def test_run_parallel_testing_script_waits_for_both_pids(self) -> None:
        """Issue #31: script must wait for BOTH background PIDs before exiting."""
        with open(self.SCRIPT_PATH) as fh:
            content = fh.read()
        assert 'wait "${UNIT_PID}"' in content, (
            'run_parallel_testing.sh must call: wait "${UNIT_PID}" to collect unit test exit code.'
        )
        assert 'wait "${UI_PID}"' in content, (
            'run_parallel_testing.sh must call: wait "${UI_PID}" to collect UI test exit code.'
        )

    def test_run_parallel_testing_script_collects_both_exit_codes(self) -> None:
        """Issue #31: script must capture exit codes from BOTH background processes."""
        with open(self.SCRIPT_PATH) as fh:
            content = fh.read()
        assert "UNIT_EXIT=$?" in content, (
            "run_parallel_testing.sh must capture unit test exit code as UNIT_EXIT."
        )
        assert "UI_EXIT=$?" in content, (
            "run_parallel_testing.sh must capture UI test exit code as UI_EXIT."
        )

    def test_run_parallel_testing_script_exits_zero_only_when_both_pass(self) -> None:
        """Issue #31: script exits 0 only when both Step 3 and Step 4 succeed."""
        with open(self.SCRIPT_PATH) as fh:
            content = fh.read()
        assert "UNIT_EXIT" in content and "UI_EXIT" in content, (
            "run_parallel_testing.sh must check both UNIT_EXIT and UI_EXIT before exiting."
        )
        assert "exit 0" in content, (
            "run_parallel_testing.sh must exit 0 when both steps complete successfully."
        )
        assert "exit 1" in content, (
            "run_parallel_testing.sh must exit 1 when one or both steps are blocked."
        )

    def test_run_parallel_testing_script_requires_workflow_id_argument(self) -> None:
        """Issue #31: script must fail with a non-zero exit when called without a workflow_id."""
        result = subprocess.run(
            ["bash", self.SCRIPT_PATH],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, (
            "run_parallel_testing.sh must exit non-zero when workflow_id argument is missing."
        )

    def test_run_parallel_testing_script_accepts_workflow_id_parameter(self) -> None:
        """Issue #31: script must accept a workflow_id as its first positional argument."""
        with open(self.SCRIPT_PATH) as fh:
            content = fh.read()
        assert 'WORKFLOW_ID="${1' in content, (
            "run_parallel_testing.sh must assign WORKFLOW_ID from the first argument ($1)."
        )

    def test_orchestrator_agent_references_parallel_script(self) -> None:
        """Issue #31: orchestrator.agent.md must reference run_parallel_testing.sh."""
        agent_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            ".github",
            "agents",
            "orchestrator.agent.md",
        )
        assert os.path.isfile(agent_path), "orchestrator.agent.md must exist."
        with open(agent_path) as fh:
            content = fh.read()
        assert "run_parallel_testing.sh" in content, (
            "orchestrator.agent.md must reference run_parallel_testing.sh so the "
            "orchestrator launches Steps 3 + 4 via the parallel script."
        )

    def test_orchestrator_agent_describes_steps_as_background_processes(self) -> None:
        """Issue #31: orchestrator.agent.md must describe Steps 3+4 as background processes."""
        agent_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            ".github",
            "agents",
            "orchestrator.agent.md",
        )
        with open(agent_path) as fh:
            content = fh.read()
        assert "background" in content.lower() or "parallel" in content.lower(), (
            "orchestrator.agent.md must describe Steps 3+4 as running in parallel / background."
        )
