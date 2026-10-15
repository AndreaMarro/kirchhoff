import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";
import type { StudentSessionView } from "../src/session/types.ts";

function payload(id: string): StudentSessionView {
  return JSON.parse(readFileSync(new URL(`../public/sessions/${id}.json`, import.meta.url), "utf8"));
}
for (const id of ["partitore-d1", "due-rami-parallelo"]) {
  test(`la giustificazione canonica ${id} si apre con tastiera e conserva i fotogrammi`, async ({ page }, info) => {
    const source = payload(id), why = source.steps[0].justification;
    expect(why, "catalogo rigenerato dal nuovo produttore").toBeTruthy();
    if (!why) throw new Error("Giustificazione assente nel catalogo sotto test");
    const posts: string[] = [];
    page.on("request", r => { if (r.method() === "POST") posts.push(r.url()); });
    await page.goto(`/?view=proof#exercise=${id}&step=0&frame=before`);
    const panel = page.locator(".kf-justification"), summary = panel.locator("summary");
    await expect(summary).toHaveText("Perché posso farlo?");
    await expect(panel).not.toHaveAttribute("open", "");
    const frame = await page.locator(".kf-stage-frame svg").evaluate(e => e.outerHTML);
    await summary.focus(); await page.keyboard.press("Enter");
    await expect(panel).toHaveAttribute("open", "");
    await expect(panel.locator("dt")).toHaveText(["Terminali", "Precondizioni", "Formula", "Certificato"]);
    await expect(panel.locator("dd").nth(0).locator("code")).toHaveText(why.terminals.map(e => e.id));
    await expect(panel.locator("dd").nth(1).locator("li")).toHaveText(why.preconditions);
    await expect(panel.locator("dd").nth(2)).toHaveText(why.formula);
    await expect(panel.locator("dd").nth(3)).toContainText(why.certificate.operation);
    for (const check of why.certificate.checks) await expect(panel).toContainText(check);
    await expect(panel).toContainText("Nessuna attestazione di identità dichiarata.");
    expect(await page.locator(".kf-stage-frame svg").evaluate(e => e.outerHTML)).toBe(frame);
    await page.keyboard.press("Space"); await expect(panel).not.toHaveAttribute("open", "");
    await summary.click(); await expect(panel).toHaveAttribute("open", "");
    await page.getByRole("button", { name: "Dopo", exact: true }).click();
    await expect(page).toHaveURL(/frame=after/);
    await expect(panel.locator("dd").nth(2)).toHaveText(why.formula);
    await page.getByRole("button", { name: "Prima", exact: true }).click();
    expect(await page.locator(".kf-stage-frame svg").evaluate(e => e.outerHTML)).toBe(frame);
    expect(posts).toEqual([]);
    expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
    await panel.scrollIntoViewIfNeeded();
    await page.screenshot({ path: info.outputPath(`giustificazione-${id}.png`), fullPage: true });
  });
}

test("il cambio fra due serie aggiorna la giustificazione e l'analitico non la eredita", async ({ page }) => {
  const source = payload("scala-due-riduzioni");
  const a = source.steps[0].justification, b = source.steps[1].justification;
  expect(a?.formula).toBeTruthy(); expect(a?.formula).not.toBe(b?.formula);
  await page.goto("/?view=proof#exercise=scala-due-riduzioni&step=0&frame=before");
  await page.getByText("Perché posso farlo?", { exact: true }).click();
  await page.getByRole("button", { name: "Passo successivo", exact: true }).click();
  const panel = page.locator(".kf-justification");
  await expect(panel.locator("dd").nth(2)).toHaveText(b!.formula);
  await expect(panel).not.toContainText(a!.formula);
  await page.getByRole("button", { name: "Passo successivo", exact: true }).click();
  await expect(page.getByRole("region", { name: "Dettaglio del passo" })).toContainText("Passo analitico");
  await expect(panel).toHaveCount(0);
});

test("il legacy esplicita il limite e mantiene risposta e derivazioni", async ({ page }) => {
  await page.route("**/sessions/partitore-d1.json", async route => {
    const response = await route.fetch(); const body = await response.json();
    for (const step of body.steps) delete step.justification;
    await route.fulfill({ response, json: body });
  });
  await page.goto("/?view=proof#exercise=partitore-d1&step=0&frame=before");
  await expect(page.getByText("Questa sessione non espone la giustificazione del passo.", { exact: true })).toBeVisible();
  await expect(page.locator(".kf-justification")).toHaveCount(0);
  await expect(page.locator(".kf-answer-exact")).toContainText("3/80");
  await page.getByText("Perché fidarsi", { exact: true }).click();
  await expect(page.locator(".kf-evidence button").first()).toBeVisible();
});

test("una giustificazione incoerente viene rifiutata prima della risposta", async ({ page }) => {
  await page.route("**/sessions/partitore-d1.json", async route => {
    const response = await route.fetch(); const body = await response.json();
    expect(body.steps[0].justification).toBeTruthy();
    body.steps[0].justification.formula = "formula estranea";
    await route.fulfill({ response, json: body });
  });
  await page.goto("/?view=proof");
  await expect(page.getByRole("heading", { name: "Impossibile caricare la sessione" })).toBeVisible();
  await expect(page.locator(".kf-answer-exact, .kf-justification")).toHaveCount(0);
});

test("testo opaco lungo resta inerte e va a capo", async ({ page }, info) => {
  const opaque = '<img src=x onerror="window.k4Injected=1">' + "nodo_opaco_".repeat(28);
  await page.route("**/sessions/partitore-d1.json", async route => {
    const response = await route.fetch(); const body = await response.json(); const p = body.steps[0];
    expect(p.justification).toBeTruthy();
    const old = p.justification.terminals[0].id;
    p.justification.terminals[0].id = opaque;
    p.preserved.find((e: {kind: string; id: string}) => e.kind === "node" && e.id === old).id = opaque;
    p.justification.preconditions[0] = opaque;
    p.justification.certificate.attestations = [{ entity: { kind: "component", id: "V1" }, changed: ["value", "type"] }];
    p.justification.future = "Non e' un quinto campo";
    await route.fulfill({ response, json: body });
  });
  await page.goto("/?view=proof#exercise=partitore-d1&step=0&frame=before");
  await page.getByText("Perché posso farlo?", { exact: true }).click();
  const panel = page.locator(".kf-justification");
  await expect(panel.locator("dt")).toHaveText(["Terminali", "Precondizioni", "Formula", "Certificato"]);
  await expect(panel).toContainText(opaque); await expect(panel).toContainText("value, type");
  await expect(panel.locator("img,script,[onerror]")).toHaveCount(0);
  expect(await page.evaluate(() => Object.hasOwn(window, "k4Injected"))).toBe(false);
  expect(await panel.evaluate(e => e.scrollWidth > e.clientWidth)).toBe(false);
  expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
  await expect(panel).not.toContainText("Non e' un quinto campo");
  await panel.scrollIntoViewIfNeeded();
  await page.screenshot({ path: info.outputPath("giustificazione-opaca.png"), fullPage: true });
});
