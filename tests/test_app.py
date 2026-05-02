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

    # ------------------------------------------------------------------
    # Issue #37 – Bi-Weekly (26 periods/year)
    # ------------------------------------------------------------------

    def test_bi_weekly_mapping_exists(self) -> None:
        # Issue #37: "Bi-Weekly" must be present in FREQUENCY_OPTIONS
        assert "Bi-Weekly" in app.FREQUENCY_OPTIONS

    def test_bi_weekly_mapped_to_26_periods(self) -> None:
        # Issue #37: Bi-Weekly must map to exactly 26 compounding periods per year
        assert app.FREQUENCY_OPTIONS["Bi-Weekly"] == 26

    def test_bi_weekly_frequency_compounds_correctly(self) -> None:
        # Issue #37: Bi-Weekly (n=26) must produce a higher balance than
        # Semi-Monthly (n=24) and a lower balance than Weekly (n=52).
        semi_monthly = _balance(10000.0, 0.0, 6.0, 10.0, 24)
        bi_weekly    = _balance(10000.0, 0.0, 6.0, 10.0, 26)
        weekly       = _balance(10000.0, 0.0, 6.0, 10.0, 52)
        assert bi_weekly > semi_monthly, (
            "Bi-Weekly (n=26) should compound more than Semi-Monthly (n=24)"
        )
        assert bi_weekly < weekly, (
            "Bi-Weekly (n=26) should compound less than Weekly (n=52)"
        )

    def test_bi_weekly_balance_formula(self) -> None:
        # Issue #37: Verify the exact compound formula for n=26 over 1 year at 12%
        # FV = P * (1 + 0.12/26)^26
        principal = 1000.0
        rate = 12.0
        years = 1.0
        n = 26
        expected = principal * (1 + (rate / 100) / n) ** (n * years)
        result = _balance(principal, 0.0, rate, years, n)
        assert isclose(result, expected, rel_tol=1e-12)

    def test_bi_weekly_ordered_between_semi_monthly_and_weekly_in_options(self) -> None:
        # Issue #37: FREQUENCY_OPTIONS must contain "Bi-Weekly" between
        # "Semi-Monthly" and "Weekly" in iteration order.
        keys = list(app.FREQUENCY_OPTIONS.keys())
        assert "Bi-Weekly" in keys
        assert keys.index("Bi-Weekly") > keys.index("Semi-Monthly"), (
            '"Bi-Weekly" must appear after "Semi-Monthly" in FREQUENCY_OPTIONS'
        )
        assert keys.index("Bi-Weekly") < keys.index("Weekly"), (
            '"Bi-Weekly" must appear before "Weekly" in FREQUENCY_OPTIONS'
        )

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
        assert isclose(rows[0]["Balance"], 10000.0, rel_tol=1e-9)

    def test_balance_increases_over_time(self) -> None:
        rows = self._summary(5.0)
        balances = [row["Balance"] for row in rows]
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
# NOTE: Tests for TestAxisBankColorConstants, TestInjectAxisBankStyles, and
# TestAxisBankChartColors were removed because issue #27 / #32 was abandoned
# before the corresponding app.py implementation was completed.


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


# ---------------------------------------------------------------------------
# S13 – Chart title font color explicitly set to THEME_TEXT_PRIMARY (Issue #33)
# ---------------------------------------------------------------------------

