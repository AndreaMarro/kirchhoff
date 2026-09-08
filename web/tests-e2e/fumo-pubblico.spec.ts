/* Fumo pubblico + fumo d'integrazione: gira SOLO con KIRCHHOFF_PUBLIC_URL.
   Produzione: homepage, 3 successi + rifiuto, niente HTTP >= 400, niente
   errori di pagina. Integrazione: l'URL pubblico dentro una cornice ospite
   (origine diversa), tastiera confinata, tema, copia-link onesta.
   Uso post-deploy (vedi docs/post-merge-playbook.md):
   KIRCHHOFF_PUBLIC_URL=https://andreamarro.github.io/kirchhoff/ npm run test:e2e -- fumo-pubblico */
import { expect, test } from "@playwright/test";

const PUB = process.env.KIRCHHOFF_PUBLIC_URL ?? "";
test.skip(!PUB, "fumo pubblico: richiede KIRCHHOFF_PUBLIC_URL");

let errori: string[] = [];
let guasti: string[] = [];

test.beforeEach(async ({ page }) => {
  errori = [];
  guasti = [];
  page.on("pageerror", (e) => errori.push(String(e).slice(0, 200)));
  page.on("response", (r) => {
    if (r.status() >= 400) guasti.push(`${r.status()} ${r.url().slice(0, 120)}`);
  });
});

test.afterEach(() => {
  expect(guasti, `HTTP >= 400 in produzione: ${guasti.join("; ")}`).toEqual([]);
  expect(errori, `errori di pagina in produzione: ${errori.join("; ")}`).toEqual([]);
});

test("pubblico: homepage e 3 successi + rifiuto", async ({ page }) => {
  await page.goto(PUB, { waitUntil: "networkidle" });
  await expect(page.locator(".kf-chip")).toHaveCount(11, { timeout: 20_000 });
  const attesi: Array<[number, string]> = [
    [0, "3/80"],
    [1, "6/325"],
    [2, "87/425"],
  ];
  for (const [n, risposta] of attesi) {
    await page.locator(".kf-chip").nth(n).click();
    await expect(page.locator(".kf-answer-exact")).toContainText(risposta, { timeout: 10_000 });
  }
  await page.locator(".kf-chip").nth(3).click();
  await expect(page.locator(".kf-notice h2")).toContainText("Non certificata", {
    timeout: 10_000,
  });
});

test("pubblico in cornice ospite: carica, tastiera confinata, tema", async ({ page }) => {
  await page.setContent(`<!doctype html><html lang="it"><head><meta charset="utf-8">
<title>Ospite pubblico</title></head><body>
<h1>Ospite</h1>
<iframe id="kf" title="Kirchhoff Proof Workbench" src="${PUB}#exercise=partitore-d1&step=0&frame=before"
  width="1120" height="720" allow="clipboard-read; clipboard-write"></iframe>
<script>
window.__tasti = 0;
window.addEventListener("keydown", () => { window.__tasti += 1; });
</script>
</body></html>`);
  const banco = page.frameLocator("#kf");
  await expect(banco.locator(".kf-chip")).toHaveCount(11, { timeout: 20_000 });
  await expect(banco.locator(".kf-answer-exact")).toContainText("3/80");
  await banco.locator(".kf-stage-caption").click();
  await page.keyboard.press("ArrowRight");
  await expect(banco.locator('.kf-rail-step[aria-current="true"]')).toContainText("Serie");
  expect(await page.evaluate(() => (window as unknown as { __tasti: number }).__tasti)).toBe(0);
  await banco.getByRole("button", { name: "Cambia tema" }).click();
  await expect(banco.locator("html")).toHaveAttribute("data-theme", "light");
  // Copia-link origine diversa: non deve rompere il banco né millantare.
  await banco.getByRole("button", { name: "Copia il link a questo passo" }).click();
  await expect(banco.locator(".kf-answer-exact")).toContainText("3/80");
  await expect(banco.locator(".kf-notice-load")).toHaveCount(0);
});
