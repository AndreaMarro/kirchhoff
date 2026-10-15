import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";

test("le evidenze conducono al passo analitico corretto anche se già corrente", async ({ page }, info) => {
  await page.goto("/?view=proof#exercise=scala-tre-riduzioni&step=1&frame=after");
  await page.getByText("Perché fidarsi", { exact: true }).click();
  const first = page.getByRole("button", { name: "D1 — Riferimento · passo 4", exact: true });
  await expect(first).toBeVisible();
  await first.focus();
  await page.keyboard.press("Enter");
  const detail = page.getByRole("region", { name: "Dettaglio del passo", exact: true });
  await expect(detail).toBeFocused();
  await expect(detail).toContainText("Passo analitico 4");
  await expect(detail.getByRole("heading", { name: "Riferimento", exact: true })).toBeVisible();
  await expect(page.locator('.kf-rail-step[aria-current="true"]')).toContainText("Riferimento");
  await expect(page).toHaveURL(/step=3&frame=before/);
  // Stesso passo: non basta un effetto che dipende solo dall'indice.
  await first.focus();
  await page.keyboard.press("Space");
  await expect(detail).toBeFocused();
  await page.getByRole("button", { name: "D2 — Incognite nodali · passo 5", exact: true }).click();
  await expect(detail).toBeFocused();
  await expect(detail).toContainText("Passo analitico 5");
  await expect(page).toHaveURL(/step=4&frame=before/);
  expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
  await page.screenshot({ path: info.outputPath("claim-derivazione-passo.png") });
});

test("una derivazione KCL mostra le equazioni proiettate dal kernel", async ({ page }, info) => {
  const payload = JSON.parse(readFileSync(new URL("../public/sessions/ponte-nodale.json", import.meta.url), "utf8"));
  await page.goto("/?view=proof#exercise=ponte-nodale&step=0&frame=before");
  await page.getByText("Perché fidarsi", { exact: true }).click();
  const link = page.getByRole("button", { name: "D3 — KCL al nodo · passo 3", exact: true });
  await expect(link).toBeVisible();
  await link.click();
  const detail = page.getByRole("region", { name: "Dettaglio del passo", exact: true });
  await expect(detail).toBeFocused();
  await expect(detail).toContainText("Passo analitico 3");
  await expect(detail.locator(".kf-equation")).toHaveText(payload.steps[2].equation);
  await expect(page).toHaveURL(/step=2&frame=before/);
  await page.screenshot({ path: info.outputPath("claim-equazione-kcl.png") });
});

test("una vista legacy dichiara il collegamento non esposto senza inventare link", async ({ page }) => {
  await page.route("**/sessions/partitore-d1.json", async route => {
    const response = await route.fetch();
    const payload = await response.json();
    for (const step of payload.steps) delete step.derivation_ref;
    await route.fulfill({ response, json: payload });
  });
  await page.goto("/?view=proof");
  await page.getByText("Perché fidarsi", { exact: true }).click();
  await expect(page.getByText("Questa sessione non espone il collegamento tra derivazione e passo.", { exact: true })).toBeVisible();
  await expect(page.locator(".kf-evidence button")).toHaveCount(0);
  await expect(page.locator(".kf-answer-exact")).toContainText("3/80");
});

test("un mapping esposto ma incoerente non mostra una risposta certificata", async ({ page }) => {
  await page.route("**/sessions/partitore-d1.json", async route => {
    const response = await route.fetch();
    const payload = await response.json();
    for (const step of payload.steps) step.derivation_ref = null;
    await route.fulfill({ response, json: payload });
  });
  await page.goto("/?view=proof");
  await expect(page.getByRole("heading", { name: "Impossibile caricare la sessione" })).toBeVisible();
  await expect(page.locator(".kf-answer-exact")).toHaveCount(0);
  await expect(page.locator(".kf-evidence button")).toHaveCount(0);
});

test("la navigazione tratta come opachi gli identificatori delle derivazioni", async ({ page }) => {
  await page.route("**/sessions/scala-tre-riduzioni.json", async route => {
    const response = await route.fetch();
    const payload = await response.json();
    payload.verification.evidence_ids = ["origine-alfa", "derivazione-omega"];
    for (const step of payload.steps) {
      step.derivation_ref = step.index === 3 ? "origine-alfa" : step.index === 4 ? "derivazione-omega" : null;
    }
    await route.fulfill({ response, json: payload });
  });
  await page.goto("/?view=proof#exercise=scala-tre-riduzioni&step=0&frame=after");
  await page.getByText("Perché fidarsi", { exact: true }).click();
  const link = page.getByRole("button", { name: "derivazione-omega — Incognite nodali · passo 5", exact: true });
  await expect(link).toBeVisible();
  await link.click();
  const detail = page.getByRole("region", { name: "Dettaglio del passo", exact: true });
  await expect(detail).toBeFocused();
  await expect(detail).toContainText("Passo analitico 5");
  await expect(detail.getByRole("heading", { name: "Incognite nodali", exact: true })).toBeVisible();
  await expect(page).toHaveURL(/step=4&frame=before/);
});