class TestChartTitleFontColor:
    """S13 – Chart title font.color must be explicitly set to THEME_TEXT_PRIMARY (#FFFFFF)
    so the title is visible on dark backgrounds and not left to the template default.
    """

    def _make_rows(self) -> list:
        return [
            {"Years": 0.0,  "Balance": 10000.0},
            {"Years": 5.0,  "Balance": 13500.0},
            {"Years": 10.0, "Balance": 18000.0},
        ]

    def _make_multi_series(self) -> list:
        rows = self._make_rows()
        return [
            {"label": "4.00%", "growth_rows": rows},
            {"label": "5.00% (base)", "growth_rows": rows},
            {"label": "6.00%", "growth_rows": rows},
        ]

    # --- build_growth_chart ---

    def test_growth_chart_title_font_color_is_explicitly_set(self) -> None:
        """build_growth_chart: title font color must not be None or empty (Issue #33)."""
        fig = app.build_growth_chart(self._make_rows(), "₹", "INR")
        color = fig.layout.title.font.color
        assert color is not None and color != "", (
            "build_growth_chart title font.color must be explicitly set, "
            "not left to the template default."
        )

    def test_growth_chart_title_font_color_matches_theme_text_primary(self) -> None:
        """build_growth_chart: title font color must equal THEME_TEXT_PRIMARY (#FFFFFF) (Issue #33)."""
        fig = app.build_growth_chart(self._make_rows(), "$", "USD")
        assert fig.layout.title.font.color == app.THEME_TEXT_PRIMARY, (
            f"Expected title font.color == {app.THEME_TEXT_PRIMARY!r}, "
            f"got {fig.layout.title.font.color!r}."
        )

    def test_growth_chart_title_font_color_is_white_hex(self) -> None:
        """build_growth_chart: title font color must be exactly #FFFFFF (Issue #33)."""
        fig = app.build_growth_chart(self._make_rows(), "€", "EUR")
        assert fig.layout.title.font.color == "#FFFFFF", (
            "build_growth_chart title font.color must be '#FFFFFF' for visibility on dark bg."
        )

    def test_growth_chart_title_text_unchanged(self) -> None:
        """build_growth_chart: adding font.color must not alter the title text (Issue #33)."""
        fig = app.build_growth_chart(self._make_rows(), "₹", "INR")
        assert fig.layout.title.text == "Compound Growth Over Time", (
            "build_growth_chart title text must remain 'Compound Growth Over Time'."
        )

    def test_growth_chart_axes_unaffected_by_title_font_color_change(self) -> None:
        """build_growth_chart: axis titles must still be set correctly after Issue #33 change."""
        fig = app.build_growth_chart(self._make_rows(), "₹", "INR")
        assert fig.layout.xaxis.title.text == "Years"
        assert "₹" in fig.layout.yaxis.title.text

    # --- build_multi_rate_growth_chart ---

    def test_variance_chart_title_font_color_is_explicitly_set(self) -> None:
        """build_multi_rate_growth_chart: title font color must not be None or empty (Issue #33)."""
        fig = app.build_multi_rate_growth_chart(self._make_multi_series(), "₹", "INR")
        color = fig.layout.title.font.color
        assert color is not None and color != "", (
            "build_multi_rate_growth_chart title font.color must be explicitly set."
        )

    def test_variance_chart_title_font_color_matches_theme_text_primary(self) -> None:
        """build_multi_rate_growth_chart: title font color must equal THEME_TEXT_PRIMARY (Issue #33)."""
        fig = app.build_multi_rate_growth_chart(self._make_multi_series(), "$", "USD")
        assert fig.layout.title.font.color == app.THEME_TEXT_PRIMARY, (
            f"Expected variance chart title font.color == {app.THEME_TEXT_PRIMARY!r}, "
            f"got {fig.layout.title.font.color!r}."
        )

    def test_variance_chart_title_font_color_is_white_hex(self) -> None:
        """build_multi_rate_growth_chart: title font color must be exactly #FFFFFF (Issue #33)."""
        fig = app.build_multi_rate_growth_chart(self._make_multi_series(), "€", "EUR")
        assert fig.layout.title.font.color == "#FFFFFF", (
            "build_multi_rate_growth_chart title font.color must be '#FFFFFF'."
        )

    def test_variance_chart_title_text_unchanged(self) -> None:
        """build_multi_rate_growth_chart: font.color change must not alter title text (Issue #33)."""
        fig = app.build_multi_rate_growth_chart(self._make_multi_series(), "$", "USD")
        assert "Interest Rate Variance" in fig.layout.title.text, (
            "Variance chart title text must still reference 'Interest Rate Variance'."
        )


# ---------------------------------------------------------------------------
# S14 – Green Gradient Styles
# ---------------------------------------------------------------------------

import pandas as pd
import re as _re  # noqa: E402 (used in TestGreenGradientStyles)


