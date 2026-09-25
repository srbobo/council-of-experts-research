import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

test.describe("story page", () => {
  test("loads with hero, all four parts, and thirteen findings", async ({ page }) => {
    await page.goto("/index.html");
    await expect(page).toHaveTitle(/Council of Experts/);
    await expect(page.getByRole("heading", { level: 1 })).toContainText(
      "panel of AI experts",
    );
    await expect(page.locator(".steps .step")).toHaveCount(13);
    for (const heading of [
      "A council of experts",
      "The bet",
      "We stopped chasing",
      "The Harness",
    ]) {
      await expect(
        page.getByRole("heading", { name: new RegExp(heading) }),
      ).toBeVisible();
    }
  });

  test("scrolling a later finding reveals more harness pieces", async ({ page }) => {
    await page.goto("/index.html");
    const onCount = () => page.locator(".rail [data-piece].on").count();
    await page.locator(".steps .step").first().scrollIntoViewIfNeeded();
    await page.waitForTimeout(500);
    const early = await onCount();
    await page.locator(".steps .step").nth(9).scrollIntoViewIfNeeded();
    await page.waitForTimeout(700);
    const later = await onCount();
    expect(later).toBeGreaterThan(early);
    await expect(page.locator(".steps .step").nth(9)).toHaveClass(/is-active/);
  });

  test("reduced motion still shows every finding readable", async ({ browser }) => {
    const ctx = await browser.newContext({ reducedMotion: "reduce" });
    const page = await ctx.newPage();
    await page.goto("/index.html");
    for (const step of await page.locator(".steps .step").all()) {
      await expect(step).toBeVisible();
    }
    await ctx.close();
  });

  test("has no serious or critical accessibility violations", async ({ page }) => {
    await page.goto("/index.html");
    const results = await new AxeBuilder({ page }).analyze();
    const serious = results.violations.filter((v) =>
      ["serious", "critical"].includes(v.impact),
    );
    expect(serious, JSON.stringify(serious, null, 1)).toEqual([]);
  });
});

test.describe("experiments page", () => {
  test("renders the full catalog with structured cards", async ({ page }) => {
    await page.goto("/experiments.html");
    await expect(page.locator("#cards .card").first()).toBeVisible();
    const count = await page.locator("#cards .card").count();
    expect(count).toBeGreaterThanOrEqual(30);
    const first = page.locator("#cards .card").first();
    for (const label of [
      "What we asked",
      "What we did",
      "What happened",
      "What it taught us",
    ]) {
      await expect(first.getByText(label)).toBeVisible();
    }
  });

  test("verdict filters narrow the cards and update the count", async ({ page }) => {
    await page.goto("/experiments.html");
    await page.locator("#cards .card").first().waitFor();
    const all = await page.locator("#cards .card").count();
    await page.getByRole("button", { name: "disproven" }).click();
    const filtered = await page.locator("#cards .card").count();
    expect(filtered).toBeGreaterThan(0);
    expect(filtered).toBeLessThan(all);
    await expect(page.locator("#count")).toContainText(`${filtered} of`);
    await page.getByRole("button", { name: "All", exact: true }).click();
    expect(await page.locator("#cards .card").count()).toEqual(all);
  });

  test("catalog prose contains no internal jargon", async ({ page }) => {
    await page.goto("/experiments.html");
    await page.locator("#cards .card").first().waitFor();
    const text = await page.locator("#cards").innerText();
    for (const banned of [
      " cell ",
      "appendix arm",
      "pre-registered",
      "confidence interval",
    ]) {
      expect(text.toLowerCase()).not.toContain(banned);
    }
  });

  test("has no serious or critical accessibility violations", async ({ page }) => {
    await page.goto("/experiments.html");
    await page.locator("#cards .card").first().waitFor();
    const results = await new AxeBuilder({ page }).analyze();
    const serious = results.violations.filter((v) =>
      ["serious", "critical"].includes(v.impact),
    );
    expect(serious, JSON.stringify(serious, null, 1)).toEqual([]);
  });
});
