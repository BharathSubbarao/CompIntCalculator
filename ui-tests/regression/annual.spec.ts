import { test, expect } from '@playwright/test';

test('Annual dropdown option and summary update', async ({ page }) => {
  // Navigate to the running Streamlit app via baseURL configured in playwright.config.ts
  await page.goto('/');

  // Locate the sidebar label and the compounding frequency select. Streamlit renders
  // a selectbox that can be addressed by its label. Use getByLabel for robustness.
  const compSelect = page.getByLabel('Compounding Frequency');
  await expect(compSelect).toBeVisible();

  // Open the select and ensure Annual appears as an option
  await compSelect.click();
  await expect(page.getByText('Annual', { exact: true })).toBeVisible();

  // Select Annual and verify the summary caption updates accordingly
  await page.getByText('Annual', { exact: true }).click();
  await expect(page.getByText(/Projected using annual compounding/i)).toBeVisible();
});
