/* E2E del rail: il rail e' navigazione, l'ispettore e' spiegazione.
   Le equazioni grezze non competono con la navigazione. */
import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.goto("/#exercise=ponte-nodale&step=3&frame=before", { waitUntil: "networkidle" });
  await expect(page.locator(".kf-chip")).toHaveCount(4, { timeout: 10_000 });
});

test("il rail non espone equazioni grezze", async ({ page }) => {
  await expect(page.locator(".kf-rail")).toContainText("KCL al nodo");
  await expect(page.locator(".kf-rail")).not.toContainText("node_voltage");
});

test("l'equazione lunga resta disponibile nell'ispettore", async ({ page }) => {
  await page.locator(".kf-rail-step").nth(4).click();
  await expect(page.locator('.kf-rail-step[aria-current="true"]')).toContainText("KCL al nodo");
  await expect(page.locator(".kf-equation")).toContainText("kcl(b):");
  await expect(page.locator(".kf-equation")).toContainText("node_voltage");
});

test("il rail resta contenuto nella sua colonna", async ({ page }) => {
  const rail = page.locator(".kf-rail");
  const direzione = await rail.evaluate((el) => getComputedStyle(el).flexDirection);
  if (direzione === "column") {
    // Colonna desktop: ogni voce resta dentro il riquadro del rail.
    const box = await rail.boundingBox();
    expect(box).not.toBeNull();
    for (const btn of await page.locator(".kf-rail-step").all()) {
      const b = await btn.boundingBox();
      expect(b).not.toBeNull();
      expect(b!.x).toBeGreaterThanOrEqual(box!.x - 1);
      expect(b!.x + b!.width).toBeLessThanOrEqual(box!.x + box!.width + 1);
    }
  } else {
    // Striscia mobile a scorrimento interno: nessuna singola voce
    // e' piu' larga della parte visibile della striscia.
    const visibile = await rail.evaluate((el) => el.clientWidth);
    for (const btn of await page.locator(".kf-rail-step").all()) {
      const b = await btn.boundingBox();
      expect(b).not.toBeNull();
      expect(b!.width).toBeLessThanOrEqual(visibile + 1);
    }
  }
  const trabocco = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(trabocco).toBeLessThanOrEqual(1);
});
