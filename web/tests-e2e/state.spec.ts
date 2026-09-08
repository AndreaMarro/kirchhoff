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

test("consumata nel prima non resta rivendicata nel dopo", async ({ page }) => {
  // R1 esiste solo nel prima della serie: passando al dopo, il banco
  // non deve piu' dichiararla come selezionata.
  await page.locator(".kf-rail-step").nth(1).click();
  await page.getByRole("button", { name: "R1", exact: true }).click();
  await expect(page.locator('.kf-entity-btn[aria-pressed="true"]')).toContainText("R1");
  await page.getByRole("button", { name: "Dopo", exact: true }).click();
  await expect(page.locator(".kf-stage-caption")).toContainText("dopo");
  await expect(page.locator('.kf-entity-btn[aria-pressed="true"]')).toHaveCount(0);
  await expect(page.locator(".kf-inspector")).not.toContainText("Selezionata");
});

test("preservata resta selezionata fra prima e dopo", async ({ page }) => {
  // V1 esiste in entrambi i fotogrammi: il confronto trattiene la selezione.
  await page.locator(".kf-rail-step").nth(1).click();
  await page.getByRole("button", { name: "V1", exact: true }).click();
  await expect(page.locator('.kf-entity-btn[aria-pressed="true"]')).toContainText("V1");
  await page.getByRole("button", { name: "Dopo", exact: true }).click();
  await expect(page.locator(".kf-stage-caption")).toContainText("dopo");
  await expect(page.locator('.kf-entity-btn[aria-pressed="true"]')).toContainText("V1");
  expect(await page.locator(".kf-stage-frame .kf-selected").count()).toBeGreaterThan(0);
});

test("pre-selezione dell'evidenza nell'altro fotogramma sopravvive", async ({ page }) => {
  // R1R2eq nasce nel dopo: sceglierla da Prima e' l'invito a passare
  // al Dopo, non una selezione stantia da azzerare.
  await page.locator(".kf-rail-step").nth(1).click();
  await page.getByRole("button", { name: "R1R2eq", exact: true }).click();
  await expect(page.locator('.kf-entity-btn[aria-pressed="true"]')).toContainText("R1R2eq");
  await page.getByRole("button", { name: "Dopo", exact: true }).click();
  await expect(page.locator(".kf-stage-caption")).toContainText("dopo");
  await expect(page.locator('.kf-entity-btn[aria-pressed="true"]')).toContainText("R1R2eq");
  expect(await page.locator(".kf-stage-frame .kf-selected").count()).toBeGreaterThan(0);
});

test("cronologia reale: indietro e avanti restano coerenti", async ({ page }) => {
  // A → passo → Dopo → B → passo → indietro → indietro → avanti.
  // A ogni tappa URL, chip, passo, fotogramma, circuito, risposta e
  // selezione devono accordarsi; nessuno stato stantio riemerge.
  await page.locator(".kf-rail-step").nth(1).click();
  await page.getByRole("button", { name: "Dopo", exact: true }).click();
  await page.getByRole("button", { name: "R1", exact: true }).click();
  await expect(page).toHaveURL(/#exercise=partitore-d1&step=0&frame=after/);
  await page.locator(".kf-chip").nth(1).click();
  await page.locator(".kf-rail-step").nth(2).click();
  await expect(page).toHaveURL(/#exercise=scala-due-riduzioni&step=1&frame=before/);
  await expect(page.locator(".kf-stage-caption")).toContainText("prima");
  await expect(page.locator(".kf-answer-exact")).toContainText("6/325");
  await page.goBack();
  await expect(page).toHaveURL(/#exercise=scala-due-riduzioni&step=-1&frame=before/);
  await expect(page.locator('.kf-chip[aria-current="true"]')).toContainText("Scala");
  await expect(page.locator('.kf-rail-step[aria-current="true"]')).toContainText("Apertura");
  await expect(page.locator(".kf-stage-question code").first()).toContainText("corrente di R1");
  await expect(page.locator(".kf-answer-exact")).toContainText("6/325");
  await expect(page.locator('.kf-entity-btn[aria-pressed="true"]')).toHaveCount(0);
  await page.goBack();
  await expect(page).toHaveURL(/#exercise=partitore-d1&step=0&frame=after/);
  await expect(page.locator('.kf-chip[aria-current="true"]')).toContainText("Partitore");
  await expect(page.locator(".kf-stage-caption")).toContainText("dopo");
  await expect(page.locator(".kf-answer-exact")).toContainText("3/80");
  // La selezione R1 era interazione, non stato profondo: indietro non la resuscita.
  await expect(page.locator('.kf-entity-btn[aria-pressed="true"]')).toHaveCount(0);
  await expect(page.locator(".kf-inspector")).not.toContainText("Selezionata");
  await page.goForward();
  await expect(page).toHaveURL(/#exercise=scala-due-riduzioni&step=-1&frame=before/);
  await expect(page.locator('.kf-chip[aria-current="true"]')).toContainText("Scala");
  await expect(page.locator('.kf-rail-step[aria-current="true"]')).toContainText("Apertura");
  await expect(page.locator(".kf-answer-exact")).toContainText("6/325");
  await expect(page.locator('.kf-entity-btn[aria-pressed="true"]')).toHaveCount(0);
});
