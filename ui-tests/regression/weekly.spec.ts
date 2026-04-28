import { test, expect } from '@playwright/test';

test('Weekly dropdown option and summary update', async ({ page }) => {
  // Navigate to the running Streamlit app using the configured base URL
  await page.goto('/');

  // Locate the sidebar label and the compounding frequency select. Streamlit renders
  // a selectbox that can be addressed by its label. Use getByLabel for robustness.
  const compSelect = page.getByLabel('Compounding Frequency');
  await expect(compSelect).toBeVisible();

  // Open the select and ensure Weekly appears as an option
  await compSelect.click();
  const dropdown = page.getByTestId('stSelectboxVirtualDropdown');
  await expect(dropdown.getByText('Weekly', { exact: true })).toBeVisible();

  // Select Weekly and verify the summary caption updates accordingly
  await dropdown.getByText('Weekly', { exact: true }).click();
  await expect(page.getByText(/Projected using weekly compounding/i)).toBeVisible();
});
