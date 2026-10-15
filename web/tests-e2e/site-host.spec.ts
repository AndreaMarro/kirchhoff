/* Misure del guscio ospite reale contro la build di produzione vera.
   Il guscio (web/site-host/) e' servito da un micro-server statico avviato
   dal test; il banco e' la build di produzione (preview su baseURL), salvo
   KIRCHHOFF_WORKBENCH_URL che punta al pubblicato per il fumo post-deploy.
   Misura, non presume: trabocco, doppia barra, tastiera, schermi, CTA. */
import { expect, test, type FrameLocator, type Page } from "@playwright/test";
import { createServer, type Server } from "node:http";
import { readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const GUSCIO = join(dirname(fileURLToPath(import.meta.url)), "..", "site-host");
const TIPI: Record<string, string> = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
};

let guscioUrl = "";
let server: Server | null = null;

test.beforeAll(async () => {
  server = createServer(async (req, res) => {
    try {
      const percorso = req.url?.split("?")[0] ?? "/";
      const file = join(GUSCIO, percorso === "/" ? "index.html" : percorso.slice(1));
      if (!file.startsWith(GUSCIO)) {
        res.writeHead(403);
        res.end();
        return;
      }
      const corpo = await readFile(file);
      const ext = file.slice(file.lastIndexOf("."));
      res.writeHead(200, { "Content-Type": TIPI[ext] ?? "application/octet-stream" });
      res.end(corpo);
    } catch {
      res.writeHead(404);
      res.end();
    }
  });
  await new Promise<void>((done) => server?.listen(0, "127.0.0.1", done));
  const porta = (server?.address() as { port: number }).port;
  guscioUrl = `http://127.0.0.1:${porta}/`;
});

test.afterAll(async () => {
  await new Promise<void>((done) => server?.close(() => done()));
});

function bancoBase(baseURL: string | undefined): string {
  return process.env.KIRCHHOFF_WORKBENCH_URL ?? baseURL ?? "http://localhost:4173";
}

function ospite(banco: string, hash: string): string {
  const url = new URL(banco);
  url.hash = hash;
  const host = new URL(guscioUrl);
  host.searchParams.set("workbench", url.toString());
  return host.toString();
}

async function apriOspite(page: Page, hash: string): Promise<FrameLocator> {
  const base = test.info().project.use.baseURL ?? "http://localhost:4173";
  await page.goto(ospite(bancoBase(base), hash), { waitUntil: "domcontentloaded" });
  // Il guscio non contiene logica elettrica: deve mostrare copia e cornice.
  await expect(page.locator(".site-main h1")).toContainText("davanti ai tuoi occhi");
  await expect(page.locator("#kf-frame")).toBeVisible();
  const banco = page.frameLocator("#kf-frame");
  await expect(banco.locator(".kf-chip")).toHaveCount(11, { timeout: 15_000 });
  return banco;
}

async function traboccoOrizzontale(page: Page): Promise<number> {
  return page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
}

async function traboccoCornice(banco: FrameLocator): Promise<number> {
  return banco
    .locator("html")
    .evaluate((el) => el.scrollWidth - el.clientWidth);
}

test("ospite desktop: cornice 720px tiene rail, palco e ispettore", async ({ page }) => {
  const banco = await apriOspite(page, "#exercise=partitore-d1&step=-1&frame=before");
  expect(await traboccoOrizzontale(page)).toBeLessThanOrEqual(1);
  expect(await traboccoCornice(banco)).toBeLessThanOrEqual(1);
  // Guida d'ingresso in una riga, dentro il banco.
  await expect(banco.locator(".kf-entry-hint")).toContainText("Scegli un esempio");
  // Flusso dei primi 15 secondi: Avanti, Prima/Dopo, risposta, evidenza.
  await banco.getByRole("button", { name: "Passo successivo" }).click();
  await expect(banco.locator(".kf-stage-caption")).toContainText("prima");
  await banco.getByRole("button", { name: "Dopo", exact: true }).click();
  await expect(banco.locator(".kf-stage-caption")).toContainText("dopo");
  await expect(banco.locator(".kf-answer-exact")).toContainText("3/80");
  await banco.getByText("Perché fidarsi").click();
  await expect(banco.getByText("Claim elettrico:")).toContainText("VERIFIED");
  expect(await traboccoCornice(banco)).toBeLessThanOrEqual(1);
  // Tema commuta dentro la cornice ospitata.
  await banco.getByRole("button", { name: "Cambia tema" }).click();
  await expect(banco.locator("html")).toHaveAttribute("data-theme", "light");
});

