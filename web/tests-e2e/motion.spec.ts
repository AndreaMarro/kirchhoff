import { expect, test } from "@playwright/test";

test.use({ reducedMotion: "reduce" });

test("moto ridotto: semantica intatta, durate nulle", async ({ page }) => {
  await page.goto("/", { waitUntil: "networkidle" });
  await expect(page.locator(".kf-chip")).toHaveCount(4, { timeout: 10_000 });
  const veloce = await page.evaluate(() =>
    getComputedStyle(document.documentElement).getPropertyValue("--kf-motion-quick").trim(),
  );
  expect(veloce).toBe("0ms");
  await page.locator(".kf-rail-step").nth(1).click();
  await page.getByRole("button", { name: "Dopo", exact: true }).click();
  await expect(page.locator(".kf-stage-caption")).toContainText("dopo");
  await expect(page.locator(".kf-answer-exact")).toContainText("3/80");
});
