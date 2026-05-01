import { expect, test } from "@playwright/test";

/**
 * UI Regression — Issue #24 (corrected root-cause analysis)
 *
 * Bug: When Principal Amount = 0 and Monthly Contribution > 0, the
 * "Interest Earned" metric displayed a negative number with low-frequency
 * compounding (e.g. Annually).
 *
 * Root cause: calculate_compound_balance treated the monthly contribution as
 * a per-compounding-period contribution, so with Annual compounding (n=1) the
 * FV only grew by C × 1 per year — far less than the 12 × C that the user
 * actually deposits each year.  The real fix is two-part:
 *   1. calculate_compound_balance converts C to per-period: C × 12 / n
 *   2. money_total_contributions = C × 12 × years  (always monthly semantics)
 *
 * Example with P=0, C=100, R=5%, T=10yr, Annually:
 *   periodic contribution (fixed) = 100 × 12 / 1 = 1,200/year
 *   balance (fixed)    ≈ ₹15,093.47
 *   contributions      =  100 × 12 × 10 = ₹12,000.00
 *   Interest Earned    ≈   ₹3,093.47  ← correct (positive)
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

  // ── Test 2: Total Contributions is always monthly × 12 × years ──────────────
  test(
    "Total Contributions shows monthly-correct ₹12,000.00 (100 × 12 × 10) with Annually compounding",
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

      // Total Contributions = monthly_contribution × 12 months/year × years
      //   = 100 × 12 × 10 = 12,000  → "₹12,000.00"
      // This must NOT show ₹1,000.00 (the Issue #24 regression value: 100 × 1 × 10).
      await expect(page.getByText("Total Contributions")).toBeVisible({ timeout: 15_000 });
      await expect(
        page.getByText("₹12,000.00"),
        "Total Contributions must be ₹12,000.00 (100 × 12 × 10), NOT the under-counted ₹1,000.00"
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