test("ospite desktop: altezze sotto 720px restano senza trabocco orizzontale", async ({
  page,
}) => {
  const banco = await apriOspite(page, "#exercise=ponte-nodale&step=3&frame=before");
  for (const h of [720, 640, 560]) {
    await page.locator("#kf-frame").evaluate((el, altezza) => {
      (el as HTMLElement).style.height = `${altezza}px`;
    }, h);
    await page.waitForTimeout(150);
    expect(await traboccoCornice(banco)).toBeLessThanOrEqual(1);
    // La rotaia resta azionabile: altezza minore non deve murarla.
    await banco.locator(".kf-rail-step").nth(0).click();
    await expect(banco.locator(".kf-stage-caption")).toContainText("Apertura");
    await banco.locator(".kf-rail-step").nth(4).click();
    await expect(banco.locator(".kf-equation")).toContainText("kcl(b):");
  }
  // Minima sana desktop: 720px (sotto serve scorrimento interno maggiore
  // e l'ispettore scende sotto la piega: usabile, non consigliato).
});

test("ospite desktop: tastiera resta nella cornice, l'ospite non la vede", async ({
  page,
}) => {
  await page.addInitScript(() => {
    (window as unknown as { __tastiOspite: number }).__tastiOspite = 0;
    window.addEventListener("keydown", () => {
      (window as unknown as { __tastiOspite: number }).__tastiOspite += 1;
    });
  });
  const banco = await apriOspite(page, "#exercise=partitore-d1&step=-1&frame=before");
  await banco.locator(".kf-stage-caption").click();
  await page.keyboard.press("ArrowRight");
  await expect(banco.locator('.kf-rail-step[aria-current="true"]')).toContainText("Serie");
  expect(await page.evaluate(() => (window as unknown as { __tastiOspite: number }).__tastiOspite)).toBe(0);
});

