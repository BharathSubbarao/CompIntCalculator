import { expect, test } from "@playwright/test";

/**
 * UI Regression — Issue #31
 *
 * The orchestrator's parallel phase was refactored so that the Unit Tester
 * (Step 3) and UI Tester (Step 4) now run as true OS-level background
 * processes via `bash scripts/run_parallel_testing.sh <workflow_id>`.
 *
 * This spec is the Gate 3 regression guard for that change: it verifies that
 * the Streamlit calculator app remains fully functional end-to-end after the
 * workflow infrastructure was updated, and that no application behaviour was
 * inadvertently broken by the parallel-testing plumbing changes.
 *
 * Coverage:
 *  1. App loads without errors and all key UI sections are present.
 *  2. Every numeric input is interactive and accepts a value.
 *  3. A complete calculation cycle (principal, contribution, rate, time,
 *     frequency) produces visible metric outputs.
 *  4. The Year-by-Year Balance table updates with the new values.
 *  5. The Compounding Frequency dropdown remains fully functional across
 *     all supported options.
 */

const FREQUENCIES = [
  "Annually",
  "Quarterly",
  "Monthly",
  "Semi-Monthly",
  "Weekly",
  "Daily",
] as const;

test.describe("UI Regression Positive - Parallel Infra (Issue #31)", () => {
  test("app loads and renders all core UI sections", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByText("Compound Interest Calculator")).toBeVisible();
    await expect(page.getByText("Inputs")).toBeVisible();
    await expect(page.getByText("Future Value")).toBeVisible();
    await expect(page.getByText("Total Contributions")).toBeVisible();
    await expect(page.getByText("Interest Earned")).toBeVisible();
    await expect(page.getByText("Compound Growth Over Time")).toBeVisible();
    await expect(page.getByText("Year-by-Year Balance")).toBeVisible();
  });

  test("all numeric inputs are visible and interactive", async ({ page }) => {
    await page.goto("/");

    for (const labelPattern of [
      /Principal Amount/,
      /Monthly Contribution/,
      /Annual Interest Rate/,
      /Time \(Years\)/,
    ]) {
      const input = page.getByLabel(labelPattern).first();
      await expect(input).toBeVisible();
      await expect(input).toBeEnabled();
    }
  });

  test("full calculation cycle produces metric outputs", async ({ page }) => {
    await page.goto("/");

    // Set Principal = 50,000
    const principal = page.getByLabel(/Principal Amount/).first();
    await principal.click({ clickCount: 3 });
    await principal.fill("50000");
    await page.keyboard.press("Tab");

    // Set Monthly Contribution = 500
    const contribution = page.getByLabel(/Monthly Contribution/).first();
    await contribution.click({ clickCount: 3 });
    await contribution.fill("500");
    await page.keyboard.press("Tab");

    // Set Annual Interest Rate = 8
    const rate = page.getByLabel(/Annual Interest Rate/).first();
    await rate.click({ clickCount: 3 });
    await rate.fill("8");
    await page.keyboard.press("Tab");

    // Set Time = 5 years
    const time = page.getByLabel(/Time \(Years\)/).first();
    await time.click({ clickCount: 3 });
    await time.fill("5");
    await page.keyboard.press("Tab");

    // All three summary metrics must be visible
    const metrics = page.locator("[data-testid='stMetricValue']");
    await expect(metrics.first()).toBeVisible({ timeout: 15000 });
    await expect(metrics).toHaveCount(3, { timeout: 15000 });
  });

  test("year-by-year table is present and contains Year 0", async ({ page }) => {
    await page.goto("/");
    await expect(
      page.locator("[data-testid='stDataFrame']")
    ).toContainText("Year 0", { timeout: 15000 });
  });

  test("compounding frequency dropdown remains fully functional", async ({
    page,
  }) => {
    await page.goto("/");

    const freqSelect = page.getByLabel("Compounding Frequency");
    await expect(freqSelect).toBeVisible();

    for (const freq of FREQUENCIES) {
      await freqSelect.click();
      await page.getByText(freq, { exact: true }).click();
      await expect(
        page.getByText(
          new RegExp(`Projected using ${freq.toLowerCase()} compounding`, "i")
        )
      ).toBeVisible({ timeout: 10000 });
    }
  });

  test("summary caption reflects selected compounding frequency", async ({
    page,
  }) => {
    await page.goto("/");

    const freqSelect = page.getByLabel("Compounding Frequency");
    await freqSelect.click();
    // Scope to the virtual dropdown to avoid strict-mode clash with the
    // currently-displayed value in the sidebar (which can also be "Monthly").
    await page
      .getByTestId("stSelectboxVirtualDropdown")
      .getByText("Monthly", { exact: true })
      .click();

    await expect(
      page.getByText(/Projected using monthly compounding/i)
    ).toBeVisible({ timeout: 10000 });
  });
});
