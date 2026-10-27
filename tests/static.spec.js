// tests/static.spec.js
// Verifies the app works on static hosting (GitHub Pages): served from the
// /ISTQB_app/ sub-path with no Flask backend, using frontend/data/db.json.

import { test, expect } from '@playwright/test';

const PAGES_URL = 'http://localhost:5051/ISTQB_app/';

test.describe('Static hosting (GitHub Pages simulation)', () => {

  test('loads styles and chapters without the backend', async ({ page }) => {
    await page.goto(PAGES_URL);
    await page.waitForSelector('.chapter-card', { timeout: 10000 });
    await expect(page.locator('.chapter-card')).toHaveCount(6);

    // CSS loaded from the relative path (nav is sticky only if style.css applied)
    const navPosition = await page.locator('nav').evaluate(el => getComputedStyle(el).position);
    expect(navPosition).toBe('sticky');

    // Opening a chapter shows content and glossary from static data
    await page.locator('.chapter-card').first().click();
    await expect(page.locator('.study-section-card').first()).toBeVisible();
    await expect(page.locator('.glossary-item').first()).toBeVisible();

    // Returning to list and opening Chapter 4 shows mathematical types
    await page.locator('#back-to-list').click();
    await page.locator('.chapter-card[data-id="4"]').click();
    await expect(page.locator('#math-cheats-section')).toBeVisible();
    await expect(page.locator('.math-cheat-card')).toHaveCount(7);
  });

  test('practice mode works from static data', async ({ page }) => {
    await page.goto(PAGES_URL);
    await page.click('[data-view="practice"]');
    await page.waitForSelector('.option-btn', { timeout: 10000 });

    await page.locator('.option-btn').first().click();
    await expect(page.locator('.option-btn.correct')).toBeVisible();
    await expect(page.locator('#next-btn')).toBeEnabled();
  });

  test('theory card filter and mock exam work from static data', async ({ page }) => {
    await page.goto(PAGES_URL);

    await page.click('[data-view="theory"]');
    await page.waitForSelector('#flip-card', { timeout: 10000 });
    const total = await page.evaluate(() => window.state.theory.filtered.length);
    await page.selectOption('#tc-k-select', 'K3');
    await expect.poll(() => page.evaluate(() => window.state.theory.filtered.length)).toBeLessThan(total);
    const k3Levels = await page.evaluate(() => [...new Set(window.state.theory.filtered.map(c => c.k_level))]);
    expect(k3Levels).toEqual(['K3']);

    await page.click('[data-view="mock"]');
    await page.waitForSelector('.mock-option', { timeout: 10000 });
    const first = page.locator('.mock-option').first();
    const qid = await first.getAttribute('data-qid');
    const label = await first.getAttribute('data-label');
    await first.click();
    expect(await page.evaluate(id => window.state.mock.answers[id], qid)).toBe(label);

    await page.click('#submit-exam');
    await expect(page.locator('.score-banner')).toBeVisible();
    expect(typeof await page.evaluate(() => window.state.mock.score)).toBe('number');
  });

});
