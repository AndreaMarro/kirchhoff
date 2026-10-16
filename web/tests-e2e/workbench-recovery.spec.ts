import { expect, test } from "@playwright/test";

test("riprova attende il catalogo corrente prima di caricare una sessione", async ({ page }) => {
  let cataloghi = 0;
  let sessioni = 0;
  let rilascia!: () => void;
  const attesa = new Promise<void>((resolve) => { rilascia = resolve; });
  let arrivata!: () => void;
  const catalogoInAttesa = new Promise<void>((resolve) => { arrivata = resolve; });
  await page.route("**/sessions/index.json", async (route) => {
    cataloghi++;
    if (cataloghi === 2) {
      arrivata();
      await attesa;
      await route.fulfill({ status: 503, body: "catalogo non disponibile" });
    } else {
      await route.continue();
    }
  });
  await page.route("**/sessions/partitore-d1.json", async (route) => {
    sessioni++;
    if (sessioni === 1) await route.fulfill({ status: 503, body: "sessione non disponibile" });
    else await route.continue();
  });
  await page.goto("/?view=proof");
  await expect(page.getByRole("alert")).toBeVisible();
  await page.getByRole("button", { name: "Riprova", exact: true }).click();
  await catalogoInAttesa;
  try {
    await expect(page.locator(".kf-center")).toContainText("Caricamento");
    await expect(page.locator(".kf-answer-exact")).toHaveCount(0);
    expect(sessioni).toBe(1);
  } finally {
    rilascia();
  }
  await expect(page.getByRole("alert")).toBeVisible();
  await page.getByText("Dettaglio tecnico", { exact: true }).click();
  await expect(page.locator(".kf-diagnosis")).toContainText("index.json: 503");
  await expect(page.locator(".kf-answer-exact")).toHaveCount(0);
  await page.getByRole("button", { name: "Riprova", exact: true }).click();
  await expect(page.locator(".kf-answer-exact")).toContainText("3/80");
  await expect(page.getByRole("alert")).toHaveCount(0);
});

for (const clipboard of ["negata", "assente"] as const) {
  test(`clipboard ${clipboard}: il link resta recuperabile e il banco utilizzabile`, async ({ page }) => {
    await page.addInitScript((modo) => {
      Object.defineProperty(navigator, "clipboard", {
        configurable: true,
        value: modo === "assente" ? undefined : {
          writeText: () => Promise.reject(new DOMException("Accesso negato", "NotAllowedError")),
        },
      });
    }, clipboard);
    await page.goto("/?view=proof");
    await expect(page.locator(".kf-answer-exact")).toContainText("3/80");
    await page.getByRole("button", { name: "Passo successivo" }).click();
    const link = page.url();
    const copia = page.getByRole("button", { name: "Copia il link a questo passo" });
    await copia.click();
    await expect(page.getByRole("status").filter({ hasText: "Copia non riuscita" })).toBeVisible();
    const manuale = page.getByRole("textbox", { name: "Link da copiare manualmente" });
    await expect(manuale).toHaveValue(link);
    await manuale.focus();
    expect(await manuale.evaluate((input: HTMLInputElement) =>
      input.value.slice(input.selectionStart ?? 0, input.selectionEnd ?? 0),
    )).toBe(link);
    await page.keyboard.press("Shift+ArrowRight");
    await expect(page).toHaveURL(link);
    await expect(manuale).toBeFocused();
    await expect(copia).not.toContainText("Copiato");
    await page.getByRole("button", { name: "Passo successivo" }).click();
    await expect(page).not.toHaveURL(link);
    await expect(manuale).toHaveCount(0);
    await expect(page.locator(".kf-answer-exact")).toContainText("3/80");
  });
}
