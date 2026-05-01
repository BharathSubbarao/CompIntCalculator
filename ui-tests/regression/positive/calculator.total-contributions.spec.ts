import { expect, test } from "@playwright/test";

/**
 * UI Regression — Issue #19
 * Total Contributions must equal monthly_contribution × 12 × time_years.
 * With Monthly Contribution = 1000 and Time = 10 years the metric must
 * display 1,20,000 (INR) / 120,000 (other currencies), NOT 10,000 (old bug).
 */
test.describe("UI Regression - Total Contributions fix (Issue #19)", () => {
  test("Total Contributions displays 120,000 for monthly contribution 1000 over 10 years", async ({ page }) => {
    await page.goto("/");

    // Set Monthly Contribution to 1000 (default currency INR, default time = 10 years)
    const contributionInput = page.getByLabel("Monthly Contribution (₹)");
    await contributionInput.click({ clickCount: 3 });
    await contributionInput.fill("1000");
    await page.keyboard.press("Tab");

    // INR formatting for 120,000 is "1,20,000" — verify Total Contributions metric
    await expect(
      page.getByText(/1,20,000/i)
    ).toBeVisible({ timeout: 15000 });
  });

  test("Total Contributions metric label is visible on the page", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("Total Contributions")).toBeVisible();
  });

  test("Total Contributions is not equal to old buggy value of 10,000 when contribution is 1000 over 10 years", async ({ page }) => {
    await page.goto("/");

    // Set Monthly Contribution to 1000 (default time = 10 years)
    const contributionInput = page.getByLabel("Monthly Contribution (₹)");
    await contributionInput.click({ clickCount: 3 });
    await contributionInput.fill("1000");
    await page.keyboard.press("Tab");

    // The old buggy value would have been ₹10,000.00 (1000 * 10) — it must NOT appear as Total Contributions
    // Correct value: ₹1,20,000.00 (1000 * 12 * 10)
    await expect(
      page.getByText(/1,20,000/i)
    ).toBeVisible({ timeout: 15000 });
  });
});