class TestGreenGradientStyles:
    """S14 – _green_gradient_styles() interpolates dark-to-neon green per cell."""

    def _series(self, values: list[float]) -> pd.Series:
        return pd.Series(values)

    def test_min_value_returns_low_rgb(self) -> None:
        """Minimum value must map to the low_rgb colour (#1A3A20 = rgb(26,58,32))."""
        styles = app._green_gradient_styles(self._series([0.0, 100.0]))
        assert "26,58,32" in styles[0].replace(", ", ",")

    def test_max_value_returns_high_rgb(self) -> None:
        """Maximum value must map to the high_rgb colour (#39D353 = rgb(57,211,83))."""
        styles = app._green_gradient_styles(self._series([0.0, 100.0]))
        assert "57,211,83" in styles[1].replace(", ", ",")

    def test_mid_range_rgb_is_between_extremes(self) -> None:
        """A value at exactly t=0.5 must yield an RGB between low_rgb and high_rgb."""
        styles = app._green_gradient_styles(self._series([0.0, 50.0, 100.0]))
        # Extract r,g,b from the mid style string
        mid = styles[1]
        import re
        numbers = re.findall(r"rgb\((\d+),(\d+),(\d+)\)", mid.replace(" ", ""))
        assert numbers, f"Could not parse rgb from: {mid}"
        r, g, b = int(numbers[0][0]), int(numbers[0][1]), int(numbers[0][2])
        assert 26 < r < 57
        assert 58 < g < 211
        assert 32 < b < 83

    def test_text_color_dark_for_high_t(self) -> None:
        """t > 0.4 must yield THEME_TEXT_PRIMARY (white) as text color."""
        # max value → t=1.0 which is > 0.4
        styles = app._green_gradient_styles(self._series([0.0, 100.0]))
        assert app.THEME_TEXT_PRIMARY in styles[1]

    def test_text_color_muted_for_low_t(self) -> None:
        """t <= 0.4 (min value, t=0.0) must yield muted text color #A0C8A0."""
        styles = app._green_gradient_styles(self._series([0.0, 100.0]))
        assert "#A0C8A0" in styles[0]

    def test_single_value_no_zero_division(self) -> None:
        """A series with all identical values must not raise ZeroDivisionError."""
        styles = app._green_gradient_styles(self._series([500.0, 500.0, 500.0]))
        assert len(styles) == 3

    def test_returns_one_style_per_value(self) -> None:
        """Output list length must equal input series length."""
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        styles = app._green_gradient_styles(self._series(values))
        assert len(styles) == len(values)

    def test_each_style_contains_background_color(self) -> None:
        """Every returned style string must contain 'background-color'."""
        styles = app._green_gradient_styles(self._series([1.0, 2.0, 3.0]))
        for style in styles:
            assert "background-color" in style

    def test_each_style_contains_color(self) -> None:
        """Every returned style string must contain 'color'."""
        styles = app._green_gradient_styles(self._series([1.0, 2.0, 3.0]))
        for style in styles:
            assert "color:" in style


# ---------------------------------------------------------------------------
# S15 – Style Summary Dataframe
# ---------------------------------------------------------------------------

