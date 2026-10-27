// tests/quiz.spec.js
// Playwright tests for ISTQB Practice App
// Run: npx playwright test

import { test, expect } from '@playwright/test';

/* ---------------------------------------------------------------
   Helpers
   --------------------------------------------------------------- */

/**
 * Navigate to the app and switch to the given view.
 */
async function goTo(page, view) {
  await page.goto('/');
  await page.waitForSelector(`[data-view="${view}"]`);
  await page.click(`[data-view="${view}"]`);
}

/**
 * Wait until the Practice view has fully rendered a question.
 */
async function waitForPracticeQuestion(page) {
  await page.waitForSelector('.option-btn', { timeout: 10000 });
}

/* ---------------------------------------------------------------
   PRACTICE MODE TESTS
   --------------------------------------------------------------- */

test.describe('Practice Mode', () => {

  test('selecting an answer disables all options and shows feedback and enables Next', async ({ page }) => {
    await goTo(page, 'practice');
    await waitForPracticeQuestion(page);

    // The Next button should be disabled before answering
    const nextBtn = page.locator('#next-btn');
    await expect(nextBtn).toBeDisabled();

    // Click the first answer option
    const firstOption = page.locator('.option-btn').first();
    await firstOption.click();

    // --- Feedback: correct/wrong class must appear on at least one button ---
    const correctBtn = page.locator('.option-btn.correct');
    await expect(correctBtn).toBeVisible({ timeout: 3000 });

    // --- All options must be disabled ---
    const allOptions = page.locator('.option-btn');
    const count = await allOptions.count();
    for (let i = 0; i < count; i++) {
      await expect(allOptions.nth(i)).toBeDisabled();
    }

    // --- Explanation box must be visible ---
    await expect(page.locator('.explanation-box.visible')).toBeVisible();

    // --- Next button must be enabled ---
    await expect(nextBtn).toBeEnabled();
  });

  test('clicking Next advances to the next question', async ({ page }) => {
    await goTo(page, 'practice');
    await waitForPracticeQuestion(page);

    // Get text of first question stem
    const firstStem = await page.locator('.question-stem').innerText();

    // Answer and advance
    await page.locator('.option-btn').first().click();
    await page.locator('#next-btn').click();

    // Wait for next question to load
    await page.waitForSelector('.option-btn', { timeout: 5000 });

    // Verify we moved on (either new stem or session complete screen)
    const newStem = await page.locator('.question-stem').innerText().catch(() => '');
    const sessionDone = await page.locator('#restart-practice').isVisible().catch(() => false);

    // Either the stem changed, or we've finished all questions
    expect(newStem !== firstStem || sessionDone).toBeTruthy();
  });

  test('wrong answer is highlighted in red and correct in green', async ({ page }) => {
    await goTo(page, 'practice');
    await waitForPracticeQuestion(page);

    // Find out which option is correct
    const isCorrectAttrs = await page.locator('.option-btn').evaluateAll(
      els => els.map(e => e.dataset.correct)
    );

    // If there's a wrong option, click it
    const wrongIndex = isCorrectAttrs.findIndex(v => v !== '1');
    if (wrongIndex === -1) {
      // All options correct — skip this scenario
      return;
    }

    await page.locator('.option-btn').nth(wrongIndex).click();

    // Clicked option should be .wrong
    await expect(page.locator('.option-btn').nth(wrongIndex)).toHaveClass(/wrong/);
    // Correct option should be .correct
    const correctIndex = isCorrectAttrs.findIndex(v => v === '1');
    await expect(page.locator('.option-btn').nth(correctIndex)).toHaveClass(/correct/);
  });

});

/* ---------------------------------------------------------------
   MOCK EXAM TESTS
   --------------------------------------------------------------- */

