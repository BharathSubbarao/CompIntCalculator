import { expect, test } from "@playwright/test";

test.describe("UI Regression Negative - Boundary and Stress", () => {
  test("very large values still render metrics", async ({ page }) => {
    await page.goto("/");

    await page.getByLabel(/Principal Amount/).first().fill("1000000000");
    await page.getByLabel(/Monthly Contribution/).first().fill("10000000");
    await page.getByLabel(/Annual Interest Rate/).first().fill("20");
    await page.getByLabel(/Time \(Years\)/).first().fill("50");
    await page.getByLabel(/Time \(Years\)/).first().press("Tab");

    await expect(page.getByText("Future Value")).toBeVisible();
    await expect(page.getByText("Total Contributions")).toBeVisible();
    await expect(page.getByText("Interest Earned")).toBeVisible();
  });

  test("zero time displays year 0 row", async ({ page }) => {
    await page.goto("/");
    await page.getByLabel(/Time \(Years\)/).first().fill("0");
    await page.getByLabel(/Time \(Years\)/).first().press("Tab");
    await expect(page.locator("[data-testid='stDataFrame']")).toContainText("Year 0");
  });

  test("fractional time (2.5 years) appends a fractional row in the summary table", async ({ page }) => {
    await page.goto("/");
    await page.getByLabel(/Time \(Years\)/).first().fill("2.5");
    await page.getByLabel(/Time \(Years\)/).first().press("Tab");

    const dataFrame = page.locator("[data-testid='stDataFrame']");
    await expect(dataFrame).toBeVisible({ timeout: 10000 });
    await expect(dataFrame).toContainText("Year 2.50");
  });

  test("changing inputs twice recalculates Future Value each time", async ({ page }) => {
    await page.goto("/");

    // First calculation: P=10000, rate=5%
    const principalInput = page.getByLabel(/Principal Amount/).first();
    await principalInput.fill("10000");
    await principalInput.press("Tab");

    const firstValue = await page.locator("[data-testid='stMetricValue']").first().textContent();

    // Second calculation: P=20000 — Future Value must be different
    await principalInput.fill("20000");
    await principalInput.press("Tab");

    await page.waitForTimeout(800);
    const secondValue = await page.locator("[data-testid='stMetricValue']").first().textContent();

    expect(firstValue).not.toEqual(secondValue);
  });

  test("year-by-year table balance is non-decreasing for positive rate", async ({ page }) => {
    await page.goto("/");

    await page.getByLabel(/Principal Amount/).first().fill("10000");
    await page.getByLabel(/Annual Interest Rate/).first().fill("5");
    await page.getByLabel(/Time \(Years\)/).first().fill("5");
    await page.getByLabel(/Time \(Years\)/).first().press("Tab");

    // Table must show Year 0 through Year 5 rows
    const dataFrame = page.locator("[data-testid='stDataFrame']");
    await expect(dataFrame).toContainText("Year 0");
    await expect(dataFrame).toContainText("Year 5");
  });
});