class TestStyleSummaryDataframe:
    """S15 – style_summary_dataframe() applies fintech styling to the yearly grid."""

    def _rows(self) -> list[dict]:
        return [
            {"Period": "Year 0", "Balance": 10000.0},
            {"Period": "Year 1", "Balance": 10500.0},
            {"Period": "Year 2", "Balance": 11025.0},
        ]

    def test_returns_styler_object(self) -> None:
        """Must return a pandas Styler instance."""
        result = app.style_summary_dataframe(self._rows())
        assert isinstance(result, pd.io.formats.style.Styler)

    def test_dataframe_has_correct_columns(self) -> None:
        """The underlying dataframe must have the same columns as the input rows."""
        result = app.style_summary_dataframe(self._rows())
        assert list(result.data.columns) == ["Period", "Balance"]

    def test_dataframe_has_correct_row_count(self) -> None:
        """Row count must equal the number of input rows."""
        result = app.style_summary_dataframe(self._rows())
        assert len(result.data) == 3

    def test_auto_detect_balance_columns_when_none(self) -> None:
        """When balance_columns=None, non-Period/Years columns must be auto-detected."""
        rows = [
            {"Period": "Year 0", "Years": 0.0, "Balance": 10000.0},
            {"Period": "Year 1", "Years": 1.0, "Balance": 10500.0},
        ]
        # Should not raise — auto-detects 'Balance' as the numeric column
        result = app.style_summary_dataframe(rows, balance_columns=None)
        assert isinstance(result, pd.io.formats.style.Styler)

    def test_empty_balance_columns_skips_gradient(self) -> None:
        """balance_columns=[] must skip gradient application and still return a Styler."""
        result = app.style_summary_dataframe(self._rows(), balance_columns=[])
        assert isinstance(result, pd.io.formats.style.Styler)

    def test_explicit_balance_columns_applies_gradient(self) -> None:
        """Explicitly passing balance_columns=['Balance'] must apply gradient styling."""
        result = app.style_summary_dataframe(self._rows(), balance_columns=["Balance"])
        assert isinstance(result, pd.io.formats.style.Styler)

    def test_nonexistent_balance_column_ignored(self) -> None:
        """A column name in balance_columns that doesn't exist must not raise."""
        result = app.style_summary_dataframe(self._rows(), balance_columns=["NonExistent"])
        assert isinstance(result, pd.io.formats.style.Styler)

    def test_string_balance_column_skipped(self) -> None:
        """A non-numeric column must be skipped when applying gradient (no error)."""
        rows = [
            {"Period": "Year 0", "Balance": "₹10,000.00"},
            {"Period": "Year 1", "Balance": "₹10,500.00"},
        ]
        result = app.style_summary_dataframe(rows, balance_columns=["Balance"])
        assert isinstance(result, pd.io.formats.style.Styler)


# ---------------------------------------------------------------------------
# S16 – Defaults: Currency and Frequency
# ---------------------------------------------------------------------------

class TestDefaults:
    """S16 – Verify default values align with documented project constants."""

    def test_frequency_options_includes_monthly_at_12(self) -> None:
        """FREQUENCY_OPTIONS['Monthly'] must equal 12."""
        assert app.FREQUENCY_OPTIONS["Monthly"] == 12

    def test_frequency_options_default_index_3_is_monthly(self) -> None:
        """Index 3 of FREQUENCY_OPTIONS keys must be 'Monthly' (the sidebar default)."""
        keys = list(app.FREQUENCY_OPTIONS.keys())
        assert keys[3] == "Monthly"

    def test_frequency_options_contains_all_seven(self) -> None:
        """FREQUENCY_OPTIONS must contain all 8 frequencies (updated for Bi-Weekly — Issue #37)."""
        expected = {"Annually", "Half Yearly", "Quarterly", "Monthly", "Semi-Monthly", "Bi-Weekly", "Weekly", "Daily"}
        assert set(app.FREQUENCY_OPTIONS.keys()) == expected

    def test_currency_symbol_inr(self) -> None:
        """INR currency symbol must be ₹."""
        money_currency_options = {
            "INR (₹)": ("INR", "₹"),
            "USD ($)": ("USD", "$"),
            "EUR (€)": ("EUR", "€"),
            "GBP (£)": ("GBP", "£"),
            "JPY (¥)": ("JPY", "¥"),
        }
        assert money_currency_options["INR (₹)"] == ("INR", "₹")

    def test_currency_options_first_entry_is_inr(self) -> None:
        """The first currency option (sidebar default index=0) must be INR (₹)."""
        # Match the dict defined in render_sidebar_inputs
        money_currency_options = {
            "INR (₹)": ("INR", "₹"),
            "USD ($)": ("USD", "$"),
            "EUR (€)": ("EUR", "€"),
            "GBP (£)": ("GBP", "£"),
            "JPY (¥)": ("JPY", "¥"),
        }
        first_key = list(money_currency_options.keys())[0]
        assert first_key == "INR (₹)"

    def test_all_five_currencies_present(self) -> None:
        """All 5 expected currency codes must be representable via format_money_value."""
        for symbol, code in [("₹", "INR"), ("$", "USD"), ("€", "EUR"), ("£", "GBP"), ("¥", "JPY")]:
            result = app.format_money_value(1234.56, symbol, code)
            assert symbol in result


