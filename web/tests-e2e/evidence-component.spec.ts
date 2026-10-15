import { expect, test } from "@playwright/test";
import { build } from "vite";
import { fileURLToPath } from "node:url";
import type { Page } from "@playwright/test";

let javascript = "", css = "";
test.beforeAll(async () => {
  // Bundle in memoria delle fonti reali. Nessun dist/public viene scritto o
  // copiato; Vite è già una dipendenza diretta e congelata del progetto.
  const result = await build({
    configFile: false, root: fileURLToPath(new URL("../", import.meta.url)),
    publicDir: false, logLevel: "silent",
    build: {
      write: false, emptyOutDir: false, minify: false,
      rollupOptions: {
        input: fileURLToPath(new URL("./fixtures/WorkbenchHarness.tsx", import.meta.url)),
        output: { format: "iife", name: "WorkbenchTestHarness", inlineDynamicImports: true },
      },
    },
  });
  if (!("output" in result)) throw new Error("Il bundle del harness non è un output finito.");
  for (const entry of result.output) {
    if (entry.type === "chunk" && entry.isEntry) javascript = entry.code;
    if (entry.type === "asset" && entry.fileName.endsWith(".css")) css += String(entry.source);
  }
  if (!javascript) throw new Error("Manca il vero bundle del harness.");
});

async function openHarness(page: Page): Promise<void> {
  await page.route("**/__evidence-harness.js", route => route.fulfill({ contentType: "text/javascript; charset=utf-8", body: javascript }));
  await page.route("**/__evidence-harness.css", route => route.fulfill({ contentType: "text/css; charset=utf-8", body: css }));
  await page.route("**/__evidence-harness", route => route.fulfill({ contentType: "text/html; charset=utf-8", body:
    '<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="/__evidence-harness.css"></head><body><div id="test-root"></div><script src="/__evidence-harness.js"></script></body></html>' }));
  await page.goto("/__evidence-harness");
}

test("il componente attraversa closed, refusal, failure e closed senza hook o prove stantie", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", e => errors.push(e.message));
  await openHarness(page);
  await expect(page.getByRole("region", { name: "Dettaglio del passo" })).toContainText("Passo analitico 4");
  for (let n = 0; n < 2; n++) {
    await page.getByRole("button", { name: "Sessione rifiutata", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Non certificata", exact: true })).toBeVisible();
    await expect(page.locator(".kf-answer-exact, .kf-evidence")).toHaveCount(0);
    await page.getByRole("button", { name: "Sessione guasta", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Guasto", exact: true })).toBeVisible();
    await expect(page.locator(".kf-answer-exact, .kf-evidence")).toHaveCount(0);
    await page.getByRole("button", { name: "Sessione chiusa", exact: true }).click();
    await expect(page.getByRole("region", { name: "Dettaglio del passo" })).toContainText("Passo analitico 4");
  }
  expect(errors).toEqual([]);
});

test("il focus richiesto da un'evidenza non passa a una nuova sessione con lo stesso ID", async ({ page }) => {
  await openHarness(page);
  await page.getByText("Perché fidarsi", { exact: true }).click();
  await page.getByRole("checkbox", { name: "Sostituisci sessione al prossimo salto" }).check();
  const link = page.getByRole("button", { name: "D1 — Riferimento · passo 4", exact: true });
  await expect(link).toBeVisible();
  await link.click();
  await expect(page.locator('.kf-rail-step[aria-current="true"]')).toContainText("Apertura");
  const normalNavigation = page.locator(".kf-rail-step").nth(4);
  await normalNavigation.click();
  await expect(page.getByRole("region", { name: "Dettaglio del passo" })).toContainText("Passo analitico 4");
  await page.evaluate(() => new Promise<void>(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve()))));
  await expect(normalNavigation).toBeFocused();
});

test("una sessione nuova già al target non riceve il focus richiesto dalla precedente", async ({ page }) => {
  await openHarness(page);
  await page.getByText("Perché fidarsi", { exact: true }).click();
  await page.getByRole("checkbox", { name: "Sostituisci sessione al prossimo salto" }).check();
  await page.getByRole("checkbox", { name: "Nuova sessione già al passo richiesto" }).check();
  const link = page.getByRole("button", { name: "D1 — Riferimento · passo 4", exact: true });
  await expect(link).toBeVisible();
  await link.click();
  const detail = page.getByRole("region", { name: "Dettaglio del passo", exact: true });
  await expect(detail).toContainText("Passo analitico 4");
  await expect(detail.getByRole("heading", { name: "KCL al nodo", exact: true })).toBeVisible();
  await page.evaluate(() => new Promise<void>(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve()))));
  await expect(detail).not.toBeFocused();
});
