import { test, expect } from '@playwright/test';

test('Weekly dropdown option and summary update', async ({ page }) => {
  // Navigate to the running Streamlit app via baseURL (set dynamically by run_ui_regression.sh)
  await page.goto('/');

  // Locate the sidebar label and the compounding frequency select. Streamlit renders
  // a selectbox that can be addressed by its label. Use getByLabel for robustness.
  const compSelect = page.getByLabel('Compounding Frequency');
  await expect(compSelect).toBeVisible();

  // Open the select and ensure Weekly appears as an option.
  // Use exact: true to avoid matching "Bi-Weekly" which also contains "Weekly".
  await compSelect.click();
  await expect(page.getByText('Weekly', { exact: true })).toBeVisible();

  // Select Weekly and verify the summary caption updates accordingly.
  // Use exact: true to click the correct "Weekly" option (not "Bi-Weekly").
  await page.getByText('Weekly', { exact: true }).click();
  await expect(page.getByText(/Projected using weekly compounding/i)).toBeVisible();
});
