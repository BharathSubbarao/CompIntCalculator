import { test, expect } from '@playwright/test';

test('Semi-Monthly dropdown option is visible and selectable', async ({ page }) => {
  // Navigate to the running Streamlit app using the configured baseURL
  await page.goto('/');

  // Open the Compounding Frequency selectbox and verify "Semi-Monthly" appears
  await page.getByLabel('Compounding Frequency').click();
  await expect(page.getByText('Semi-Monthly', { exact: true })).toBeVisible();

  // Select Semi-Monthly and verify the summary caption reflects it
  await page.getByText('Semi-Monthly', { exact: true }).click();
  await expect(page.getByText(/Projected using semi-monthly compounding/i)).toBeVisible();
});