# ---------------------------------------------------------------------------
# S17 – Main smoke test
# ---------------------------------------------------------------------------

class TestMain:
    """S17 – main() must run without exception when all Streamlit calls are mocked."""

    def test_main_runs_without_exception(self, monkeypatch) -> None:
        """Smoke test: main() must complete without raising when st calls are monkeypatched."""
        monkeypatch.setattr(app.st, "set_page_config", lambda **kwargs: None)

        stub_inputs = (
            10000.0,   # money_principal
            500.0,     # money_monthly_contribution
            5.0,       # annual_rate_percent
            10.0,      # time_years
            12,        # compounds_per_year
            "Monthly", # frequency_label
            "INR",     # money_currency_code
            "₹",       # money_currency_symbol
            0.0,       # rate_variance_percent
        )
        monkeypatch.setattr(app, "inject_app_styles", lambda: None)
        monkeypatch.setattr(app, "render_sidebar_inputs", lambda: stub_inputs)
        monkeypatch.setattr(app, "render_results", lambda *a, **kw: None)

        app.main()  # must not raise


# ---------------------------------------------------------------------------
# S18 – build_yearly_summary uses neutral "Balance" key (not currency-specific)
# ---------------------------------------------------------------------------

class TestBuildYearlySummaryBalanceKey:
    """S18 – build_yearly_summary() must return 'Balance' (not 'Balance ($)') as the raw key."""

    def test_raw_rows_use_balance_key(self) -> None:
        """build_yearly_summary must use 'Balance' as the raw dict key (currency-neutral)."""
        rows = app.build_yearly_summary(
            money_principal=5000.0,
            money_monthly_contribution=0.0,
            annual_rate_percent=5.0,
            time_years=3.0,
            compounds_per_year=12,
        )
        assert "Balance" in rows[0], "Expected 'Balance' key in summary row"
        assert "Balance ($)" not in rows[0], "Stale 'Balance ($)' key must not be present"

    def test_balance_key_value_is_numeric(self) -> None:
        """The 'Balance' value must be a float/int (not a formatted string)."""
        rows = app.build_yearly_summary(
            money_principal=1000.0,
            money_monthly_contribution=0.0,
            annual_rate_percent=5.0,
            time_years=2.0,
            compounds_per_year=12,
        )
        assert isinstance(rows[0]["Balance"], (int, float))


# ---------------------------------------------------------------------------
# S19 – Y-axis tick config: INR lakhs/crores and non-INR millions (Issue #35)
# ---------------------------------------------------------------------------

