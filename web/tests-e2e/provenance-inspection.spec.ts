import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";

const canonical = JSON.parse(readFileSync(new URL("../public/sessions/partitore-d1.json", import.meta.url), "utf8"));
const notice = "Questi metadati sono dichiarati dal produttore; non attestano l’autenticità della sessione.";

test("la provenienza completa del catalogo è leggibile da tastiera e dopo riapertura", async ({ page }, info) => {
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  for (let visit = 0; visit < 2; visit++) {
    if (visit === 0) await page.goto("/?view=proof");
    else await page.reload();
    const summary = page.getByText("Perché fidarsi", { exact: true });
    await summary.focus();
    await page.keyboard.press(visit === 0 ? "Enter" : "Space");
    const origin = page.getByRole("region", { name: "Provenienza dichiarata", exact: true });
    await expect(origin).toBeVisible();
    await expect(origin.locator("dd")).toHaveText([
      canonical.provenance.producer, canonical.provenance.source_sha, canonical.provenance.detail,
    ]);
    await expect(origin).toContainText(notice);
    await expect(origin.locator(".kf-check")).toHaveCount(0);
    await expect(page.locator(".kf-answer-exact")).toContainText("3/80");
    expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
    expect(await origin.evaluate(element => element.scrollWidth > element.clientWidth)).toBe(false);
    await page.screenshot({ path: info.outputPath(`provenienza-catalogo-${visit}.png`), fullPage: true });
  }
  expect(errors).toEqual([]);
});

test("revisioni con lo stesso prefisso restano distinguibili e i metadati opachi sono testo", async ({ page }, info) => {
  const prefix = canonical.provenance.source_sha.slice(0, 12);
  const revisions = [prefix + "a".repeat(28), prefix + "b".repeat(28)];
  let current = revisions[0];
  const producer = "produttore/".repeat(16) + "<img src=x onerror=alert(1)>";
  const detail = "Contesto dichiarato <script>throw new Error('html')</script> & nessun link";
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.route("**/sessions/partitore-d1.json", route => route.fulfill({ json: {
    ...canonical, provenance: { producer, source_sha: current, detail },
  } }));
  for (const revision of revisions) {
    current = revision;
    await page.goto("/?view=proof");
    await page.getByText("Perché fidarsi", { exact: true }).click();
    const origin = page.getByRole("region", { name: "Provenienza dichiarata", exact: true });
    await expect(origin.locator("dd")).toHaveText([producer, revision, detail]);
    await expect(origin.locator("img, script, a, .kf-check")).toHaveCount(0);
    await expect(origin).toContainText(notice);
    expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
    expect(await origin.evaluate(element => element.scrollWidth > element.clientWidth)).toBe(false);
  }
  expect(errors).toEqual([]);
  await page.screenshot({ path: info.outputPath("provenienza-prefisso-comune.png"), fullPage: true });
});

test("la provenienza assente è dichiarata senza inventare un produttore o nascondere il Claim", async ({ page }) => {
  await page.route("**/sessions/partitore-d1.json", route => route.fulfill({ json: { ...canonical, provenance: null } }));
  await page.goto("/?view=proof");
  await page.getByText("Perché fidarsi", { exact: true }).click();
  const origin = page.getByRole("region", { name: "Provenienza dichiarata", exact: true });
  await expect(origin).toContainText("Provenienza non disponibile per questa sessione.");
  await expect(origin.locator("dd, .kf-check")).toHaveCount(0);
  await expect(page.locator(".kf-answer-exact")).toContainText("3/80");
  await expect(page.locator(".kf-evidence-links button")).toHaveCount(canonical.verification.evidence_ids.length);
});

test("i campi vuoti del profilo leggibile hanno un limite esplicito", async ({ page }) => {
  await page.route("**/sessions/partitore-d1.json", route => route.fulfill({ json: {
    ...canonical, provenance: { producer: " \n ", source_sha: "", detail: "\t" },
  } }));
  await page.goto("/?view=proof");
  await page.getByText("Perché fidarsi", { exact: true }).click();
  const origin = page.getByRole("region", { name: "Provenienza dichiarata", exact: true });
  await expect(origin.locator("dd")).toHaveText(["Non dichiarato", "Non dichiarata", "Non dichiarato"]);
  await expect(origin).toContainText(notice);
  await expect(origin.locator(".kf-check")).toHaveCount(0);
  await expect(page.locator(".kf-answer-exact")).toContainText("3/80");
});
