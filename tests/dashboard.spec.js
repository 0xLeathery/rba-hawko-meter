// @ts-check
const { test, expect } = require('@playwright/test');

test.describe('Phase 4 — Hawk-O-Meter Gauges', () => {

  test('1. Hero gauge renders with hawk score and stance label', async ({ page }) => {
    await page.goto('/');

    // Wait for Plotly to render inside the hero gauge container
    const heroPlot = page.locator('#hero-gauge-plot');
    await expect(heroPlot).toBeVisible();

    // Plotly renders SVG elements — wait for the gauge to appear
    const svg = heroPlot.locator('svg.main-svg');
    await expect(svg.first()).toBeVisible({ timeout: 15000 });

    // Hawk score "42/100" should be visible in the rendered gauge (41.8 rounds to 42)
    await expect(heroPlot).toContainText('42/100');

    // Stance label "HOLDING STEADY" should be visible (score 46 falls in 40-60 range)
    await expect(heroPlot).toContainText('HOLDING STEADY');
  });

  test('2. Individual metric cards render with interpretations', async ({ page }) => {
    await page.goto('/');

    const grid = page.locator('#metric-gauges-grid');
    await expect(grid).toBeVisible();

    // Wait for metric cards to render (replaces the "Loading..." placeholder)
    // 5 active cards (bg-finance-gray) + 2 placeholder cards (bg-finance-gray/50) = 7 total
    const allCards = grid.locator('[class*="bg-finance-gray"]');
    await expect(allCards).toHaveCount(7, { timeout: 15000 });

    // Each card should have interpretation text with real numbers
    const cards = allCards;

    // Inflation card: "Prices up 3.8" (raw_value 3.76 rounded to 1 decimal)
    await expect(cards.nth(0)).toContainText('Prices up 3.8');

    // Wages card: "Wages up 1.6" (raw_value 1.56)
    await expect(cards.nth(1)).toContainText('Wages up 1.6');

    // Employment card (index 2): job market text
    await expect(cards.nth(2)).toContainText('job market');

    // Spending card (index 3): consumer spending text
    await expect(cards.nth(3)).toContainText('Consumer spending');

    // Building approvals card (index 4): interpretation text present
    await expect(cards.nth(4)).toContainText('Building Approvals');
  });

  test('3. Responsive layout — single column at mobile, 3 columns at desktop', async ({ page }) => {
    // Mobile viewport (375px)
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');

    const grid = page.locator('#metric-gauges-grid');
    // 5 active + 2 placeholder = 7 total
    await expect(grid.locator('[class*="bg-finance-gray"]')).toHaveCount(7, { timeout: 15000 });

    // At 375px the grid should be single-column
    let columns = await grid.evaluate(el => {
      return window.getComputedStyle(el).getPropertyValue('grid-template-columns');
    });
    // Single column: one value (no space-separated multiple values)
    expect(columns.split(' ').length).toBe(1);

    // Desktop viewport (1024px)
    await page.setViewportSize({ width: 1024, height: 768 });
    // Allow Tailwind responsive classes to re-evaluate
    await page.waitForTimeout(500);

    columns = await grid.evaluate(el => {
      return window.getComputedStyle(el).getPropertyValue('grid-template-columns');
    });
    // 3 columns at lg breakpoint
    expect(columns.split(' ').length).toBe(3);
  });

  test('4. Error state when status.json unavailable', async ({ page }) => {
    // Intercept status.json fetch and return 404
    await page.route('**/data/status.json', route => {
      route.fulfill({ status: 404, body: 'Not Found' });
    });

    await page.goto('/');

    // The error message should appear in the hero gauge area
    const heroPlot = page.locator('#hero-gauge-plot');
    await expect(heroPlot).toContainText('Unable to load economic data', { timeout: 15000 });
  });

  test('5. Staleness indicator — wages card has amber border', async ({ page }) => {
    await page.goto('/');

    const grid = page.locator('#metric-gauges-grid');
    // 5 active + 2 placeholder = 7 total
    await expect(grid.locator('[class*="bg-finance-gray"]')).toHaveCount(7, { timeout: 15000 });

    // Wages is the second card (index 1) — staleness_days=220 > 90 threshold
    const wagesCard = grid.locator('[class*="bg-finance-gray"]').nth(1);

    // The card should have the amber border class applied by renderMetricCard
    const classAttr = await wagesCard.getAttribute('class');
    expect(classAttr).toContain('border-amber-500');

    // It should also show the "months old" text
    await expect(wagesCard).toContainText('months old');
  });

});
