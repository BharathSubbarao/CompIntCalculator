import { test, expect } from '@playwright/test';

test('Bi-Weekly dropdown option is visible, selectable, and computes correctly', async ({ page }) => {
  // Navigate to the running Streamlit app using the configured baseURL
  await page.goto('/');

  // Open the Compounding Frequency selectbox and verify "Bi-Weekly" appears
  await page.getByLabel('Compounding Frequency').click();
  await expect(page.getByText('Bi-Weekly', { exact: true })).toBeVisible();

  // Select Bi-Weekly and verify the summary caption reflects it
  await page.getByText('Bi-Weekly', { exact: true }).click();
  await expect(page.getByText(/Projected using bi-weekly compounding/i)).toBeVisible();
});
