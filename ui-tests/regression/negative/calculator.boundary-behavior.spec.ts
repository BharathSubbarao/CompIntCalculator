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
});