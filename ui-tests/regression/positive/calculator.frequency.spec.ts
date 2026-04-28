import { expect, test } from "@playwright/test";

async function selectCompoundingFrequency(
  page: Parameters<typeof test>[0]["page"],
  frequency: string
) {
  await page.getByLabel("Compounding Frequency").click();
  const dropdown = page.getByTestId('stSelectboxVirtualDropdown');
  await dropdown.getByText(frequency, { exact: true }).click();
}

test.describe("UI Regression Positive - Frequency", () => {
  test("all compounding frequencies are selectable", async ({ page }) => {
    await page.goto("/");

    for (const frequency of ["Annually", "Quarterly", "Monthly", "Bi-Weekly", "Weekly", "Daily"]) {
      await selectCompoundingFrequency(page, frequency);
      await expect(
        page.getByText(new RegExp(`Projected using ${frequency.toLowerCase()} compounding`))
      ).toBeVisible();
    }
  });

  test("Bi-Weekly option is present and selectable in dropdown", async ({ page }) => {
    await page.goto("/");

    await page.getByLabel("Compounding Frequency").click();
    const dropdown = page.getByTestId('stSelectboxVirtualDropdown');
    await expect(dropdown.getByText("Bi-Weekly", { exact: true })).toBeVisible();
    await dropdown.getByText("Bi-Weekly", { exact: true }).click();
    await expect(
      page.getByText(/Projected using bi-weekly compounding/i)
    ).toBeVisible();
  });

  test("Half Yearly option is no longer present in dropdown", async ({ page }) => {
    await page.goto("/");

    await page.getByLabel("Compounding Frequency").click();
    const dropdown = page.getByTestId('stSelectboxVirtualDropdown');
    await expect(dropdown.getByText("Half Yearly", { exact: true })).not.toBeVisible();
  });
});