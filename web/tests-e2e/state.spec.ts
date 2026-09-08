/* E2E delle transizioni di stato: cambi rapidi non devono incrociare le sessioni. */
import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.goto("/", { waitUntil: "networkidle" });
  await expect(page.locator(".kf-chip")).toHaveCount(4, { timeout: 10_000 });
});

test("cambio rapido di esercizio non incrocia le sessioni", async ({ page }) => {
  // La risposta di scala tarda: se l'ordine di risoluzione vincesse su
  // quello di richiesta, scala sovrascriverebbe ponte.
  await page.route("**/sessions/scala-due-riduzioni.json", async (route) => {
    await new Promise((r) => setTimeout(r, 600));
    await route.continue();
  });
  await page.locator(".kf-chip").nth(1).click();
  await page.locator(".kf-chip").nth(2).click();
  await expect(page).toHaveURL(/#exercise=ponte-nodale/);
  await expect(page.locator(".kf-stage-question code").first()).toContainText("corrente di R4");
  // La risposta tardiva di scala arriva ORA: non deve sovrascrivere ponte.
  await page.waitForResponse("**/sessions/scala-due-riduzioni.json");
  await expect(page).toHaveURL(/#exercise=ponte-nodale/);
  await expect(page.locator(".kf-stage-question code").first()).toContainText("corrente di R4");
  await expect(page.locator(".kf-answer-exact")).toContainText("87/425");
});

test("cambio passo non lascia selezioni stantie", async ({ page }) => {  await page.locator(".kf-rail-step").nth(1).click();
  await page.locator('.kf-stage-frame [data-component-id="R1"]').first().click({ force: true });
  await expect(page.locator('.kf-entity-btn[aria-pressed="true"]')).toContainText("R1");
  await page.locator(".kf-rail-step").nth(2).click();
  // R1 non appartiene al passo di riferimento: nessuna selezione rivendicata.
  await expect(page.locator('.kf-entity-btn[aria-pressed="true"]')).toHaveCount(0);
  await expect(page.locator(".kf-inspector")).not.toContainText("Selezionata");
});

test("fotogramma non disponibile si normalizza a prima", async ({ page }) => {
  await page.goto("/#exercise=ponte-nodale&step=2&frame=after", { waitUntil: "networkidle" });
  await expect(page.locator(".kf-chip")).toHaveCount(4, { timeout: 10_000 });
  await expect(page).toHaveURL(/#exercise=ponte-nodale&step=2&frame=before/);
  await expect(page.locator(".kf-stage-caption")).toContainText("prima");
});

test("passo invalido si normalizza all'apertura", async ({ page }) => {
  await page.goto("/#exercise=partitore-d1&step=99&frame=before", { waitUntil: "networkidle" });
  await expect(page.locator(".kf-chip")).toHaveCount(4, { timeout: 10_000 });
  await expect(page.locator('.kf-rail-step[aria-current="true"]')).toContainText("Apertura");
  await expect(page).toHaveURL(/#exercise=partitore-d1&step=-1&frame=before/);
});
