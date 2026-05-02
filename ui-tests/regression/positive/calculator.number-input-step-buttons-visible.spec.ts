import { expect, test } from "@playwright/test";

test.describe("UI Regression Positive - Number Input Step Buttons Always Visible (Issue #29)", () => {
  test("app loads successfully", async ({ page }) => {
    await page.goto("/");

    // Core heading must be present confirming the app rendered
    await expect(
      page.getByText("Compound Interest Calculator")
    ).toBeVisible();
  });

  test("number input StepUp buttons are visible without hover", async ({
    page,
  }) => {
    await page.goto("/");

    // The CSS fix sets opacity:1 !important and visibility:visible !important on
    // all stNumberInputStepUp buttons, so at least one must be visible on load
    // without any hover interaction.
    const stepUpButtons = page.locator(
      "button[data-testid='stNumberInputStepUp']"
    );
    await expect(stepUpButtons.first()).toBeVisible();

    // Confirm it is actually rendered (not opacity:0 / visibility:hidden)
    const opacity = await stepUpButtons
      .first()
      .evaluate((el) => getComputedStyle(el).opacity);
    expect(Number(opacity)).toBeGreaterThan(0);
  });

  test("number input StepDown buttons are visible without hover", async ({
    page,
  }) => {
    await page.goto("/");

    // The CSS fix must also apply to stNumberInputStepDown buttons.
    const stepDownButtons = page.locator(
      "button[data-testid='stNumberInputStepDown']"
    );
    await expect(stepDownButtons.first()).toBeVisible();

    const opacity = await stepDownButtons
      .first()
      .evaluate((el) => getComputedStyle(el).opacity);
    expect(Number(opacity)).toBeGreaterThan(0);
  });

  test("StepUp button increments a number input value", async ({ page }) => {
    await page.goto("/");

    // Grab the first number input's current value, click StepUp, confirm it changed
    const firstInput = page.getByLabel(/Principal Amount/i).first();
    await expect(firstInput).toBeVisible();

    const before = await firstInput.inputValue();
    const stepUpBtn = page
      .locator("button[data-testid='stNumberInputStepUp']")
      .first();
    await stepUpBtn.click();

    const after = await firstInput.inputValue();
    // The value should have increased (step = 1 by default in Streamlit number inputs)
    expect(Number(after)).toBeGreaterThan(Number(before));
  });

  test("StepDown button decrements a number input value", async ({ page }) => {
    await page.goto("/");

    const firstInput = page.getByLabel(/Principal Amount/i).first();
    await expect(firstInput).toBeVisible();

    const before = await firstInput.inputValue();
    const stepDownBtn = page
      .locator("button[data-testid='stNumberInputStepDown']")
      .first();
    await stepDownBtn.click();

    const after = await firstInput.inputValue();
    // The value should have decreased
    expect(Number(after)).toBeLessThan(Number(before));
  });
});
