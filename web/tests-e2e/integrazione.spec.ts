/* E2E d'integrazione: il banco dentro una pagina ospite, come cornice.
   La pagina ospite e' generata dal test (origine diversa dal banco):
   nessun finto sito di produzione nel codice. Misura, non presume:
   incorniciamento permesso, trabocco, tastiera, copia-link, guasto. */
import { expect, test, type Page } from "@playwright/test";

function ospite(base: string, hash: string, larghezza: number, altezza: number): string {
  return `<!doctype html><html lang="it"><head><meta charset="utf-8">
<title>Ospite finto</title></head><body>
<h1>Pagina ospite finta</h1>
<p>Marcatura ospite: <span id="marcatore-ospite">intatta</span>
(tasti arrivati all'ospite: <span id="tasti-ospite">0</span>)</p>
<script>
window.addEventListener("keydown", () => {
  const el = document.getElementById("tasti-ospite");
  if (el) el.textContent = String(Number(el.textContent) + 1);
});
</script>
<iframe class="kf-ospite" title="Kirchhoff Proof Workbench"
  src="${base}${hash}" width="${larghezza}" height="${altezza}"
  allow="clipboard-read; clipboard-write"></iframe>
</body></html>`;
}

async function incornicia(
  page: Page,
  hash: string,
  larghezza: number,
  altezza: number,
): Promise<void> {
  const base = test.info().project.use.baseURL ?? "http://localhost:4173";
  await page.setContent(ospite(base, hash, larghezza, altezza));
  await expect(page.frameLocator("iframe.kf-ospite").locator(".kf-chip")).toHaveCount(11, {
    timeout: 10_000,
  });
}

async function traboccoCornice(page: Page): Promise<number> {
  return page
    .frameLocator("iframe.kf-ospite")
    .locator("html")
    .evaluate((el) => el.scrollWidth - el.clientWidth);
}

test("incorniciato largo: invarianti d'integrazione", async ({ page }) => {
  const vw = page.viewportSize()?.width ?? 1440;
  await incornicia(page, "#exercise=partitore-d1&step=0&frame=before", Math.min(1120, vw - 16), 720);
  const banco = page.frameLocator("iframe.kf-ospite");
  // Stato profondo via URL della cornice.
  await expect(banco.locator(".kf-stage-caption")).toContainText("prima");
  await expect(banco.locator(".kf-answer-exact")).toContainText("3/80");
  expect(await traboccoCornice(page)).toBeLessThanOrEqual(1);
  // Rail, fotogramma, ispettore raggiungibili dentro la cornice.
  await banco.getByRole("button", { name: "Dopo", exact: true }).click();
  await expect(banco.locator(".kf-stage-caption")).toContainText("dopo");
  await banco.getByText("Perché fidarsi").click();
  await expect(banco.getByText("Claim elettrico:")).toContainText("VERIFIED");
  // Il rifiuto resta deliberato anche incorniciato.
  await banco.locator(".kf-chip").nth(3).click();
  await expect(banco.locator(".kf-notice h2")).toContainText("Non certificata");
  expect(await traboccoCornice(page)).toBeLessThanOrEqual(1);
  // Tema commuta dentro la cornice.
  await banco.getByRole("button", { name: "Cambia tema" }).click();
  await expect(banco.locator("html")).toHaveAttribute("data-theme", "light");
});

test("incorniciato stretto: resta usabile e senza trabocco", async ({ page }) => {
  await incornicia(page, "#exercise=scala-due-riduzioni&step=1&frame=before", 358, 640);
  const banco = page.frameLocator("iframe.kf-ospite");
  expect(await traboccoCornice(page)).toBeLessThanOrEqual(1);
  await banco.getByRole("button", { name: "Dopo", exact: true }).click();
  await expect(banco.locator(".kf-stage-caption")).toContainText("dopo");
  await expect(banco.locator(".kf-answer-exact")).toContainText("6/325");
  await expect(banco.getByRole("button", { name: "Copia il link a questo passo" })).toBeVisible();
  expect(await traboccoCornice(page)).toBeLessThanOrEqual(1);
});

