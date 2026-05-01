import { expect, test } from "@playwright/test";

/**
 * UI Regression — Issue #24
 *
 * Bug: When Principal Amount = 0 and Monthly Contribution > 0, the
 * "Interest Earned" metric displayed a negative number.
 *
 * Root cause: money_total_contributions was computed as
 *   monthly_contribution * 12 * years
 * instead of
 *   monthly_contribution * compounds_per_year * years
 *
 * The negative value was most pronounced with low-frequency compounding
 * (e.g. Annually = 1 compound/year): the old code over-counted contributions
 * by 12×, making Interest Earned = balance - 0 - (12× actual contributions)
 * which went deeply negative.
 *
 * Example with P=0, C=100, R=5%, T=10yr, Annually:
 *   balance             ≈ $1,257.79
 *   contributions (fix) =   100 × 1 × 10 = $1,000.00
 *   Interest Earned     ≈     $257.79  ← correct (positive)
 *
 *   contributions (bug) =   100 × 12 × 10 = $12,000.00
 *   Interest Earned     ≈ -$10,742.21 ← wrong (negative)
 */
test.describe("UI Regression — Zero Principal Interest Earned fix (Issue #24)", () => {
  // ── Helper: select "Annually" compounding ──────────────────────────────────
  async function selectAnnuallyCompounding(page: Parameters<typeof test>[0]["page"]) {
    const compSelect = page.getByLabel("Compounding Frequency");
    await compSelect.click();
    // Wait for the option list to appear then click Annually
    await page.getByRole("option", { name: "Annually" }).click();
  }

  // ── Test 1: Core bug fix ───────────────────────────────────────────────────
  test(
    "Interest Earned is NON-NEGATIVE when principal=0 and monthly contribution=100 with Annually compounding",
    async ({ page }) => {
      await page.goto("/");

      // Set Principal to 0 (clear default 10,000)
      const principalInput = page.getByLabel(/Principal Amount/).first();
      await principalInput.click({ clickCount: 3 });
      await principalInput.fill("0");
      await principalInput.press("Tab");

      // Set Monthly Contribution to 100
      const contributionInput = page.getByLabel(/Monthly Contribution/).first();
      await contributionInput.click({ clickCount: 3 });
      await contributionInput.fill("100");
      await contributionInput.press("Tab");

      // Select Annually (compounds_per_year = 1) — maximises the old bug impact
      await selectAnnuallyCompounding(page);

      // "Interest Earned" metric label must be visible
      await expect(page.getByText("Interest Earned")).toBeVisible({ timeout: 15_000 });

      // Locate the Interest Earned metric container and read its value
      const interestEarnedContainer = page
        .locator('[data-testid="stMetric"]')
        .filter({ hasText: "Interest Earned" });
      await expect(interestEarnedContainer).toBeVisible({ timeout: 15_000 });

      const valueEl = interestEarnedContainer.locator('[data-testid="stMetricValue"]');
      await expect(valueEl).toBeVisible({ timeout: 15_000 });

      const valueText = await valueEl.innerText();

      // The value must NOT start with "-" (which would indicate a negative amount)
      expect(valueText, `Interest Earned should be non-negative but got: "${valueText}"`).not.toMatch(
        /^-/
      );
    }
  );

  // ── Test 2: Total Contributions is NOT 12× overcounted with Annually ────────
  test(
    "Total Contributions shows period-correct ₹1,000.00 (not overcounted ₹12,000.00) with Annually compounding",
    async ({ page }) => {
      await page.goto("/");

      // Principal → 0
      const principalInput = page.getByLabel(/Principal Amount/).first();
      await principalInput.click({ clickCount: 3 });
      await principalInput.fill("0");
      await principalInput.press("Tab");

      // Monthly Contribution → 100
      const contributionInput = page.getByLabel(/Monthly Contribution/).first();
      await contributionInput.click({ clickCount: 3 });
      await contributionInput.fill("100");
      await contributionInput.press("Tab");

      // Compounding → Annually (compounds_per_year = 1)
      await selectAnnuallyCompounding(page);

      // With the fix, using defaults (R=5%, T=10yr):
      //   total_contribs (fix) = 100 × 1 × 10 = 1,000  → "₹1,000.00"
      //   total_contribs (bug) = 100 × 12 × 10 = 12,000 → "₹12,000.00"  ← overcounted
      //
      // Verifying ₹1,000.00 is present confirms compounds_per_year is used, not 12.
      await expect(page.getByText("Total Contributions")).toBeVisible({ timeout: 15_000 });
      await expect(
        page.getByText("₹1,000.00"),
        "Total Contributions must be ₹1,000.00 (100 × 1 × 10), NOT the overcounted ₹12,000.00"
      ).toBeVisible({ timeout: 15_000 });

      // Also confirm Interest Earned is still non-negative
      const interestEarnedContainer = page
        .locator('[data-testid="stMetric"]')
        .filter({ hasText: "Interest Earned" });
      const valueEl = interestEarnedContainer.locator('[data-testid="stMetricValue"]');
      await expect(valueEl).toBeVisible({ timeout: 15_000 });
      const valueText = await valueEl.innerText();
      expect(valueText, `Interest Earned should be non-negative; got: "${valueText}"`).not.toMatch(/^-/);
    }
  );

  // ── Test 3: Regression — non-zero principal still works correctly ──────────
  test(
    "Regression: non-zero principal with non-zero contribution still shows non-negative Interest Earned",
    async ({ page }) => {
      await page.goto("/");

      // Principal = 5,000 (non-zero)
      const principalInput = page.getByLabel(/Principal Amount/).first();
      await principalInput.click({ clickCount: 3 });
      await principalInput.fill("5000");
      await principalInput.press("Tab");

      // Monthly Contribution = 200
      const contributionInput = page.getByLabel(/Monthly Contribution/).first();
      await contributionInput.click({ clickCount: 3 });
      await contributionInput.fill("200");
      await contributionInput.press("Tab");

      // Rate = 5%, Time = 10yr (defaults)
      // Compounding → Annually (most impactful case from the bug)
      await selectAnnuallyCompounding(page);

      await expect(page.getByText("Interest Earned")).toBeVisible({ timeout: 15_000 });

      const interestEarnedContainer = page
        .locator('[data-testid="stMetric"]')
        .filter({ hasText: "Interest Earned" });
      const valueEl = interestEarnedContainer.locator('[data-testid="stMetricValue"]');
      await expect(valueEl).toBeVisible({ timeout: 15_000 });

      const valueText = await valueEl.innerText();
      expect(valueText, `Interest Earned should be non-negative but got: "${valueText}"`).not.toMatch(
        /^-/
      );
    }
  );

  // ── Test 4: Regression — default inputs (P>0, C=0) still work ─────────────
  test(
    "Regression: default inputs (principal=10000, contribution=0) show non-negative Interest Earned",
    async ({ page }) => {
      await page.goto("/");

      // Use all defaults: Principal=10000, Contribution=0, Rate=5%, Time=10, Monthly
      await expect(page.getByText("Future Value")).toBeVisible({ timeout: 15_000 });
      await expect(page.getByText("Total Contributions")).toBeVisible();
      await expect(page.getByText("Interest Earned")).toBeVisible();

      const interestEarnedContainer = page
        .locator('[data-testid="stMetric"]')
        .filter({ hasText: "Interest Earned" });
      const valueEl = interestEarnedContainer.locator('[data-testid="stMetricValue"]');
      await expect(valueEl).toBeVisible({ timeout: 15_000 });

      const valueText = await valueEl.innerText();
      expect(valueText, `Default Interest Earned should be non-negative; got: "${valueText}"`).not.toMatch(
        /^-/
      );
    }
  );
});
