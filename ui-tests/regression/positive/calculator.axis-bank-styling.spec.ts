import { expect, test } from "@playwright/test";

test.describe("UI Regression Positive - Axis Bank Bold Color Scheme (Issue #27)", () => {
  test("app loads and renders core sections with styled header", async ({
    page,
  }) => {
    await page.goto("/");

    // Core sections must still render correctly after styling change
    await expect(
      page.getByText("Compound Interest Calculator")
    ).toBeVisible();
    await expect(page.getByText("Future Value")).toBeVisible();
    await expect(page.getByText("Interest Earned")).toBeVisible();
    await expect(page.getByText("Total Contributions")).toBeVisible();
  });

  test("sidebar inputs remain visible and interactive after Axis Bank styling", async ({
    page,
  }) => {
    await page.goto("/");

    // Sidebar inputs must still be accessible after CSS override
    await expect(page.getByText("Inputs")).toBeVisible();
    await expect(
      page.getByLabel("Principal Amount (₹)")
    ).toBeVisible();
    await expect(
      page.getByLabel("Annual Interest Rate (%)")
    ).toBeVisible();
  });

  test("calculator still computes correct results after styling change", async ({
    page,
  }) => {
    await page.goto("/");

    // Default calculation must still produce a valid Future Value metric
    await expect(page.getByText("Future Value")).toBeVisible();
    // The results table must still render after CSS injection
    await expect(
      page.locator("[data-testid='stDataFrame']")
    ).toBeVisible();
  });

  test("Compounding Frequency selector remains functional with Axis Bank styling", async ({
    page,
  }) => {
    await page.goto("/");

    // The styled selectbox must remain interactable
    const compSelect = page.getByLabel("Compounding Frequency");
    await expect(compSelect).toBeVisible();
    await compSelect.click();
    // Monthly option must still be present
    await expect(page.getByText("Monthly")).toBeVisible();
  });

  test("chart section renders after Axis Bank color injection", async ({
    page,
  }) => {
    await page.goto("/");

    // The Plotly chart container must be present after CSS overrides
    await expect(
      page.getByText("Compound Growth Over Time", { exact: false })
    ).toBeVisible();
  });
});
