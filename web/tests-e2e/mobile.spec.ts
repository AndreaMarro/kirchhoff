import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.goto("/", { waitUntil: "networkidle" });
  await expect(page.locator(".kf-chip")).toHaveCount(11, { timeout: 10_000 });
});

test("niente scroll orizzontale e flusso a una mano", async ({ page }) => {
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow).toBe(0);
  await page.locator(".kf-chip").nth(1).click();
  await page.locator(".kf-rail-step").nth(2).click();
  await page.getByRole("button", { name: "Dopo", exact: true }).click();
  await expect(page.locator(".kf-stage-caption")).toContainText("dopo");
  await expect(page.locator(".kf-answer-exact")).toContainText("6/325");
  const targets = await page.evaluate(() => {
    let piccoli = 0;
    document.querySelectorAll("button, summary").forEach((el) => {
      const r = el.getBoundingClientRect();
      if (r.width > 0 && (r.width < 44 || r.height < 44)) piccoli++;
    });
    return piccoli;
  });
  expect(targets).toBe(0);
});

test("schermata mobile per il quaderno visuale", async ({ page }, testInfo) => {
  await page.screenshot({ path: testInfo.outputPath("mobile-apertura.png") });
  await page.locator(".kf-chip").nth(3).click();
  await page.screenshot({ path: testInfo.outputPath("mobile-rifiuto.png") });
});
