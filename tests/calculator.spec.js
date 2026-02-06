// @ts-check
const { test, expect } = require('@playwright/test');

test.describe('Phase 5 — Mortgage Repayment Calculator', () => {

  test.beforeEach(async ({ page }) => {
    // Clear localStorage before each test to avoid cross-contamination
    await page.goto('/');
    await page.evaluate(() => localStorage.removeItem('rba-hawko-calculator'));
    await page.reload();
  });

  test('6. Repayment math — $600k / 25yr / 3.85% P&I monthly ≈ $3,104', async ({ page }) => {
    // Default values are already $600k, 25yr, 3.85%, P&I, monthly
    // Wait for the calculator to initialize and compute
    const currentPayment = page.locator('#calc-current-payment');
    await expect(currentPayment).not.toHaveText('--', { timeout: 10000 });

    const paymentText = await currentPayment.textContent();
    // Extract numeric value from formatted currency string like "$3,104.12"
    const numericValue = parseFloat(paymentText.replace(/[^0-9.]/g, ''));

    // Standard amortization: M = 600000 * [0.003208*(1.003208)^300] / [(1.003208)^300 - 1]
    // Expected ≈ $3,104 (allow ±$10 tolerance for rounding)
    expect(numericValue).toBeGreaterThan(3090);
    expect(numericValue).toBeLessThan(3120);
  });

  test('7. Slider interaction — changing slider updates scenario payment and table', async ({ page }) => {
    // Wait for calculator to initialize
    const currentPayment = page.locator('#calc-current-payment');
    await expect(currentPayment).not.toHaveText('--', { timeout: 10000 });

    // Set the slider to 6.0%
    const slider = page.locator('#calc-slider');
    await slider.fill('6');
    // Trigger input event so calculator recalculates
    await slider.dispatchEvent('input');

    // Slider output should show 6%
    await expect(page.locator('#calc-slider-output')).toHaveText('6%');

    // Scenario payment should update to a value higher than the current payment at 3.85%
    const scenarioPayment = page.locator('#calc-scenario-payment');
    await expect(scenarioPayment).not.toHaveText('--');
    const scenarioText = await scenarioPayment.textContent();
    const scenarioValue = parseFloat(scenarioText.replace(/[^0-9.]/g, ''));
    expect(scenarioValue).toBeGreaterThan(3500); // 6% should give ~$3,865

    // Comparison table should have 3 rows
    const tableRows = page.locator('#calc-table-body tr');
    await expect(tableRows).toHaveCount(3);
  });

  test('8. localStorage persistence — loan amount survives page reload', async ({ page }) => {
    // Wait for initial load
    const currentPayment = page.locator('#calc-current-payment');
    await expect(currentPayment).not.toHaveText('--', { timeout: 10000 });

    // Change loan amount to $800,000
    const loanInput = page.locator('#calc-loan-amount');
    await loanInput.fill('800000');
    // Trigger change event so it saves to localStorage
    await loanInput.dispatchEvent('change');

    // Wait for save to complete
    await page.waitForTimeout(500);

    // Verify localStorage was updated
    const stored = await page.evaluate(() => {
      const item = localStorage.getItem('rba-hawko-calculator');
      return item ? JSON.parse(item) : null;
    });
    expect(stored).not.toBeNull();
    expect(stored.loanAmount).toBe(800000);

    // Reload the page
    await page.reload();

    // Loan amount should be restored to 800000
    await expect(loanInput).toHaveValue('800000', { timeout: 10000 });
  });

  test('9. Comparison table — 3 rows with non-empty payment values', async ({ page }) => {
    // Wait for calculator to render
    const currentPayment = page.locator('#calc-current-payment');
    await expect(currentPayment).not.toHaveText('--', { timeout: 10000 });

    // Table should have 3 rows: current rate, scenario rate, +0.25%
    const tableRows = page.locator('#calc-table-body tr');
    await expect(tableRows).toHaveCount(3);

    // Row 1: Current Rate with "current" badge
    const row1 = tableRows.nth(0);
    await expect(row1).toContainText('current');
    await expect(row1).toContainText('3.85%');

    // Row 2: Scenario Rate — payment cell should not be empty
    const row2 = tableRows.nth(1);
    const row2Payment = row2.locator('td').nth(1);
    const row2Text = await row2Payment.textContent();
    expect(row2Text.trim()).not.toBe('');
    expect(row2Text).toContain('$');

    // Row 3: +0.25% standard RBA move
    const row3 = tableRows.nth(2);
    await expect(row3).toContainText('4.1%'); // 3.85 + 0.25 = 4.10
    const row3Payment = row3.locator('td').nth(1);
    const row3Text = await row3Payment.textContent();
    expect(row3Text.trim()).not.toBe('');
    expect(row3Text).toContain('$');
  });

  test('10. Mobile responsiveness — calculator stacks vertically at 375px', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });

    // Wait for calculator to render
    const currentPayment = page.locator('#calc-current-payment');
    await expect(currentPayment).not.toHaveText('--', { timeout: 10000 });

    // Calculator form grid should be single column at mobile
    const formGrid = page.locator('#calculator-section .grid').first();
    const columns = await formGrid.evaluate(el => {
      return window.getComputedStyle(el).getPropertyValue('grid-template-columns');
    });
    // Single column: one value
    expect(columns.split(' ').length).toBe(1);

    // Calculator section itself should not overflow its container
    const calcOverflow = await page.locator('#calculator-section').evaluate(el => {
      return el.scrollWidth > el.clientWidth;
    });
    expect(calcOverflow).toBe(false);

    // All calculator inputs should be visible (not clipped off-screen)
    await expect(page.locator('#calc-loan-amount')).toBeVisible();
    await expect(page.locator('#calc-term')).toBeVisible();
    await expect(page.locator('#calc-rate')).toBeVisible();
    await expect(page.locator('#calc-slider')).toBeVisible();
  });

});
