/* E2E del guasto di trasporto: la sessione che non arriva non e' un
   rifiuto del motore né un guasto di dominio. Si dichiara come mancato
   caricamento e si supera senza ricaricare la pagina. */
import { expect, test } from "@playwright/test";

test("carico fallito poi esercizio sano: la vista sana diventa autorevole", async ({
  page,
}) => {
  await page.goto("/", { waitUntil: "networkidle" });
  await expect(page.locator(".kf-chip")).toHaveCount(11, { timeout: 10_000 });
  // Solo scala cade in trasporto; il resto resta sano.
  await page.route("**/sessions/scala-due-riduzioni.json", async (route) => {
    await route.abort("failed");
  });
  await page.locator(".kf-chip").nth(1).click();
  // Fallimento comprensibile, senza semantica di dominio.
  await expect(page.locator(".kf-notice-load h2")).toContainText(
    "Impossibile caricare la sessione",
  );
  await expect(page.locator("main")).not.toContainText("Guasto");
  await expect(page.locator("main")).not.toContainText("Non certificata");
  await expect(page.locator(".kf-answer-exact")).toHaveCount(0);
  // Passaggio a un esercizio sano: recupero senza ricaricare la pagina.
  await page.locator(".kf-chip").nth(2).click();
  await expect(page.locator(".kf-stage-question code").first()).toContainText("corrente di R4");
  await expect(page.locator(".kf-answer-exact")).toContainText("87/425");
  // L'errore stantio sparisce: la sessione sana e' l'unica vista autorevole.
  await expect(page.locator(".kf-notice-load")).toHaveCount(0);
  await expect(page.locator("main")).not.toContainText("Impossibile caricare");
});

test("errore tardivo della vecchia richiesta non sovrascrive la sessione sana", async ({
  page,
}) => {
  await page.goto("/", { waitUntil: "networkidle" });
  await expect(page.locator(".kf-chip")).toHaveCount(11, { timeout: 10_000 });
  // Partitore cade lentamente: il cambio rapido lo rende stantio prima
  // che il suo errore arrivi.
  await page.route("**/sessions/partitore-d1.json", async (route) => {
    await new Promise((r) => setTimeout(r, 600));
    await route.abort("failed");
  });
  const fallita = page.waitForEvent("requestfailed", (r) =>
    r.url().includes("partitore-d1.json"),
  );
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.locator(".kf-chip").nth(2).click();
  await expect(page.locator(".kf-stage-question code").first()).toContainText("corrente di R4");
  // L'errore tardivo di partitore arriva ORA: non deve contaminare ponte.
  await fallita;
  await expect(page).toHaveURL(/#exercise=ponte-nodale/);
  await expect(page.locator(".kf-stage-question code").first()).toContainText("corrente di R4");
  await expect(page.locator(".kf-answer-exact")).toContainText("87/425");
  await expect(page.locator(".kf-notice-load")).toHaveCount(0);
});

test("riprova dopo il guasto di trasporto, senza cambiare esercizio", async ({ page }) => {
  let guasta = true;
  await page.route("**/sessions/partitore-d1.json", async (route) => {
    if (guasta) await route.abort("failed");
    else await route.continue();
  });
  await page.goto("/", { waitUntil: "networkidle" });
  await expect(page.locator(".kf-notice-load h2")).toContainText(
    "Impossibile caricare la sessione",
  );
  guasta = false;
  await page.getByRole("button", { name: "Riprova" }).click();
  await expect(page.locator(".kf-stage-question code").first()).toContainText("corrente di R1");
  await expect(page.locator(".kf-answer-exact")).toContainText("3/80");
  await expect(page.locator(".kf-notice-load")).toHaveCount(0);
});
