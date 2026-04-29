import { expect, test } from "@playwright/test";

async function selectCompoundingFrequency(
  page: Parameters<typeof test>[0]["page"],
  frequency: string
) {
  await page.getByLabel("Compounding Frequency").click();
  await page.getByText(frequency, { exact: true }).click();
}

test.describe("UI Regression Positive - Frequency", () => {
  test("all compounding frequencies are selectable", async ({ page }) => {
    await page.goto("/");

    for (const frequency of ["Annually", "Quarterly", "Monthly", "Semi-Monthly", "Weekly", "Daily"]) {
      await selectCompoundingFrequency(page, frequency);
      await expect(
        page.getByText(new RegExp(`Projected using ${frequency.toLowerCase()} compounding`))
      ).toBeVisible();
    }
  });
});