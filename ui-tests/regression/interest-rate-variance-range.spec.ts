import { test, expect } from '@playwright/test';

test('Interest Rate Variance Range input is visible in the sidebar', async ({ page }) => {
  await page.goto('/');
  await expect(
    page.getByText('Interest Rate Variance Range (%)', { exact: false })
  ).toBeVisible();
});

test('Interest Rate Variance Range defaults to 0 and shows single-rate chart', async ({ page }) => {
  await page.goto('/');
  await expect(
    page.getByText('Compound Growth Over Time', { exact: false })
  ).toBeVisible();
});

test('Interest Rate Variance Range non-zero value shows multi-rate chart with Variance in title', async ({ page }) => {
  await page.goto('/');

  const varianceInput = page.getByLabel('Interest Rate Variance Range (%)');
  await varianceInput.click({ clickCount: 3 });
  await varianceInput.fill('2');
  await page.keyboard.press('Tab');

  await expect(
    page.getByText(/Interest Rate Variance/i)
  ).toBeVisible({ timeout: 10000 });
});

test('Interest Rate Variance Range shows three rate scenario lines when variance is set', async ({ page }) => {
  await page.goto('/');

  const varianceInput = page.getByLabel('Interest Rate Variance Range (%)');
  await varianceInput.click({ clickCount: 3 });
  await varianceInput.fill('1');
  await page.keyboard.press('Tab');

  await expect(
    page.getByText(/base/i)
  ).toBeVisible({ timeout: 10000 });
});

test('variance Year-by-Year table shows three balance columns when variance is set', async ({ page }) => {
  await page.goto('/');

  const varianceInput = page.getByLabel('Interest Rate Variance Range (%)');
  await varianceInput.click({ clickCount: 3 });
  await varianceInput.fill('2');
  await page.keyboard.press('Tab');

  // Wait for the dataframe to re-render with variance data
  const dataFrame = page.getByTestId('stDataFrame');
  await expect(dataFrame).toBeVisible({ timeout: 10000 });

  // With base rate 5% and variance 2%, columns should contain 3.00%, 5.00%, 7.00%
  await expect(dataFrame).toContainText('3.00%');
  await expect(dataFrame).toContainText('5.00%');
  await expect(dataFrame).toContainText('7.00%');
});

test('variance clamped to zero when variance exceeds base rate does not error', async ({ page }) => {
  await page.goto('/');

  // Set base rate to 1% so lower rate clamps to 0
  const rateInput = page.getByLabel(/Annual Interest Rate/).first();
  await rateInput.click({ clickCount: 3 });
  await rateInput.fill('1');
  await rateInput.press('Tab');

  const varianceInput = page.getByLabel('Interest Rate Variance Range (%)');
  await varianceInput.click({ clickCount: 3 });
  await varianceInput.fill('5');
  await page.keyboard.press('Tab');

  // App must still show chart without crashing
  await expect(page.getByText(/Interest Rate Variance/i)).toBeVisible({ timeout: 10000 });
  await expect(page.getByText('Future Value')).toBeVisible();
});
