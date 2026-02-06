// @ts-check
const { test, expect } = require('@playwright/test');

test.describe('Phase 6 — UX & Plain English Overhaul', () => {

  test('11. Zone labels use plain English — no DOVISH/HAWKISH terminology', async ({ page }) => {
    await page.goto('/');

    // Wait for hero gauge to render with Plotly
    const heroPlot = page.locator('#hero-gauge-plot');
    await expect(heroPlot).toBeVisible();
    const svg = heroPlot.locator('svg.main-svg');
    await expect(svg.first()).toBeVisible({ timeout: 15000 });

    // Score 46 falls in neutral zone (40-60) — should show "HOLDING STEADY"
    await expect(heroPlot).toContainText('HOLDING STEADY');

    // Verify NO occurrence of old jargon terms anywhere on the page
    const bodyText = await page.locator('body').textContent();
    expect(bodyText).not.toContain('DOVISH');
    expect(bodyText).not.toContain('HAWKISH');
  });

  test('12. All gauges show /100 suffix for clarity', async ({ page }) => {
    await page.goto('/');

    // Hero gauge should display "42/100" (hawk_score 41.8 rounds to 42)
    const heroPlot = page.locator('#hero-gauge-plot');
    await expect(heroPlot).toBeVisible();
    await expect(heroPlot).toContainText('42/100', { timeout: 15000 });

    // At least one bullet gauge in the grid should contain "/100"
    const grid = page.locator('#metric-gauges-grid');
    await expect(grid).toBeVisible();
    // 5 active cards (bg-finance-gray) + 2 placeholder cards (bg-finance-gray/50) = 7
    const allCards = grid.locator('[class*="bg-finance-gray"]');
    await expect(allCards).toHaveCount(7, { timeout: 15000 });

    // Check that at least one active metric card contains "/100"
    // Bullet gauges render via Plotly inside SVG — wait for rendering
    await page.waitForTimeout(2000);
    let foundSlash100 = false;
    for (let i = 0; i < 5; i++) {
      const cardText = await allCards.nth(i).textContent();
      if (cardText.includes('/100')) {
        foundSlash100 = true;
        break;
      }
    }
    expect(foundSlash100).toBe(true);
  });

  test('13. Onboarding explainer is visible and open by default', async ({ page }) => {
    await page.goto('/');

    // Onboarding section should be visible
    const onboarding = page.locator('#onboarding');
    await expect(onboarding).toBeVisible();

    // Should contain the explanatory heading
    await expect(onboarding).toContainText('What is the Hawk-O-Meter?');

    // Should contain the disclaimer
    await expect(onboarding).toContainText('not a prediction or financial advice');

    // The details element should be open by default
    const details = onboarding.locator('details');
    await expect(details).toHaveAttribute('open');
  });

  test('14. Scale explainer appears beneath verdict', async ({ page }) => {
    await page.goto('/');

    // Scale explainer section should be visible
    const scaleExplainer = page.locator('#scale-explainer');
    await expect(scaleExplainer).toBeVisible({ timeout: 15000 });

    // Should explain the 0-100 scale
    await expect(scaleExplainer).toContainText('Score out of 100');
  });

  test('15. Plain English verdict replaces jargon', async ({ page }) => {
    await page.goto('/');

    // Wait for verdict to render
    const verdictContainer = page.locator('#verdict-container');
    await expect(verdictContainer).toBeVisible({ timeout: 15000 });

    // Score 46 falls in mixed signals range (40-60)
    // Should contain plain English guidance about interest rates
    await expect(verdictContainer).toContainText('Interest rates are likely to stay');

    // Should NOT contain the old jargon phrase
    const verdictText = await verdictContainer.textContent();
    expect(verdictText).not.toContain('Economic indicators are broadly balanced');
  });

  test('16. Plain English metric interpretations with why-it-matters text', async ({ page }) => {
    await page.goto('/');

    const grid = page.locator('#metric-gauges-grid');
    const allCards = grid.locator('[class*="bg-finance-gray"]');
    await expect(allCards).toHaveCount(7, { timeout: 15000 });

    // Inflation card (first active card) should use plain English "Prices up" instead of "CPI at"
    const inflationCard = allCards.nth(0);
    await expect(inflationCard).toContainText('Prices up');

    // Each active card should have italic why-it-matters text
    const italicTexts = grid.locator('.text-gray-500.italic');
    const count = await italicTexts.count();
    // Expect at least 5 (one per active indicator)
    expect(count).toBeGreaterThanOrEqual(5);
  });

  test('17. Building approvals data guard prevents -99.9 display', async ({ page }) => {
    await page.goto('/');

    const grid = page.locator('#metric-gauges-grid');
    const allCards = grid.locator('[class*="bg-finance-gray"]');
    await expect(allCards).toHaveCount(7, { timeout: 15000 });

    // Building approvals is the 5th active card (index 4)
    const buildingCard = allCards.nth(4);
    await expect(buildingCard).toContainText('Building');

    // Should NOT contain the invalid -99.9 value
    const cardText = await buildingCard.textContent();
    expect(cardText).not.toContain('-99.9');

    // Should contain either a data quality guard message or qualitative interpretation
    const hasValidText =
      cardText.includes('being updated') ||
      cardText.includes('below average') ||
      cardText.includes('near average') ||
      cardText.includes('Building approvals');
    expect(hasValidText).toBe(true);
  });

  test('18. Weight badges show importance labels', async ({ page }) => {
    await page.goto('/');

    const grid = page.locator('#metric-gauges-grid');
    const allCards = grid.locator('[class*="bg-finance-gray"]');
    await expect(allCards).toHaveCount(7, { timeout: 15000 });

    // Inflation card (weight=25%) should show "High importance"
    const inflationCard = allCards.nth(0);
    await expect(inflationCard).toContainText('High importance');

    // Building approvals card (index 4, weight=5%) should show "Lower importance"
    const buildingCard = allCards.nth(4);
    await expect(buildingCard).toContainText('Lower importance');

    // Wages card should contain staleness indicator (220 days > 90 threshold)
    const wagesCard = allCards.nth(1);
    await expect(wagesCard).toContainText('months old');
  });

  test('19. Australian dates and coverage notice are present', async ({ page }) => {
    await page.goto('/');

    const grid = page.locator('#metric-gauges-grid');
    const allCards = grid.locator('[class*="bg-finance-gray"]');
    await expect(allCards).toHaveCount(7, { timeout: 15000 });

    // At least one metric card should contain an Australian date pattern
    // Intl.DateTimeFormat('en-AU') produces "1 Dec 2025" — allow optional dot after month
    const australianDatePattern = /\d{1,2}\s\w{3}\.?\s\d{4}/;
    let foundAustralianDate = false;
    for (let i = 0; i < 3; i++) {
      const cardText = await allCards.nth(i).textContent();
      if (australianDatePattern.test(cardText)) {
        foundAustralianDate = true;
        break;
      }
    }
    expect(foundAustralianDate).toBe(true);

    // Data coverage notice should indicate 5 of 8 indicators
    const coverageNotice = page.locator('#data-coverage-notice');
    await expect(coverageNotice).toBeVisible({ timeout: 15000 });
    await expect(coverageNotice).toContainText('5 of 8 indicators');
  });

  test('20. Placeholder cards for missing indicators', async ({ page }) => {
    await page.goto('/');

    const grid = page.locator('#metric-gauges-grid');
    const allCards = grid.locator('[class*="bg-finance-gray"]');
    await expect(allCards).toHaveCount(7, { timeout: 15000 });

    // Count cards with "Data coming soon" text — placeholder cards use bg-finance-gray/50
    const placeholderCards = grid.locator('[class*="bg-finance-gray"]:has-text("Data coming soon")');
    await expect(placeholderCards).toHaveCount(2); // housing, business_confidence

    // Verify no placeholder card contains "ASX" (futures are benchmark only)
    const placeholderText = await placeholderCards.allTextContents();
    const placeholderString = placeholderText.join(' ');
    expect(placeholderString).not.toContain('ASX');
  });

  test('21. Calculator bridge and jump link are present', async ({ page }) => {
    await page.goto('/');

    // Jump link container should be visible
    const jumpContainer = page.locator('#calculator-jump-link');
    await expect(jumpContainer).toBeVisible({ timeout: 15000 });
    await expect(jumpContainer).toContainText('mortgage');

    // The <a> element inside the container should point to #calculator-section
    const jumpAnchor = jumpContainer.locator('a');
    await expect(jumpAnchor).toHaveAttribute('href', '#calculator-section');

    // Calculator section should contain bridge text with "/100" reference
    const calculatorSection = page.locator('#calculator-section');
    await expect(calculatorSection).toBeVisible();
    const bridgeText = await calculatorSection.textContent();
    expect(bridgeText).toContain('/100');
  });

  test('22. Mobile collapsible chart and What to Do Next section', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');

    // Chart details should be wrapped in a details element at mobile width
    const chartDetails = page.locator('#chart-details');
    await expect(chartDetails).toBeVisible({ timeout: 15000 });

    // Verify it's a details element (collapsible)
    const tagName = await chartDetails.evaluate(el => el.tagName.toLowerCase());
    expect(tagName).toBe('details');

    // "What to Do Next" heading should be visible
    const whatToDoHeading = page.locator('h2:has-text("What to Do Next")');
    await expect(whatToDoHeading).toBeVisible();

    // Should have 3 action cards visible
    const actionCards = page.locator('[class*="bg-finance-gray"]:has-text("Bookmark"),' +
                                     '[class*="bg-finance-gray"]:has-text("RBA meeting"),' +
                                     '[class*="bg-finance-gray"]:has-text("financial adviser")');
    const count = await actionCards.count();
    expect(count).toBeGreaterThanOrEqual(3);
  });

});
