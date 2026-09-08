/* E2E del banco: comportamento osservabile, mai dettagli d'implementazione.
   Gira sulla build di produzione servita in locale. */
import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.goto("/", { waitUntil: "networkidle" });
  await expect(page.locator(".kf-chip")).toHaveCount(4, { timeout: 10_000 });
});

test("scelta esercizio e navigazione della dimostrazione", async ({ page }) => {
  await expect(page.locator(".kf-stage-question code").first()).toContainText("corrente di R1");
  await page.locator(".kf-chip").nth(1).click();
  await expect(page.locator(".kf-stage-question code").first()).toContainText("corrente di R1");
  await expect(page).toHaveURL(/#exercise=scala-due-riduzioni/);
  await page.getByRole("button", { name: "Passo successivo" }).click();
  await expect(page.locator('.kf-rail-step[aria-current="true"]')).toContainText("Serie");
  await page.getByRole("button", { name: "Passo precedente" }).click();
  await expect(page.locator('.kf-rail-step[aria-current="true"]')).toContainText("Apertura");
});

test("prima/dopo commuta il fotogramma", async ({ page }) => {
  await page.locator(".kf-rail-step").nth(1).click();
  await page.getByRole("button", { name: "Dopo", exact: true }).click();
  await expect(page.locator(".kf-stage-caption")).toContainText("dopo");
  await expect(page).toHaveURL(/frame=after/);
  await page.getByRole("button", { name: "Prima", exact: true }).click();
  await expect(page.locator(".kf-stage-caption")).toContainText("prima");
});

test("il preservato non si teletrasporta fra prima e dopo", async ({ page }) => {
  await page.locator(".kf-rail-step").nth(1).click();
  const nodo = '.kf-stage-frame circle[data-node-id="b"]';
  const prima = await page.locator(nodo).boundingBox();
  expect(prima).not.toBeNull();
  await page.getByRole("button", { name: "Dopo", exact: true }).click();
  const dopo = await page.locator(nodo).boundingBox();
  expect(dopo).not.toBeNull();
  const cx = (b: { x: number; width: number }): number => b.x + b.width / 2;
  const cy = (b: { y: number; height: number }): number => b.y + b.height / 2;
  expect(Math.abs(cx(prima!) - cx(dopo!))).toBeLessThan(2);
  expect(Math.abs(cy(prima!) - cy(dopo!))).toBeLessThan(2);
  expect(Math.abs(prima!.width - dopo!.width)).toBeLessThan(2);
});

test("click sull'entita' la evidenzia e la contestualizza", async ({ page }) => {
  await page.locator(".kf-rail-step").nth(1).click();
  // force: i tratti SVG sono sottili e il punto centrale del riquadro
  // puo' cadere sul vuoto; il fallback di prossimita' risolve comunque.
  await page.locator('.kf-stage-frame [data-component-id="R1"]').first().click({ force: true });
  await expect(page.locator('.kf-entity-btn[aria-pressed="true"]')).toContainText("R1");
  expect(await page.locator(".kf-stage-frame .kf-selected").count()).toBeGreaterThan(0);
});

test("la tastiera attraversa il flusso essenziale", async ({ page }) => {
  await page.keyboard.press("ArrowRight");
  await expect(page.locator('.kf-rail-step[aria-current="true"]')).toContainText("Serie");
  await page.keyboard.press("a");
  await expect(page.locator(".kf-stage-caption")).toContainText("dopo");
  await page.keyboard.press("b");
  await expect(page.locator(".kf-stage-caption")).toContainText("prima");
  await page.keyboard.press("ArrowLeft");
  await expect(page.locator('.kf-rail-step[aria-current="true"]')).toContainText("Apertura");
});

test("l'evidenza si ispeziona su richiesta", async ({ page }) => {
  await page.getByText("Perché fidarsi").click();
  await expect(page.getByText("Claim elettrico:")).toContainText("VERIFIED");
  await expect(page.getByText("Sessione backend:")).toContainText("CLOSED");
});

test("il rifiuto e' deliberato e senza risposta", async ({ page }) => {
  await page.locator(".kf-chip").nth(3).click();
  await expect(page.locator(".kf-notice h2")).toContainText("Non certificata");
  await expect(page.locator(".kf-answer-exact")).toHaveCount(0);
  await expect(page.locator(".kf-notice-refusal .kf-tech summary")).toContainText(
    "Dettaglio tecnico",
  );
  await page.locator(".kf-notice-refusal .kf-tech summary").click();
  await expect(page.locator(".kf-diagnosis")).toContainText("nessuna tecnica eseguibile");
});

test("il link al passo si copia", async ({ page, context }) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.locator(".kf-rail-step").nth(1).click();
  await page.getByRole("button", { name: "Copia il link a questo passo" }).click();
  await expect(page.getByRole("button", { name: "Copia il link a questo passo" })).toContainText(
    "Copiato",
  );
  const incollato = await page.evaluate(() => navigator.clipboard.readText());
  expect(incollato).toMatch(/#exercise=partitore-d1&step=\d+&frame=(before|after)/);
});

test("l'esatto comanda, il decimale accompagna", async ({ page }) => {
  await expect(page.locator(".kf-answer-exact")).toContainText("3/80");
  await expect(page.locator(".kf-answer-decimal")).toContainText("0.0375");
  await expect(page.locator("body")).not.toContainText("Product Verified");
});

test("il refresh non perde il passo", async ({ page }) => {
  await page.locator(".kf-chip").nth(1).click();
  await page.locator(".kf-rail-step").nth(2).click();
  await page.getByRole("button", { name: "Dopo", exact: true }).click();
  await page.reload({ waitUntil: "networkidle" });
  await expect(page.locator(".kf-stage-caption")).toContainText("dopo");
  await expect(page).toHaveURL(/#exercise=scala-due-riduzioni/);
});

test("il tema commuta e persiste", async ({ page }) => {
  await page.getByRole("button", { name: "Cambia tema" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.reload({ waitUntil: "networkidle" });
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.getByRole("button", { name: "Cambia tema" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
});

test("il fuoco da tastiera e' visibile", async ({ page }) => {
  await page.keyboard.press("Tab");
  const focused = page.locator(":focus");
  await expect(focused).toBeVisible();
  const ring = await focused.evaluate((el) => getComputedStyle(el).boxShadow);
  expect(ring).not.toBe("none");
});

function luminanza(rgb: string): number {
  const m = rgb.match(/[\d.]+/g)?.map(Number) ?? [0, 0, 0];
  const [r, g, b] = m.slice(0, 3).map((v) => {
    const s = v / 255;
    return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

test("il contrasto del testo principale regge AA", async ({ page }) => {
  const ratio = await page.evaluate(() => {
    const fg = getComputedStyle(document.querySelector(".kf-answer-exact")!).color;
    const bg = getComputedStyle(document.querySelector(".kf-answer")!).backgroundColor;
    return { fg, bg };
  });
  const l1 = luminanza(ratio.fg);
  const l2 = luminanza(ratio.bg);
  const contrasto = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
  expect(contrasto).toBeGreaterThanOrEqual(4.5);
});

test("schermate per il quaderno visuale", async ({ page }, testInfo) => {
  await page.screenshot({ path: testInfo.outputPath("desktop-apertura.png") });
  await page.locator(".kf-rail-step").nth(1).click();
  await page.getByRole("button", { name: "Dopo", exact: true }).click();
  await page.screenshot({ path: testInfo.outputPath("desktop-trasformazione.png") });
  await page.locator(".kf-chip").nth(3).click();
  await page.screenshot({ path: testInfo.outputPath("desktop-rifiuto.png") });
});
