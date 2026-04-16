import { expect, test } from "@playwright/test";

test.describe("UI Regression Positive - Happy Path", () => {
  test("app loads and renders core sections", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByText("Compound Interest Calculator")).toBeVisible();
    await expect(page.getByText("Inputs")).toBeVisible();
    await expect(page.getByText("Future Value")).toBeVisible();
    await expect(page.getByText("Total Contributions")).toBeVisible();
    await expect(page.getByText("Interest Earned")).toBeVisible();
    await expect(page.getByText("Compound Growth Over Time")).toBeVisible();
    await expect(page.getByText("Year-by-Year Balance")).toBeVisible();
  });

  test("summary table has year zero row", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("[data-testid='stDataFrame']")).toContainText("Year 0");
  });
});