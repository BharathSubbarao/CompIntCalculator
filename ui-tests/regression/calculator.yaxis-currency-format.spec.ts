import { test, expect, Locator } from '@playwright/test';

// ---------------------------------------------------------------------------
// Helper: fill a Streamlit number input (triple-click to select all, then fill)
// ---------------------------------------------------------------------------
async function fillNumberInput(locator: Locator, value: string) {
  await locator.click({ clickCount: 3 });
  await locator.fill(value);
  await locator.press('Tab');
}

// ---------------------------------------------------------------------------
// Helper: wait for at least one Plotly Y-axis tick label that contains `unit`
//   Plotly renders tick labels as SVG <text> nodes inside .ytick elements.
// ---------------------------------------------------------------------------
async function expectYAxisUnit(page: import('@playwright/test').Page, unit: string | RegExp) {
  const yTicks = page.locator('.ytick text');
  // At least one tick label should contain the expected unit string / pattern
  await expect(yTicks.filter({ hasText: unit }).first()).toBeVisible({ timeout: 15000 });
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

test('Currency selector is visible and defaults to INR (₹)', async ({ page }) => {
  await page.goto('/');

  const currencySelect = page.getByLabel('Currency');
  await expect(currencySelect).toBeVisible();

  // Verify INR is selected by default: the dynamic label for the principal input
  // changes to include the currency symbol — "Principal Amount (₹)" confirms INR.
  await expect(page.getByText('Principal Amount (₹)')).toBeVisible({ timeout: 10000 });
});

test('Currency dropdown lists all expected options', async ({ page }) => {
  await page.goto('/');

  const currencySelect = page.getByLabel('Currency');
  await currencySelect.click();

  // Scope checks to the virtual dropdown to avoid strict-mode violations
  // (the sidebar also shows the currently-selected value text alongside the open dropdown)
  const dropdown = page.getByTestId('stSelectboxVirtualDropdown');
  await expect(dropdown.getByText('INR (₹)')).toBeVisible();
  await expect(dropdown.getByText('USD ($)')).toBeVisible();
  await expect(dropdown.getByText('EUR (€)')).toBeVisible();
  await expect(dropdown.getByText('GBP (£)')).toBeVisible();
  await expect(dropdown.getByText('JPY (¥)')).toBeVisible();
});

test('INR with crore-range principal shows "Cr" labels on Y-axis', async ({ page }) => {
  await page.goto('/');

  // INR is selected by default — enter a principal of 5 crore (50,000,000)
  const principalInput = page.getByLabel('Principal Amount (₹)');
  await fillNumberInput(principalInput, '50000000');

  // The chart title must be present
  await expect(page.getByText('Compound Growth Over Time', { exact: false })).toBeVisible({
    timeout: 10000,
  });

  // Y-axis ticks should carry the "Cr" (crore) unit suffix
  await expectYAxisUnit(page, /Cr/);
});

test('INR with lakh-range principal shows "L" labels on Y-axis', async ({ page }) => {
  await page.goto('/');

  // Enter a principal of 5 lakhs (500,000)
  const principalInput = page.getByLabel('Principal Amount (₹)');
  await fillNumberInput(principalInput, '500000');

  await expect(page.getByText('Compound Growth Over Time', { exact: false })).toBeVisible({
    timeout: 10000,
  });

  // Y-axis ticks should carry the "L" (lakh) unit suffix
  await expectYAxisUnit(page, /\bL\b/);
});

test('INR with small principal shows default (no Cr/L/M) Y-axis labels', async ({ page }) => {
  await page.goto('/');

  // Default principal 10,000 is well below 1 lakh — Y-axis should NOT show Cr/L/M
  await expect(page.getByText('Compound Growth Over Time', { exact: false })).toBeVisible({
    timeout: 10000,
  });

  const crTicks = page.locator('.ytick text').filter({ hasText: /Cr/ });
  const lTicks  = page.locator('.ytick text').filter({ hasText: /\bL\b/ });
  const mTicks  = page.locator('.ytick text').filter({ hasText: /\bM\b/ });

  await expect(crTicks).toHaveCount(0);
  await expect(lTicks).toHaveCount(0);
  await expect(mTicks).toHaveCount(0);
});

test('USD with million-range principal shows "M" labels on Y-axis', async ({ page }) => {
  await page.goto('/');

  // Switch currency to USD ($)
  const currencySelect = page.getByLabel('Currency');
  await currencySelect.click();
  await page.getByText('USD ($)').click();

  // Enter a principal of $2,000,000 (2 million)
  const principalInput = page.getByLabel('Principal Amount ($)');
  await fillNumberInput(principalInput, '2000000');

  await expect(page.getByText('Compound Growth Over Time', { exact: false })).toBeVisible({
    timeout: 10000,
  });

  // Y-axis ticks should carry the "M" (million) unit suffix
  await expectYAxisUnit(page, /\bM\b/);
});

test('Switching from INR (crore) to USD keeps "M" and removes "Cr" on Y-axis', async ({ page }) => {
  await page.goto('/');

  // --- Step 1: INR with crore-range principal → expect "Cr" ---
  const principalInr = page.getByLabel('Principal Amount (₹)');
  await fillNumberInput(principalInr, '50000000');

  await expect(page.getByText('Compound Growth Over Time', { exact: false })).toBeVisible({
    timeout: 10000,
  });
  await expectYAxisUnit(page, /Cr/);

  // --- Step 2: Switch to USD → same large principal → expect "M", no "Cr" ---
  const currencySelect = page.getByLabel('Currency');
  await currencySelect.click();
  await page.getByText('USD ($)').click();

  // Streamlit re-renders with the same numeric principal value under the new currency
  await expect(page.getByText('Compound Growth Over Time', { exact: false })).toBeVisible({
    timeout: 10000,
  });

  await expectYAxisUnit(page, /\bM\b/);

  // "Cr" labels must no longer be present after switching to USD
  const crTicksAfterSwitch = page.locator('.ytick text').filter({ hasText: /Cr/ });
  await expect(crTicksAfterSwitch).toHaveCount(0);
});

test('Switching from USD (million) back to INR shows "Cr" and removes "M" on Y-axis', async ({ page }) => {
  await page.goto('/');

  // Start in USD
  const currencySelect = page.getByLabel('Currency');
  await currencySelect.click();
  await page.getByText('USD ($)').click();

  const principalUsd = page.getByLabel('Principal Amount ($)');
  await fillNumberInput(principalUsd, '20000000');

  await expect(page.getByText('Compound Growth Over Time', { exact: false })).toBeVisible({
    timeout: 10000,
  });
  await expectYAxisUnit(page, /\bM\b/);

  // Switch back to INR — 20,000,000 INR = 2 crore → expect "Cr"
  await currencySelect.click();
  await page.getByText('INR (₹)').click();

  await expect(page.getByText('Compound Growth Over Time', { exact: false })).toBeVisible({
    timeout: 10000,
  });
  await expectYAxisUnit(page, /Cr/);

  // "M" labels must no longer be present after switching back to INR
  const mTicksAfterSwitch = page.locator('.ytick text').filter({ hasText: /\bM\b/ });
  await expect(mTicksAfterSwitch).toHaveCount(0);
});