test("schermo intero nativo conserva la navigazione; il link dedicato resta iniziale", async ({ page }) => {
  const banco = await apriOspite(page, "#exercise=scala-due-riduzioni&step=1&frame=before");
  const iniziale = await page.locator("#kf-frame").getAttribute("src");
  expect(iniziale).toMatch(/view=proof/);
  expect(iniziale).toMatch(/#exercise=scala-due-riduzioni&step=1&frame=before/);
  expect(await page.locator("#kf-open").getAttribute("href")).toBe(iniziale);
  await expect(page.locator("#kf-open")).toContainText("link iniziale");
  await banco.locator(".kf-chip").nth(7).click();
  await banco.locator(".kf-rail-step").nth(2).click();
  await banco.getByRole("button", { name: "Dopo", exact: true }).click();
  await expect(banco.locator(".kf-answer-exact")).toContainText("2/3");
  const corrente = await banco.locator("html").evaluate(el => el.ownerDocument.location.hash);
  expect(corrente).toMatch(/exercise=scala-tre-riduzioni&step=1&frame=after/);
  expect(await page.locator("#kf-open").getAttribute("href")).toBe(iniziale);
  const riquadro = await page.locator("#kf-fullscreen").boundingBox();
  expect(riquadro?.height ?? 0).toBeGreaterThanOrEqual(44);
  await page.locator("#kf-fullscreen").click();
  await expect.poll(() => page.evaluate(() => document.fullscreenElement?.id)).toBe("kf-frame-wrap");
  await expect(banco.locator(".kf-chip")).toHaveCount(11);
  await expect(banco.locator(".kf-answer-exact")).toContainText("2/3");
  expect(await banco.locator("html").evaluate(el => el.ownerDocument.location.hash)).toBe(corrente);
});

for (const modo of ["assente", "rigetto", "throw"] as const) {
  test(`alternativa ${modo}: richiede il link iniziale e lo dichiara dopo navigazione`, async ({ page }) => {
    const errori: string[] = []; page.on("pageerror", error => errori.push(String(error)));
    await page.addInitScript(modo => {
      if (window !== window.top) return;
      const stato = window as unknown as { __kfOpened: unknown[][] };
      stato.__kfOpened = [];
      Object.defineProperty(window, "open", { configurable: true, value: (...args: unknown[]) => { stato.__kfOpened.push(args); return null; } });
      Object.defineProperty(HTMLElement.prototype, "requestFullscreen", { configurable: true, value: modo === "assente" ? undefined : function () {
        if (modo === "throw") throw new DOMException("Schermo intero negato", "NotAllowedError");
        return Promise.reject(new DOMException("Schermo intero negato", "NotAllowedError"));
      } });
    }, modo);
    const banco = await apriOspite(page, "#exercise=scala-due-riduzioni&step=1&frame=before");
    const iniziale = await page.locator("#kf-frame").getAttribute("src");
    await banco.locator(".kf-chip").nth(9).click();
    await expect(banco.locator(".kf-answer-exact")).toContainText("5/2");
    await page.locator("#kf-fullscreen").click();
    await expect.poll(() => page.evaluate(() => (window as unknown as {__kfOpened: unknown[][]}).__kfOpened.length)).toBe(1);
    const aperto = await page.evaluate(() => (window as unknown as {__kfOpened: unknown[][]}).__kfOpened[0]);
    expect(aperto).toEqual([iniziale, "_blank", "noopener"]);
    await expect(page.locator("#kf-open-note")).toContainText("link iniziale");
    await expect(page.locator("#kf-open-note")).toContainText("Copia link");
    await expect(banco.locator(".kf-answer-exact")).toContainText("5/2");
    expect(errori).toEqual([]);
  });
}

test("URL con query conserva gli altri parametri e apre proof, ingresso normale resta studente", async ({ page }) => {
  const raw = new URL(bancoBase(test.info().project.use.baseURL));
  raw.searchParams.set("sentinella", "conservata"); raw.searchParams.set("view", "student");
  await page.goto(ospite(raw.toString(), "#exercise=generatore-flottante&step=-1&frame=before"));
  const src = new URL((await page.locator("#kf-frame").getAttribute("src"))!);
  expect(src.searchParams.get("sentinella")).toBe("conservata"); expect(src.searchParams.get("view")).toBe("proof");
  await expect(page.frameLocator("#kf-frame").locator(".kf-answer-exact")).toContainText("5/2");
  await page.goto("/"); await expect(page.locator(".student-app")).toBeVisible(); await expect(page.locator(".kf-picker")).toHaveCount(0);
});

test("ospite desktop: intestazione appiccicosa non copre la cornice", async ({ page }) => {
  await apriOspite(page, "#exercise=partitore-d1&step=-1&frame=before");
  await page.locator("#kf-frame").scrollIntoViewIfNeeded();
  // Il centro e la barra in alto devono restare raggiungibili dopo lo scroll.
  const accessi = await page.locator("#kf-frame").evaluate((el) => {
    const r = el.getBoundingClientRect();
    const libero = (y: number) => { const trovato = document.elementFromPoint(r.x + r.width / 2, y); return trovato === el || el.contains(trovato); };
    return { centro: libero(r.y + Math.min(200, r.height / 2)), barraInAlto: libero(r.y + 20) };
  });
  expect(accessi.centro).toBe(true);
  expect(accessi.barraInAlto, "l'intestazione non deve intercettare i comandi in alto nel banco").toBe(true);
});

test("ospite desktop: guasto di trasporto senza ricaricare l'ospite", async ({ page }) => {
  let guasta = true;
  await page.route("**/sessions/scala-due-riduzioni.json", async (route) => {
    if (guasta) await route.abort("failed");
    else await route.continue();
  });
  await page.addInitScript(() => {
    (window as unknown as { __ospiteVivo: string }).__ospiteVivo = "intatto";
  });
  const banco = await apriOspite(page, "#exercise=scala-due-riduzioni&step=-1&frame=before");
  await expect(banco.locator(".kf-notice-load h2")).toContainText(
    "Impossibile caricare la sessione",
  );
  await expect(page.locator(".site-main h1")).toContainText("davanti ai tuoi occhi");
  guasta = false;
  await banco.getByRole("button", { name: "Riprova" }).click();
  await expect(banco.locator(".kf-answer-exact")).toContainText("6/325");
  expect(await page.evaluate(() => (window as unknown as { __ospiteVivo: string }).__ospiteVivo)).toBe(
    "intatto",
  );
});

test.describe("ospite tablet", () => {
  test.use({ viewport: { width: 810, height: 1080 } });

  test("misura 780x700: usabile e senza trabocco", async ({ page }) => {
    const banco = await apriOspite(page, "#exercise=ponte-nodale&step=3&frame=before");
    await page.locator("#kf-frame").evaluate((el) => {
      (el as HTMLElement).style.width = "780px";
      (el as HTMLElement).style.height = "700px";
    });
    await page.waitForTimeout(150);
    expect(await traboccoOrizzontale(page)).toBeLessThanOrEqual(1);
    expect(await traboccoCornice(banco)).toBeLessThanOrEqual(1);
    await banco.locator(".kf-rail-step").nth(4).click();
    await expect(banco.locator(".kf-equation")).toContainText("kcl(b):");
    // Il ponte e' via nodale diretta: passi analitici a cornice singola,
    // Dopo onestamente disabilitato (il Prima/Dopo vive sulle riduzioni).
    await expect(banco.getByRole("button", { name: "Dopo", exact: true })).toBeDisabled();
    await expect(banco.locator(".kf-stage-caption")).toContainText("prima");
    await expect(banco.locator(".kf-answer-exact")).toContainText("87/425");
    expect(await traboccoCornice(banco)).toBeLessThanOrEqual(1);
  });
});

test.describe("ospite mobile stretto", () => {
  test.use({ viewport: { width: 360, height: 780 } });

  test("barra iniziale del banco accessibile dopo aver portato la cornice in vista", async ({ page }) => {
    const banco = await apriOspite(page, "#exercise=scala-due-riduzioni&step=0&frame=after");
    await expect(banco.locator(".kf-answer-exact")).toContainText("6/325");
    // Stato riproducibile: contenuto caricato e pagina riportata all'ingresso.
    await page.evaluate(() => window.scrollTo(0, 0));
    await expect.poll(() => page.evaluate(() => window.scrollY)).toBe(0);
    await page.locator("#kf-frame").scrollIntoViewIfNeeded();
    const top = await page.locator("#kf-frame").evaluate(el => {
      const r = el.getBoundingClientRect();
      return { y: r.y + 20, inside: r.y + 20 >= 0 && r.y + 20 < innerHeight,
        hit: document.elementFromPoint(r.x + r.width / 2, r.y + 20) === el };
    });
    expect(top.inside).toBe(true);
    expect(top.hit, "la barra del banco non deve essere coperta dall'intestazione mobile").toBe(true);
  });

  test("misura 360px: cornice fluida, niente trabocco, bersagli a una mano", async ({
    page,
  }) => {
    const banco = await apriOspite(page, "#exercise=scala-due-riduzioni&step=-1&frame=before");
    expect(await traboccoOrizzontale(page)).toBeLessThanOrEqual(1);
    expect(await traboccoCornice(banco)).toBeLessThanOrEqual(1);
    await expect(banco.locator(".kf-entry-hint")).toContainText("Scegli un esempio");
    await banco.getByRole("button", { name: "Passo successivo" }).click();
    await banco.getByRole("button", { name: "Dopo", exact: true }).click();
    await expect(banco.locator(".kf-answer-exact")).toContainText("6/325");
    // Bersagli dentro la cornice: niente sotto 44px.
    const piccoli = await banco
      .locator("body")
      .evaluate((el) => {
        let n = 0;
        el.querySelectorAll("button, summary").forEach((b) => {
          const r = (b as HTMLElement).getBoundingClientRect();
          if (r.width > 0 && (r.width < 44 || r.height < 44)) n += 1;
        });
        return n;
      });
    expect(piccoli).toBe(0);
    // Le CTA dell'ospite restano raggiungibili e oneste.
    await expect(page.locator("#kf-fullscreen")).toBeVisible();
    const src = await page.locator("#kf-frame").getAttribute("src");
    expect(await page.locator("#kf-open").getAttribute("href")).toBe(src);
    expect(await traboccoOrizzontale(page)).toBeLessThanOrEqual(1);
  });
});
