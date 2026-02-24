// @ts-check
const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

// Read hawk score from status.json so tests aren't coupled to specific pipeline output
const statusJson = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'public', 'data', 'status.json'), 'utf8'));
const hawkScore = Math.round(statusJson.overall.hawk_score);

// Derive the expected stance label from the score (mirrors gauges.js ZONE_COLORS logic)
function getExpectedStanceLabel(score) {
  if (score < 20) return 'RATES LIKELY FALLING';
  if (score < 40) return 'LEANING TOWARDS CUTS';
  if (score < 60) return 'HOLDING STEADY';
  if (score < 80) return 'LEANING TOWARDS RISES';
  return 'RATES LIKELY RISING';
}
const expectedStance = getExpectedStanceLabel(hawkScore);

test.describe('Phase 4 — Hawk-O-Meter Gauges', () => {

  test('1. Hero gauge renders with hawk score and stance label', async ({ page }) => {
    await page.goto('/');

    // Wait for Plotly to render inside the hero gauge container
    const heroPlot = page.locator('#hero-gauge-plot');
    await expect(heroPlot).toBeVisible();

    // Plotly renders SVG elements — wait for the gauge to appear
    const svg = heroPlot.locator('svg.main-svg');
    await expect(svg.first()).toBeVisible({ timeout: 15000 });

    // Hawk score should be visible as "<score>/100" (derived from status.json)
    await expect(heroPlot).toContainText(`${hawkScore}/100`);

    // Stance label should match the zone for the current score
    await expect(heroPlot).toContainText(expectedStance);
  });

  test('2. Individual metric cards render with interpretations', async ({ page }) => {
    await page.goto('/');

    const grid = page.locator('#metric-gauges-grid');
    await expect(grid).toBeVisible();

    // Wait for metric cards to render (replaces the "Loading..." placeholder)
    // 6 active cards (bg-finance-gray) + 1 placeholder card (bg-finance-gray/50) = 7 total
    // METRIC_ORDER: inflation, wages, employment, housing, spending, building_approvals, business_confidence
    const allCards = grid.locator('[class*="bg-finance-gray"]');
    await expect(allCards).toHaveCount(7, { timeout: 15000 });

    // Each card should have interpretation text with real numbers
    const cards = allCards;

    // Inflation card: should show "Prices up" with a percentage
    await expect(cards.nth(0)).toContainText('Prices up');

    // Wages card: should show "Wages up" with a percentage
    await expect(cards.nth(1)).toContainText('Wages up');

    // Employment card (index 2): job market text
    await expect(cards.nth(2)).toContainText('job market');

    // Housing card (index 3): directional label (RISING/FALLING/STEADY)
    await expect(cards.nth(3)).toContainText(/(?:RISING|FALLING|STEADY)/);

    // Spending card (index 4): consumer spending text
    await expect(cards.nth(4)).toContainText('Consumer spending');

    // Building approvals card (index 5): interpretation text present
    await expect(cards.nth(5)).toContainText('Building Approvals');
  });

  test('3. Responsive layout — single column at mobile, 3 columns at desktop', async ({ page }) => {
    // Mobile viewport (375px)
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');

    const grid = page.locator('#metric-gauges-grid');
    // 6 active + 1 placeholder = 7 total
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
    // 6 active + 1 placeholder = 7 total
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

test.describe('Phase 9 — Housing Prices Gauge', () => {

  test('housing gauge shows directional label and source attribution', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('#metric-gauges-grid');

    // Check housing card exists (not a placeholder)
    const housingCard = page.locator('#metric-gauges-grid .bg-finance-gray').filter({ hasText: 'Housing' });
    await expect(housingCard).toBeVisible({ timeout: 15000 });

    // Check directional label (RISING, FALLING, or STEADY) with % in interpretation
    const interpretation = housingCard.locator('[id^="interp-housing"]');
    await expect(interpretation).toContainText(/(?:RISING|FALLING|STEADY)/);
    await expect(interpretation).toContainText('year-on-year');

    // Check quarter format label
    await expect(interpretation).toContainText(/\(Q\d \d{4}\)/);

    // Check source attribution
    await expect(housingCard).toContainText('Source: ABS RPPI');
  });

  test('housing gauge has no amber staleness border despite stale data', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('#metric-gauges-grid');

    const housingCard = page.locator('#metric-gauges-grid .bg-finance-gray').filter({ hasText: 'Housing' });
    await expect(housingCard).toBeVisible({ timeout: 15000 });

    // Housing card should NOT have amber border even though data is >90 days old
    const classAttr = await housingCard.getAttribute('class');
    expect(classAttr).not.toContain('border-amber-500');
  });

});

test.describe('Phase 7 — ASX Futures Section', () => {

  test('6. ASX futures section renders with probability table when data available', async ({ page }) => {
    // Intercept status.json and inject asx_futures data
    await page.route('**/data/status.json', async route => {
      const response = await route.fetch();
      const json = await response.json();
      // Inject test asx_futures data with multi-meeting contract
      json.asx_futures = {
        current_rate: 4.35,
        implied_rate: 4.10,
        next_meeting: '2026-02-18',
        direction: 'cut',
        data_date: '2026-02-07',
        staleness_days: 0,
        probabilities: { cut: 85, hold: 15, hike: 0 },
        meetings: [
          {
            meeting_date: '2026-03-03',
            meeting_date_label: '3 Mar 2026',
            implied_rate: 4.10,
            change_bp: -25.0,
            probability_cut: 85,
            probability_hold: 15,
            probability_hike: 0
          },
          {
            meeting_date: '2026-04-07',
            meeting_date_label: '7 Apr 2026',
            implied_rate: 4.15,
            change_bp: -20.0,
            probability_cut: 60,
            probability_hold: 40,
            probability_hike: 0
          },
          {
            meeting_date: '2026-05-19',
            meeting_date_label: '19 May 2026',
            implied_rate: 4.20,
            change_bp: -15.0,
            probability_cut: 40,
            probability_hold: 60,
            probability_hike: 0
          }
        ]
      };
      await route.fulfill({ json });
    });

    await page.goto('/');

    // The ASX futures container should be visible
    const asxContainer = page.locator('#asx-futures-container');
    await expect(asxContainer).toBeVisible({ timeout: 15000 });

    // Should show "What Markets Expect" heading
    await expect(asxContainer).toContainText('What Markets Expect');

    // Should show multi-meeting table rows
    await expect(asxContainer).toContainText('3 Mar 2026');
    await expect(asxContainer).toContainText('7 Apr 2026');
    await expect(asxContainer).toContainText('4.10%');
    await expect(asxContainer).toContainText('Data as of');
  });

  test('7. ASX futures section shows placeholder when data unavailable', async ({ page }) => {
    // Intercept status.json and ensure asx_futures is null
    await page.route('**/data/status.json', async route => {
      const response = await route.fetch();
      const json = await response.json();
      // Ensure no asx_futures data
      json.asx_futures = null;
      await route.fulfill({ json });
    });

    await page.goto('/');

    // Wait for gauges to render (proves page loaded)
    const heroPlot = page.locator('#hero-gauge-plot');
    await expect(heroPlot).toBeVisible({ timeout: 15000 });

    // ASX futures container should be visible (always shown) with placeholder text
    const asxContainer = page.locator('#asx-futures-container');
    await expect(asxContainer).toBeVisible();
    await expect(asxContainer).toContainText('Market futures data currently unavailable');
  });

});