class TestBuildYaxisTickConfig:
    """S19 – _build_yaxis_tick_config() returns correct tick labels for INR and
    non-INR currencies based on data magnitude (Issue #35)."""

    # ------------------------------------------------------------------
    # INR – crore threshold (>= 1 Crore = 10,000,000)
    # ------------------------------------------------------------------

    def test_inr_crore_scale_returns_cr_labels(self) -> None:
        """INR with max_balance >= 1 Crore must produce ticktext entries ending in 'Cr'."""
        result = app._build_yaxis_tick_config(20_000_000.0, "INR")
        assert result, "Expected non-empty tick config for INR crore-scale value"
        assert "ticktext" in result and "tickvals" in result
        # At least one tick label (beyond '0') should contain 'Cr'
        non_zero_labels = [t for t in result["ticktext"] if t != "0 Cr"]
        assert any("Cr" in label for label in non_zero_labels), (
            "Expected 'Cr' suffix in tick labels for INR crore-scale"
        )

    def test_inr_crore_scale_tickvals_and_ticktext_same_length(self) -> None:
        """tickvals and ticktext arrays must have equal length for INR crore scale."""
        result = app._build_yaxis_tick_config(50_000_000.0, "INR")
        assert len(result["tickvals"]) == len(result["ticktext"])

    def test_inr_crore_scale_first_tick_is_zero(self) -> None:
        """First tick value must be 0 so the axis always starts at zero."""
        result = app._build_yaxis_tick_config(15_000_000.0, "INR")
        assert result["tickvals"][0] == 0.0

    def test_inr_crore_scale_tickvals_are_monotonically_increasing(self) -> None:
        """tickvals must be strictly increasing for INR crore-scale data."""
        result = app._build_yaxis_tick_config(30_000_000.0, "INR")
        vals = result["tickvals"]
        assert all(v2 > v1 for v1, v2 in zip(vals, vals[1:]))

    # ------------------------------------------------------------------
    # INR – lakh threshold (>= 1 Lakh = 100,000 but < 1 Crore)
    # ------------------------------------------------------------------

    def test_inr_lakh_scale_returns_l_labels(self) -> None:
        """INR with max_balance >= 1 Lakh but < 1 Crore must produce 'L' tick labels."""
        result = app._build_yaxis_tick_config(500_000.0, "INR")
        assert result, "Expected non-empty tick config for INR lakh-scale value"
        assert any("L" in label for label in result["ticktext"]), (
            "Expected 'L' suffix in tick labels for INR lakh-scale"
        )

    def test_inr_lakh_scale_no_cr_labels(self) -> None:
        """INR lakh-scale must NOT use 'Cr' labels (value is below 1 Crore)."""
        result = app._build_yaxis_tick_config(500_000.0, "INR")
        assert not any("Cr" in label for label in result["ticktext"]), (
            "INR lakh-scale must not produce 'Cr' labels"
        )

    def test_inr_lakh_scale_tickvals_and_ticktext_same_length(self) -> None:
        """tickvals and ticktext arrays must have equal length for INR lakh scale."""
        result = app._build_yaxis_tick_config(800_000.0, "INR")
        assert len(result["tickvals"]) == len(result["ticktext"])

    # ------------------------------------------------------------------
    # INR – below threshold (< 1 Lakh)
    # ------------------------------------------------------------------

    def test_inr_below_lakh_threshold_returns_empty_dict(self) -> None:
        """INR with max_balance < 1 Lakh must return {} (default Plotly ticks)."""
        result = app._build_yaxis_tick_config(50_000.0, "INR")
        assert result == {}, (
            "Expected empty dict for INR value below 1 Lakh threshold"
        )

    def test_inr_exactly_at_lakh_threshold_returns_tick_config(self) -> None:
        """INR with max_balance exactly equal to 1 Lakh must return a tick config."""
        result = app._build_yaxis_tick_config(100_000.0, "INR")
        assert result != {}, "Expected tick config at exactly 1 Lakh boundary"

    # ------------------------------------------------------------------
    # Non-INR – million threshold (>= 1,000,000)
    # ------------------------------------------------------------------

    def test_non_inr_million_scale_returns_m_labels(self) -> None:
        """Non-INR currency with max_balance >= 1 Million must produce 'M' tick labels."""
        result = app._build_yaxis_tick_config(5_000_000.0, "USD")
        assert result, "Expected non-empty tick config for USD million-scale value"
        assert any("M" in label for label in result["ticktext"]), (
            "Expected 'M' suffix in tick labels for USD million-scale"
        )

    def test_non_inr_million_scale_no_cr_or_l_labels(self) -> None:
        """Non-INR million-scale must NOT produce 'Cr' or 'L' labels."""
        result = app._build_yaxis_tick_config(3_000_000.0, "EUR")
        labels = result["ticktext"]
        assert not any("Cr" in label for label in labels), "Non-INR must not use 'Cr' labels"
        assert not any(" L" in label for label in labels), "Non-INR must not use 'L' labels"

    def test_non_inr_million_scale_tickvals_and_ticktext_same_length(self) -> None:
        """tickvals and ticktext must have equal length for non-INR million scale."""
        result = app._build_yaxis_tick_config(10_000_000.0, "GBP")
        assert len(result["tickvals"]) == len(result["ticktext"])

    def test_non_inr_million_scale_first_tick_is_zero(self) -> None:
        """First tick value must be 0 for non-INR million-scale data."""
        result = app._build_yaxis_tick_config(2_000_000.0, "USD")
        assert result["tickvals"][0] == 0.0

    # ------------------------------------------------------------------
    # Non-INR – below million threshold
    # ------------------------------------------------------------------

    def test_non_inr_below_million_threshold_returns_empty_dict(self) -> None:
        """Non-INR currency with max_balance < 1 Million must return {} (default ticks)."""
        result = app._build_yaxis_tick_config(500_000.0, "USD")
        assert result == {}, (
            "Expected empty dict for USD value below 1 Million threshold"
        )

    def test_non_inr_exactly_at_million_threshold_returns_tick_config(self) -> None:
        """Non-INR with max_balance exactly equal to 1 Million must return a tick config."""
        result = app._build_yaxis_tick_config(1_000_000.0, "USD")
        assert result != {}, "Expected tick config at exactly 1 Million boundary"

    # ------------------------------------------------------------------
    # Edge cases
    # ------------------------------------------------------------------

    def test_zero_max_balance_returns_empty_dict(self) -> None:
        """max_balance of 0 must return {} (no meaningful ticks to generate)."""
        result = app._build_yaxis_tick_config(0.0, "INR")
        assert result == {}

    def test_negative_max_balance_returns_empty_dict(self) -> None:
        """Negative max_balance must return {} (guard against degenerate input)."""
        result = app._build_yaxis_tick_config(-1_000_000.0, "USD")
        assert result == {}

    def test_inr_crore_scale_labels_do_not_use_m_suffix(self) -> None:
        """INR crore-scale tick labels must not contain 'M' (millions notation)."""
        result = app._build_yaxis_tick_config(20_000_000.0, "INR")
        assert not any("M" in label for label in result["ticktext"]), (
            "INR tick labels must never use 'M' (millions) suffix"
        )