test("incorniciato: la tastiera resta nel contesto atteso", async ({ page }) => {
  const vw = page.viewportSize()?.width ?? 1440;
  await incornicia(page, "#exercise=partitore-d1&step=-1&frame=before", Math.min(1120, vw - 16), 720);
  const banco = page.frameLocator("iframe.kf-ospite");
  // Fuoco dentro la cornice senza attivare comandi: la didascalia non ha gestori.
  await banco.locator(".kf-stage-caption").click();
  await expect(banco.locator('.kf-rail-step[aria-current="true"]')).toContainText("Apertura");
  await page.keyboard.press("ArrowRight");
  await expect(banco.locator('.kf-rail-step[aria-current="true"]')).toContainText("Serie");
  // L'ospite non ha visto il tasto: gli eventi restano nella cornice.
  await expect(page.locator("#tasti-ospite")).toContainText("0");
  await expect(page.locator("#marcatore-ospite")).toContainText("intatta");
});

test("incorniciato origine diversa: copia-link resta onesto", async ({ page }) => {
  // Ospite opaco (caso peggiore per gli appunti): il clic non deve
  // rompere il banco né millantare una copia non avvenuta. L'URL copiato,
  // quando la piattaforma lo concede, e' il deep link autonomo del banco
  // (URL della cornice), non l'URL dell'ospite: lo fissa il codice che
  // legge window.location.href dentro la cornice.
  const vw = page.viewportSize()?.width ?? 1440;
  await incornicia(
    page,
    "#exercise=partitore-d1&step=0&frame=after",
    Math.min(1120, vw - 16),
    720,
  );
  const banco = page.frameLocator("iframe.kf-ospite");
  const copiabile = await banco
    .locator("body")
    .evaluate((el) => el.ownerDocument.location.href);
  expect(copiabile).toMatch(/#exercise=partitore-d1&step=0&frame=after/);
  await banco.getByRole("button", { name: "Copia il link a questo passo" }).click();
  await expect(banco.locator(".kf-answer-exact")).toContainText("3/80");
  await expect(banco.locator(".kf-notice-load")).toHaveCount(0);
});

test("incorniciato stessa origine: copia-link consegna il deep link", async ({
  page,
  context,
}) => {
  // Modello stesso-dominio (futuro /kirchhoff/): l'ospite condivide
  // l'origine, gli appunti sono concedibili e la copia riesce.
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.goto("/#exercise=partitore-d1&step=-1&frame=before", {
    waitUntil: "domcontentloaded",
  });
  await page.setContent(
    ospite("", "#exercise=partitore-d1&step=0&frame=after", 1100, 700),
  );
  const banco = page.frameLocator("iframe.kf-ospite");
  await expect(banco.locator(".kf-chip")).toHaveCount(11, { timeout: 10_000 });
  await banco.getByRole("button", { name: "Copia il link a questo passo" }).click();
  await expect(banco.getByRole("button", { name: "Copia il link a questo passo" })).toContainText(
    "Copiato",
  );
  const incollato = await page.evaluate(() => navigator.clipboard.readText());
  expect(incollato).toMatch(/#exercise=partitore-d1&step=0&frame=after/);
});

test("incorniciato: il guasto di trasporto si supera senza ricaricare l'ospite", async ({
  page,
}) => {
  let guasta = true;
  await page.route("**/sessions/scala-due-riduzioni.json", async (route) => {
    if (guasta) await route.abort("failed");
    else await route.continue();
  });
  const vw = page.viewportSize()?.width ?? 1440;
  await incornicia(
    page,
    "#exercise=scala-due-riduzioni&step=-1&frame=before",
    Math.min(1120, vw - 16),
    720,
  );
  const banco = page.frameLocator("iframe.kf-ospite");
  await expect(banco.locator(".kf-notice-load h2")).toContainText(
    "Impossibile caricare la sessione",
  );
  guasta = false;
  await banco.getByRole("button", { name: "Riprova" }).click();
  await expect(banco.locator(".kf-stage-question code").first()).toContainText("corrente di R1");
  await expect(banco.locator(".kf-answer-exact")).toContainText("6/325");
  // L'ospite non e' stato ricaricato: la ripresa e' interna alla cornice.
  await expect(page.locator("#marcatore-ospite")).toContainText("intatta");
});

test.describe("incorniciato tablet", () => {
  test.use({ viewport: { width: 820, height: 900 } });

  test("misura intermedia: usabile e senza trabocco", async ({ page }) => {
    await incornicia(page, "#exercise=ponte-nodale&step=3&frame=before", 780, 700);
    const banco = page.frameLocator("iframe.kf-ospite");
    expect(await traboccoCornice(page)).toBeLessThanOrEqual(1);
    await expect(banco.locator(".kf-stage-question code").first()).toContainText("corrente di R4");
    await banco.locator(".kf-rail-step").nth(4).click();
    await expect(banco.locator(".kf-equation")).toContainText("kcl(b):");
    expect(await traboccoCornice(page)).toBeLessThanOrEqual(1);
  });
});
