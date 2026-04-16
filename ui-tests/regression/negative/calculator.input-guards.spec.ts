import { expect, test } from "@playwright/test";

async function assertNumericInputNotNegative(
  page: Parameters<typeof test>[0]["page"],
  labelPattern: RegExp
) {
  const input = page.getByLabel(labelPattern).first();

  // Streamlit number inputs expose browser-level range validation via min=0.
  await expect(input).toHaveAttribute("min", "0");
  await input.fill("-100");
  await input.press("Tab");

  const isUnderflow = await input.evaluate(
    (element) => (element as HTMLInputElement).validity.rangeUnderflow
  );
  expect(isUnderflow).toBeTruthy();

  // The app should continue rendering outputs even if a user types invalid text.
  await expect(page.locator("[data-testid='stMetricValue']").first()).toBeVisible();
}

test.describe("UI Regression Negative - Input Guardrails", () => {
  test("principal input cannot stay negative", async ({ page }) => {
    await page.goto("/");
    await assertNumericInputNotNegative(page, /Principal Amount/);
  });

  test("contribution input cannot stay negative", async ({ page }) => {
    await page.goto("/");
    await assertNumericInputNotNegative(page, /Monthly Contribution/);
  });

  test("rate input cannot stay negative", async ({ page }) => {
    await page.goto("/");
    await assertNumericInputNotNegative(page, /Annual Interest Rate/);
  });

  test("time input cannot stay negative", async ({ page }) => {
    await page.goto("/");
    await assertNumericInputNotNegative(page, /Time \(Years\)/);
  });
});