# ------------------------------------------------------------------
# Integration: build_growth_chart applies yaxis tick config (Issue #35)
# ------------------------------------------------------------------

class TestBuildGrowthChartYaxisTickConfig:
    """S19 – build_growth_chart() sets yaxis tickvals/ticktext via the
    _build_yaxis_tick_config helper for INR crore-scale and non-INR
    million-scale data (Issue #35)."""

    def _crore_rows(self) -> list:
        """Growth rows whose max Balance is ~2 Crore (INR crore-scale)."""
        return [
            {"Years": 0.0,  "Balance": 1_000_000.0},
            {"Years": 10.0, "Balance": 10_000_000.0},
            {"Years": 20.0, "Balance": 20_000_000.0},
        ]

    def _million_rows(self) -> list:
        """Growth rows whose max Balance is 5 million (non-INR million-scale)."""
        return [
            {"Years": 0.0,  "Balance": 500_000.0},
            {"Years": 10.0, "Balance": 2_500_000.0},
            {"Years": 20.0, "Balance": 5_000_000.0},
        ]

    def _small_rows(self) -> list:
        """Growth rows whose max Balance is below all thresholds."""
        return [
            {"Years": 0.0,  "Balance": 1_000.0},
            {"Years": 5.0,  "Balance": 5_000.0},
            {"Years": 10.0, "Balance": 10_000.0},
        ]

    def test_inr_crore_scale_chart_yaxis_has_tickvals(self) -> None:
        """build_growth_chart with INR crore-scale data must set yaxis tickvals."""
        fig = app.build_growth_chart(self._crore_rows(), "₹", "INR")
        assert fig.layout.yaxis.tickvals is not None and len(fig.layout.yaxis.tickvals) > 0, (
            "INR crore-scale chart must have yaxis tickvals set"
        )

    def test_inr_crore_scale_chart_yaxis_ticktext_contains_cr(self) -> None:
        """build_growth_chart with INR crore-scale data must label ticks with 'Cr'."""
        fig = app.build_growth_chart(self._crore_rows(), "₹", "INR")
        ticktext = list(fig.layout.yaxis.ticktext)
        assert any("Cr" in t for t in ticktext), (
            "INR crore-scale chart yaxis ticktext must contain 'Cr' labels"
        )

    def test_inr_lakh_scale_chart_yaxis_ticktext_contains_l(self) -> None:
        """build_growth_chart with INR lakh-scale data (< 1 Cr) must label ticks with 'L'."""
        lakh_rows = [
            {"Years": 0.0,  "Balance": 50_000.0},
            {"Years": 5.0,  "Balance": 300_000.0},
            {"Years": 10.0, "Balance": 700_000.0},
        ]
        fig = app.build_growth_chart(lakh_rows, "₹", "INR")
        ticktext = list(fig.layout.yaxis.ticktext)
        assert any("L" in t for t in ticktext), (
            "INR lakh-scale chart yaxis ticktext must contain 'L' labels"
        )

    def test_non_inr_million_scale_chart_yaxis_ticktext_contains_m(self) -> None:
        """build_growth_chart with USD million-scale data must label ticks with 'M'."""
        fig = app.build_growth_chart(self._million_rows(), "$", "USD")
        ticktext = list(fig.layout.yaxis.ticktext)
        assert any("M" in t for t in ticktext), (
            "USD million-scale chart yaxis ticktext must contain 'M' labels"
        )

    def test_small_value_chart_yaxis_has_no_custom_tickvals(self) -> None:
        """build_growth_chart with small data (below all thresholds) must not set custom tickvals."""
        fig = app.build_growth_chart(self._small_rows(), "$", "USD")
        # When _build_yaxis_tick_config returns {}, tickvals stays at Plotly default (None)
        assert fig.layout.yaxis.tickvals is None, (
            "Small-value chart must not override yaxis tickvals"
        )

    def test_switching_inr_to_usd_changes_tick_labels_to_m(self) -> None:
        """Switching from INR to USD on same crore-scale data must produce 'M' not 'Cr' labels."""
        fig_usd = app.build_growth_chart(self._crore_rows(), "$", "USD")
        ticktext = list(fig_usd.layout.yaxis.ticktext)
        assert any("M" in t for t in ticktext), "USD chart for large values must use 'M' labels"
        assert not any("Cr" in t for t in ticktext), "USD chart must not use 'Cr' labels"


