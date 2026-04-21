import { test, expect } from '@playwright/test';

test('Half Yearly dropdown option and summary update', async ({ page }) => {
  // Navigate to the running Streamlit app (default port)
  await page.goto('http://localhost:8501', { waitUntil: 'networkidle' });

  // Locate the sidebar label and the compounding frequency select. Streamlit renders
  // a selectbox that can be addressed by its label. Use getByLabel for robustness.
  const compSelect = page.getByLabel('Compounding Frequency');
  await expect(compSelect).toBeVisible();

  // Open the select and ensure Half Yearly appears as an option
  await compSelect.click();
  await expect(page.getByText('Half Yearly')).toBeVisible();

  // Select Half Yearly and verify the summary caption updates accordingly
  await page.getByText('Half Yearly').click();
  await expect(page.getByText(/Projected using half yearly compounding/i)).toBeVisible();
});
