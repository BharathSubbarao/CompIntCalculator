import { test, expect } from '@playwright/test';

test('Semi-Weekly dropdown option is visible and selectable', async ({ page }) => {
  // Navigate to the running Streamlit app using the configured baseURL
  await page.goto('/');

  // Open the Compounding Frequency selectbox and verify "Semi-Weekly" appears
  await page.getByLabel('Compounding Frequency').click();
  await expect(page.getByText('Semi-Weekly', { exact: true })).toBeVisible();

  // Select Semi-Weekly and verify the summary caption reflects it
  await page.getByText('Semi-Weekly', { exact: true }).click();
  await expect(page.getByText(/Projected using semi-weekly compounding/i)).toBeVisible();
});