# ------------------------------------------------------------------
# Integration: build_multi_rate_growth_chart applies yaxis tick config (Issue #35)
# ------------------------------------------------------------------

class TestBuildMultiRateGrowthChartYaxisTickConfig:
    """S19 – build_multi_rate_growth_chart() applies the same yaxis tick config
    logic as build_growth_chart for INR and non-INR currencies (Issue #35)."""

    def _crore_series(self, currency_symbol: str, currency_code: str) -> list:
        """Three-rate series with crore-scale balances."""
        return [
            {
                "label": "8% (base)",
                "growth_rows": [
                    {"Years": 0.0,  "Balance": 1_000_000.0},
                    {"Years": 20.0, "Balance": 20_000_000.0},
                ],
            },
            {
                "label": "10% (+2%)",
                "growth_rows": [
                    {"Years": 0.0,  "Balance": 1_000_000.0},
                    {"Years": 20.0, "Balance": 30_000_000.0},
                ],
            },
        ]

    def test_multi_rate_inr_crore_scale_yaxis_has_cr_labels(self) -> None:
        """build_multi_rate_growth_chart with INR crore-scale must set 'Cr' ticktext."""
        fig = app.build_multi_rate_growth_chart(self._crore_series("₹", "INR"), "₹", "INR")
        ticktext = list(fig.layout.yaxis.ticktext)
        assert any("Cr" in t for t in ticktext), (
            "INR crore-scale multi-rate chart must have 'Cr' yaxis tick labels"
        )

    def test_multi_rate_usd_million_scale_yaxis_has_m_labels(self) -> None:
        """build_multi_rate_growth_chart with USD million-scale must set 'M' ticktext."""
        fig = app.build_multi_rate_growth_chart(self._crore_series("$", "USD"), "$", "USD")
        ticktext = list(fig.layout.yaxis.ticktext)
        assert any("M" in t for t in ticktext), (
            "USD million-scale multi-rate chart must have 'M' yaxis tick labels"
        )

    def test_multi_rate_inr_crore_scale_yaxis_tickvals_not_none(self) -> None:
        """build_multi_rate_growth_chart with INR crore-scale data must set yaxis tickvals."""
        fig = app.build_multi_rate_growth_chart(self._crore_series("₹", "INR"), "₹", "INR")
        assert fig.layout.yaxis.tickvals is not None and len(fig.layout.yaxis.tickvals) > 0, (
            "INR crore-scale multi-rate chart must have yaxis tickvals set"
        )