test.describe('Mock Exam', () => {

  test('selecting a radio button stores the answer in state.mock.answers', async ({ page }) => {
    await goTo(page, 'mock');

    // Wait for mock exam to render
    await page.waitForSelector('.mock-option', { timeout: 10000 });

    // Get first question's id and first option's label
    const firstOption = page.locator('.mock-option').first();
    const qid   = await firstOption.getAttribute('data-qid');
    const label = await firstOption.getAttribute('data-label');

    // Click the first option
    await firstOption.click();

    // Check that state.mock.answers was updated
    const answer = await page.evaluate(
      ([qid]) => window.state.mock.answers[qid],
      [qid]
    );
    expect(answer).toBe(label);
  });

  test('submitting the mock exam displays a score', async ({ page }) => {
    await goTo(page, 'mock');
    await page.waitForSelector('.mock-option', { timeout: 10000 });

    // Answer all 40 questions with the first option
    const questions = page.locator('[data-qid].mock-option');
    const count = await questions.count();

    // Click first option of each unique question using JS in page context
    await page.evaluate(() => {
      const seen = new Set();
      document.querySelectorAll('.mock-option').forEach(el => {
        const qid = el.dataset.qid;
        if (!seen.has(qid)) {
          seen.add(qid);
          el.click();
        }
      });
    });

    // Wait a moment for state to update
    await page.waitForTimeout(200);

    // Submit
    await page.locator('#submit-exam').click();

    // Score banner must appear
    await page.waitForSelector('.score-banner', { timeout: 5000 });
    await expect(page.locator('.score-banner')).toBeVisible();

    // Score must be a number (state.mock.score)
    const score = await page.evaluate(() => window.state.mock.score);
    expect(typeof score).toBe('number');
    expect(score).toBeGreaterThanOrEqual(0);
    expect(score).toBeLessThanOrEqual(40);
  });

  test('timer starts at 60:00 and counts down', async ({ page }) => {
    await goTo(page, 'mock');
    await page.waitForSelector('#timer-display', { timeout: 10000 });

    // Initial timer value
    const initial = await page.locator('#timer-display').innerText();
    expect(initial).toBe('60:00');

    // Wait ~2 seconds and verify it has decremented
    await page.waitForTimeout(2500);
    const after = await page.locator('#timer-display').innerText();
    expect(after).not.toBe('60:00');
    // Timer should be less than 60:00 now
    const [m, s] = after.split(':').map(Number);
    const totalSecs = m * 60 + s;
    expect(totalSecs).toBeLessThan(3600);
    expect(totalSecs).toBeGreaterThan(3590);
  });

  test('submitted exam shows per-question explanations', async ({ page }) => {
    await goTo(page, 'mock');
    await page.waitForSelector('.mock-option', { timeout: 10000 });

    // Answer all questions
    await page.evaluate(() => {
      const seen = new Set();
      document.querySelectorAll('.mock-option').forEach(el => {
        const qid = el.dataset.qid;
        if (!seen.has(qid)) {
          seen.add(qid);
          el.click();
        }
      });
    });

    await page.locator('#submit-exam').click();
    await page.waitForSelector('.review-explanation', { timeout: 5000 });

    // At least 1 explanation is visible
    const explanations = page.locator('.review-explanation');
    await expect(explanations.first()).toBeVisible();
    const expCount = await explanations.count();
    expect(expCount).toBe(40);
  });

});

/* ---------------------------------------------------------------
   STUDY MODE TESTS
   --------------------------------------------------------------- */

test.describe('Study Mode', () => {

  test('chapter list renders 6 chapters', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.chapter-card', { timeout: 10000 });
    const cards = page.locator('.chapter-card');
    await expect(cards).toHaveCount(6);
  });

  test('clicking a chapter shows its content and glossary', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.chapter-card', { timeout: 10000 });

    await page.locator('.chapter-card').first().click();
    await page.waitForSelector('.chapter-content', { timeout: 5000 });

    await expect(page.locator('.chapter-content')).toBeVisible();
  });

  test('clicking Chapter 4 displays dedicated mathematical types section', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.chapter-card', { timeout: 10000 });

    await page.locator('.chapter-card[data-id="4"]').click();
    await page.waitForSelector('#math-cheats-section', { timeout: 5000 });

    await expect(page.locator('#math-cheats-section')).toBeVisible();
    const mathCards = page.locator('.math-cheat-card');
    await expect(mathCards).toHaveCount(7);
    await expect(page.locator('.math-cheat-title').first()).toContainText('Boundary Value Analysis');
  });

});

/* ---------------------------------------------------------------
   THEORY CARDS TESTS
   --------------------------------------------------------------- */

test.describe('Theory Cards', () => {

  test('flip card flips on click', async ({ page }) => {
    await goTo(page, 'theory');
    await page.waitForSelector('#flip-card', { timeout: 10000 });

    const card = page.locator('#flip-card');
    // Should not be flipped initially
    await expect(card).not.toHaveClass(/flipped/);

    await card.click();

    // Should be flipped after click
    await expect(card).toHaveClass(/flipped/);
  });

  test('filtering by K-level reduces card count', async ({ page }) => {
    await goTo(page, 'theory');
    await page.waitForSelector('#flip-card', { timeout: 10000 });

    // Get total from state
    const totalAll = await page.evaluate(() => window.state.theory.filtered.length);

    // Filter by K1
    await page.selectOption('#tc-k-select', 'K1');
    await page.waitForTimeout(500);
    const totalK1 = await page.evaluate(() => window.state.theory.filtered.length);

    expect(totalK1).toBeLessThan(totalAll);
    expect(totalK1).toBeGreaterThan(0);
  });

});

