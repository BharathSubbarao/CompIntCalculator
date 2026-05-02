import { expect, test, type Page } from "@playwright/test";

async function selectCurrency(page: Page, currency: string) {
  await page.getByLabel("Currency").click();
  await page.getByText(currency, { exact: true }).click();
}

test.describe("UI Regression Positive - Currency and Labels", () => {
  test("default INR labels are visible", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("Principal Amount (₹)")).toBeVisible();
    await expect(page.getByText("Monthly Contribution (₹)")).toBeVisible();
  });

  test("switching currency updates dynamic labels", async ({ page }) => {
    await page.goto("/");

    await selectCurrency(page, "USD ($)");
    await expect(page.getByText("Principal Amount ($)")).toBeVisible();
    await expect(page.getByText("Monthly Contribution ($)")).toBeVisible();
    await expect(
      page.getByTestId("stPlotlyChart").getByText("Balance ($)", { exact: true })
    ).toBeVisible();

    await selectCurrency(page, "EUR (€)");
    await expect(page.getByText("Principal Amount (€)")).toBeVisible();
    await expect(page.getByText("Monthly Contribution (€)")).toBeVisible();
    await expect(
      page.getByTestId("stPlotlyChart").getByText("Balance (€)", { exact: true })
    ).toBeVisible();

    await selectCurrency(page, "GBP (£)");
    await expect(page.getByText("Principal Amount (£)")).toBeVisible();
    await expect(page.getByText("Monthly Contribution (£)")).toBeVisible();
    await expect(
      page.getByTestId("stPlotlyChart").getByText("Balance (£)", { exact: true })
    ).toBeVisible();

    await selectCurrency(page, "JPY (¥)");
    await expect(page.getByText("Principal Amount (¥)")).toBeVisible();
    await expect(page.getByText("Monthly Contribution (¥)")).toBeVisible();
    await expect(
      page.getByTestId("stPlotlyChart").getByText("Balance (¥)", { exact: true })
    ).toBeVisible();
  });

  test("metric values display currency symbols", async ({ page }) => {
    await page.goto("/");

    await selectCurrency(page, "GBP (£)");
    await expect(page.locator("[data-testid='stMetricValue']").first()).toContainText("£");
  });

  test("JPY currency symbol appears in metric values", async ({ page }) => {
    await page.goto("/");

    await selectCurrency(page, "JPY (¥)");
    await expect(page.locator("[data-testid='stMetricValue']").first()).toContainText("¥");
  });
});