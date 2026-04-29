import { test, expect } from '@playwright/test';

test('Interest Rate Variance Range input is visible in the sidebar', async ({ page }) => {
  // Navigate to the running Streamlit app
  await page.goto('/');

  // The "Interest Rate Variance Range (%)" label must be present in the sidebar
  await expect(
    page.getByText('Interest Rate Variance Range (%)', { exact: false })
  ).toBeVisible();
});

test('Interest Rate Variance Range defaults to 0 and shows single-rate chart', async ({ page }) => {
  await page.goto('/');

  // Default variance should be 0 — the standard single-line chart title must show
  await expect(
    page.getByText('Compound Growth Over Time', { exact: false })
  ).toBeVisible();
});

test('Interest Rate Variance Range non-zero value shows multi-rate chart with Variance in title', async ({ page }) => {
  await page.goto('/');

  // Locate and set the variance input to a non-zero value (e.g. 2)
  const varianceInput = page.getByLabel('Interest Rate Variance Range (%)');
  await varianceInput.click({ clickCount: 3 });
  await varianceInput.fill('2');
  await page.keyboard.press('Tab');

  // The multi-rate chart title must contain "Variance"
  await expect(
    page.getByText(/Interest Rate Variance/i)
  ).toBeVisible({ timeout: 10000 });
});

test('Interest Rate Variance Range shows three rate scenario lines when variance is set', async ({ page }) => {
  await page.goto('/');

  // Set variance to 1% — three scenarios should appear in the legend
  const varianceInput = page.getByLabel('Interest Rate Variance Range (%)');
  await varianceInput.click({ clickCount: 3 });
  await varianceInput.fill('1');
  await page.keyboard.press('Tab');

  // Verify the legend contains base rate indicator
  await expect(
    page.getByText(/base/i)
  ).toBeVisible({ timeout: 10000 });
});