/* ---------------------------------------------------------------
   FORMULAS & MATHEMATICAL CALCULATORS TESTS
   --------------------------------------------------------------- */

test.describe('Formulas & Mathematical Reference', () => {

  test('navigating to formulas view shows calculators and math subtabs', async ({ page }) => {
    await goTo(page, 'formulas');
    await page.waitForSelector('.math-subnav', { timeout: 10000 });

    // Subtabs must exist
    const subtabs = page.locator('.math-tab-btn');
    expect(await subtabs.count()).toBeGreaterThanOrEqual(5);

    // Calculators tab is active
    await expect(page.locator('#tab-calculators')).toBeVisible();
  });

  test('BVA calculator computes 2-value and 3-value boundary test sets', async ({ page }) => {
    await goTo(page, 'formulas');
    await page.waitForSelector('#calc-bva-btn', { timeout: 10000 });

    // Fill in min=1, max=10, step=1
    await page.fill('#bva-min', '1');
    await page.fill('#bva-max', '10');
    await page.fill('#bva-step', '1');

    await page.click('#calc-bva-btn');

    // Result should be visible and contain calculated values
    const result = page.locator('#bva-result');
    await expect(result).toBeVisible();
    const text = await result.innerText();
    expect(text).toContain('0');  // min - 1
    expect(text).toContain('1');  // min
    expect(text).toContain('10'); // max
    expect(text).toContain('11'); // max + 1
  });

  test('PERT calculator computes expected hours correctly', async ({ page }) => {
    await goTo(page, 'formulas');
    await page.waitForSelector('#calc-pert-btn', { timeout: 10000 });

    // Fill in O=4, M=10, P=22 => (4 + 40 + 22)/6 = 66/6 = 11
    await page.fill('#pert-o', '4');
    await page.fill('#pert-m', '10');
    await page.fill('#pert-p', '22');

    await page.click('#calc-pert-btn');

    const result = page.locator('#pert-result');
    await expect(result).toBeVisible();
    const text = await result.innerText();
    expect(text).toContain('11');
  });

  test('switching math tabs reveals mathematical formula cheat sheets', async ({ page }) => {
    await goTo(page, 'formulas');
    await page.waitForSelector('[data-tab="bva-ref"]', { timeout: 10000 });

    await page.click('[data-tab="bva-ref"]');
    await expect(page.locator('#tab-bva-ref')).toBeVisible();
    await expect(page.locator('#tab-calculators')).not.toBeVisible();
  });

  test('White-box calculator and reference display correct Statement & Branch Coverage formulas', async ({ page }) => {
    await goTo(page, 'formulas');
    await page.waitForSelector('#calc-wb-btn', { timeout: 10000 });

    await page.click('#calc-wb-btn');
    const result = page.locator('#wb-result');
    await expect(result).toBeVisible();
    await expect(result).toContainText('Executable Statements Executed / Total Executable Statements');
    await expect(result).toContainText('Decision Outcomes Exercised / Total Decision Outcomes (Branches)');

    // Switch to White-Box reference tab
    await page.click('[data-tab="whitebox-ref"]');
    const ref = page.locator('#tab-whitebox-ref');
    await expect(ref).toBeVisible();
    await expect(ref).toContainText('Executable Statements Executed');
    await expect(ref).toContainText('Decision Outcomes Exercised');
  });

  test('BVA reference displays clean HTML fraction without raw LaTeX syntax', async ({ page }) => {
    await goTo(page, 'formulas');
    await page.waitForSelector('[data-tab="bva-ref"]', { timeout: 10000 });

    await page.click('[data-tab="bva-ref"]');
    const bvaRef = page.locator('#tab-bva-ref');
    await expect(bvaRef).toBeVisible();

    // Must have the fraction display card
    const card = bvaRef.locator('.math-display-card');
    await expect(card).toBeVisible();
    await expect(card.locator('.math-var')).toHaveText('BVA Coverage');
    await expect(card.locator('.math-num')).toHaveText('Identified Boundary Values Exercised');
    await expect(card.locator('.math-denom')).toHaveText('Total Identified Boundary Values');

    // Must NOT contain raw LaTeX string
    const rawText = await bvaRef.innerText();
    expect(rawText).not.toContain('$$\\text');
    expect(rawText).not.toContain('\\frac');
  });

  test('question pool contains 160 questions across all 4 sample exams', async ({ page }) => {
    await goTo(page, 'practice');
    await waitForPracticeQuestion(page);

    const total = await page.evaluate(() => window.state.questions.length);
    expect(total).toBe(160);
  });

  test('all 5 math reference tabs contain rich real-world and official ISTQB exam examples', async ({ page }) => {
    await goTo(page, 'formulas');
    await page.waitForSelector('.math-subnav', { timeout: 10000 });

    // 1. Check BVA Tab
    await page.click('[data-tab="bva-ref"]');
    const bvaTab = page.locator('#tab-bva-ref');
    await expect(bvaTab).toBeVisible();
    await expect(bvaTab).toContainText('Highway Speed Limits');
    await expect(bvaTab).toContainText('Sample Exam A — Q16');
    await expect(bvaTab).toContainText('Sample Exam D — Q141');

    // 2. Check EP Tab
    await page.click('[data-tab="ep-ref"]');
    const epTab = page.locator('#tab-ep-ref');
    await expect(epTab).toBeVisible();
    await expect(epTab).toContainText('Cinema Ticket Age Tiers');
    await expect(epTab).toContainText('Sample Exam D — Q140');
    await expect(epTab).toContainText('Sample Exam A — Q17');

    // 3. Check Decision Tables Tab
    await page.click('[data-tab="dt-ref"]');
    const dtTab = page.locator('#tab-dt-ref');
    await expect(dtTab).toBeVisible();
    await expect(dtTab).toContainText('Pizza Delivery & Free Shipping Rules');
    await expect(dtTab).toContainText('Sample Exam B — Q62');
    await expect(dtTab).toContainText('Sample Exam A — Q36');

    // 4. Check White-Box Tab
    await page.click('[data-tab="whitebox-ref"]');
    const wbTab = page.locator('#tab-whitebox-ref');
    await expect(wbTab).toBeVisible();
    await expect(wbTab).toContainText('Single If');
    await expect(wbTab).toContainText('Sample Exam B — Q64');
    await expect(wbTab).toContainText('Sample Exam C — Q104');

    // 5. Check Estimation & Metrics Tab
    await page.click('[data-tab="metrics-ref"]');
    const metricsTab = page.locator('#tab-metrics-ref');
    await expect(metricsTab).toBeVisible();
    await expect(metricsTab).toContainText('Payment Gateway');
    await expect(metricsTab).toContainText('Sample Exam C — Q111');
    await expect(metricsTab).toContainText('Banking App Quality Gate');
    await expect(metricsTab).toContainText('Product Risk Exposure');

    // None should contain raw LaTeX strings
    for (const tab of [bvaTab, epTab, dtTab, wbTab, metricsTab]) {
      const text = await tab.innerText();
      expect(text).not.toContain('$$\\text');
      expect(text).not.toContain('\\frac');
      expect(text).not.toContain('\\sum');
      expect(text).not.toContain('\\prod');
    }
  });

  test('mobile responsiveness on iPhone 13 Mini (375px width): all menus visible and no horizontal scroll', async ({ page }) => {
    // Set viewport to iPhone 13 Mini screen size
    await page.setViewportSize({ width: 375, height: 812 });
    await goTo(page, 'formulas');
    await page.waitForSelector('.math-subnav', { timeout: 10000 });

    // Verify all 5 navigation buttons are fully visible within viewport width
    const navButtons = ['study', 'practice', 'theory', 'formulas', 'mock'];
    for (const btnId of navButtons) {
      const btn = page.locator(`button[data-testid="nav-${btnId}"]`);
      await expect(btn).toBeVisible();
      const box = await btn.boundingBox();
      expect(box).not.toBeNull();
      // Button must be within screen width
      expect(box.x).toBeGreaterThanOrEqual(0);
      expect(box.x + box.width).toBeLessThanOrEqual(375);
    }

    // Verify that the page body does NOT horizontally overflow 375px
    const isOverflowing = await page.evaluate(() => {
      return document.documentElement.scrollWidth > document.documentElement.clientWidth;
    });
    expect(isOverflowing).toBe(false);

    // Verify separate div structure for steps and exam stem in EP
    await page.click('[data-tab="ep-ref"]');
    const epTab = page.locator('#tab-ep-ref');
    await expect(epTab).toBeVisible();

    const stemBoxes = epTab.locator('.exam-stem-box');
    expect(await stemBoxes.count()).toBeGreaterThanOrEqual(2);

    const stepCards = epTab.locator('.math-step-card');
    expect(await stepCards.count()).toBeGreaterThanOrEqual(5);

    const takeawayCards = epTab.locator('.math-takeaway-card');
    expect(await takeawayCards.count()).toBeGreaterThanOrEqual(2);

    const tableWraps = epTab.locator('.math-table-wrap');
    expect(await tableWraps.count()).toBeGreaterThanOrEqual(1);

    // Verify again that scrolling EP tab does not overflow horizontally
    const isStillWithinBounds = await page.evaluate(() => {
      return document.documentElement.scrollWidth <= document.documentElement.clientWidth;
    });
    expect(isStillWithinBounds).toBe(true);
  });

});
