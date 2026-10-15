import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { createServer, type Server } from "node:http";
import { cp, mkdir, mkdtemp, readFile, readdir, rm, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { execFile } from "node:child_process";
import { promisify } from "node:util";

const esegui = promisify(execFile);
const web = join(import.meta.dirname, "..");
let directory: string;
let dist: string;
let script: string;
let server: Server;
let base: string;
let remoti: Map<string, Buffer>;
let richieste: string[];

beforeEach(async () => {
  directory = await mkdtemp(join(tmpdir(), "kirchhoff-artifact-cli-"));
  dist = join(directory, "web/dist");
  script = join(directory, "web/scripts");
  // Copia byte-identica degli script veri, eseguiti come CLI con dist fratello.
  // Non si riscrivono import, fetch o filesystem del programma sotto test.
  await cp(join(web, "scripts"), script, { recursive: true });
  remoti = new Map([
    ["index.html", Buffer.from('<html><body><div id="root"></div><script type="module" src="./assets/index-LOCAL.js"></script><link rel="stylesheet" href="./assets/index-LOCAL.css"></body></html>')],
    ["assets/index-LOCAL.js", Buffer.from('import("./lazy.js");')],
    ["assets/index-LOCAL.css", Buffer.from("body{margin:0}")],
    ["assets/lazy.js", Buffer.from('export const value=1;')],
    ["assets/pdf.worker.min.mjs", Buffer.from('/* worker atteso */')],
    ["lessons/index.json", Buffer.from("[]")],
    ["mcp/build-manifest.json", Buffer.from("{}")],
  ]);
  for (const file of await readdir(join(web, "public/sessions"))) {
    if (file.endsWith(".json")) remoti.set("sessions/" + file, await readFile(join(web, "public/sessions", file)));
  }
  for (const [file, bytes] of remoti) {
    await mkdir(join(dist, file, ".."), { recursive: true });
    await writeFile(join(dist, file), bytes);
  }
  richieste = [];
  server = createServer((req, res) => {
    const path = new URL(req.url ?? "/", "http://localhost").pathname;
    richieste.push(path);
    const file = path.startsWith("/beta/") ? path.slice("/beta/".length) || "index.html" : "";
    const bytes = remoti.get(file);
    res.writeHead(bytes ? 200 : 404);
    res.end(bytes ?? "assente");
  });
  await new Promise<void>((done) => server.listen(0, "127.0.0.1", done));
  base = `http://127.0.0.1:${(server.address() as {port: number}).port}/beta/`;
});

afterEach(async () => {
  if (server) { server.closeAllConnections(); await new Promise<void>((done) => server.close(() => done())); }
  if (directory) await rm(directory, { recursive: true, force: true });
});

async function cli(nome: string, args = [base]) {
  try {
    const result = await esegui(process.execPath, [join(script, nome + ".mjs"), ...args], { timeout: 20_000 });
    return { code: 0, stdout: result.stdout, stderr: result.stderr };
  } catch (caught) {
    const error = caught as Error & { code?: string | number; stdout?: string; stderr?: string };
    if (typeof error.code !== "number") throw caught;
    return { code: error.code, stdout: error.stdout ?? "", stderr: error.stderr ?? "" };
  }
}
function cambia(file: string, mutate: (view: {answer: {exact: string; unit: string} | null; verification: unknown; truth: Record<string, unknown>}) => void) {
  const view = JSON.parse(remoti.get(file)!.toString());
  mutate(view);
  remoti.set(file, Buffer.from(JSON.stringify(view)));
}

describe("verifier: build attesa e file realmente serviti", () => {
  it("la build identica verifica tutti i corpi, chunk lazy, worker, lessons e MCP", async () => {
    const r = await cli("verify-artifacts"); expect(r.code).toBe(0);
    for (const path of remoti.keys()) expect(richieste).toContain("/beta/" + path);
  });
  it("un nuovo corpo diverso non può dare MATCH", async () => {
    cambia("sessions/partitore-tensione.json", v => { v.answer!.exact = "999"; });
    const r = await cli("verify-artifacts"); expect(r.code).toBe(1); expect(r.stdout).toContain("partitore-tensione.json");
  });
  it("HTML con entry diversa fallisce anche se il vecchio asset identico è ancora disponibile", async () => {
    remoti.set("index.html", Buffer.from(remoti.get("index.html")!.toString().replace("index-LOCAL.js", "index-REMOTE.js")));
    remoti.set("assets/index-REMOTE.js", Buffer.from("/* codice remoto diverso */"));
    const r = await cli("verify-artifacts"); expect(r.code).toBe(1); expect(r.stdout).toContain("index.html");
  });
  it.each(["sessions/scala-tre-riduzioni.json", "assets/pdf.worker.min.mjs", "assets/lazy.js", "lessons/index.json", "mcp/build-manifest.json"])("assenza di %s fallisce", async (file) => {
    remoti.delete(file); const r = await cli("verify-artifacts"); expect(r.code).toBe(1); expect(r.stdout).toContain(file);
  });
  it("anche i byte di un chunk non indicato nellHTML sono verificati", async () => {
    remoti.set("assets/lazy.js", Buffer.from("export const value=2;"));
    const r = await cli("verify-artifacts"); expect(r.code).toBe(1); expect(r.stdout).toContain("assets/lazy.js");
  });
});

describe("smoke: indice dinamico e coerenza delle viste proof DC", () => {
  it("undici voci sane passano e vengono lette tutte", async () => {
    const r = await cli("smoke-public"); expect(r.code).toBe(0);
    for (const file of remoti.keys()) if (file.startsWith("sessions/")) expect(richieste).toContain("/beta/" + file);
  });
  it("la mancanza di un nuovo corpo è un guasto", async () => {
    remoti.delete("sessions/ramo-derivato.json"); const r = await cli("smoke-public"); expect(r.code).toBe(1); expect(r.stdout).toContain("ramo-derivato");
  });
  it.each(["risposta", "unita", "truth", "verifica", "razionale"])("una chiusura con %s incoerente fallisce", async (caso) => {
    cambia("sessions/partitore-tensione.json", v => {
      if (caso === "risposta") v.answer = null;
      if (caso === "unita") v.answer!.unit = "ampere";
      if (caso === "truth") v.truth.product_verified = true;
      if (caso === "verifica") v.verification = null;
      if (caso === "razionale") v.answer!.exact = "5/0";
    });
    const r = await cli("smoke-public"); expect(r.code).toBe(1); expect(r.stdout).toContain("partitore-tensione");
  });
  it("un rifiuto con risposta non è presentato come onesto", async () => {
    cambia("sessions/rifiuto-domanda.json", v => { v.answer = { exact: "1", unit: "volt" }; });
    const r = await cli("smoke-public"); expect(r.code).toBe(1); expect(r.stdout).toContain("rifiuto-domanda");
  });
  it("identificatori duplicati nellindice falliscono senza ignorare la coda", async () => {
    const index = JSON.parse(remoti.get("sessions/index.json")!.toString()); index.push(index[0]);
    remoti.set("sessions/index.json", Buffer.from(JSON.stringify(index)));
    const r = await cli("smoke-public"); expect(r.code).toBe(1); expect(r.stdout).toContain("indice");
  });
});


describe("argomenti espliciti degli strumenti", () => {
  it.each(["smoke-public", "verify-artifacts"])("%s senza URL termina senza richieste implicite", async (nome) => {
    const r = await cli(nome, []); expect(r.code).toBe(1); expect(r.stdout).toContain("URL base esplicito"); expect(richieste).toEqual([]);
  });
  it.each(["smoke-public", "verify-artifacts"])("%s respinge protocolli diversi da HTTP", async (nome) => {
    const r = await cli(nome, ["file:///build/"]); expect(r.code).toBe(1); expect(richieste).toEqual([]);
  });
  it("verifier usa la directory attesa esplicita anche senza dist di default", async () => {
    const alternativa = join(directory, "build-fissata");
    await cp(dist, alternativa, { recursive: true }); await rm(dist, { recursive: true });
    const r = await cli("verify-artifacts", [base, alternativa]); expect(r.code).toBe(0);
  });
});


describe("regressioni della review sul contratto operativo", () => {
  it("review: rifiuto con chiusura VERIFIED non dà verde", async () => {
    cambia("sessions/rifiuto-domanda.json", v => { v.truth.backend_closure_status = "VERIFIED"; });
    const r = await cli("smoke-public"); expect(r.code).toBe(1); expect(r.stdout).toContain("rifiuto-domanda");
  });
  it("review: denominatore negativo non dà verde", async () => {
    cambia("sessions/partitore-tensione.json", v => { v.answer!.exact = "1/-2"; });
    const r = await cli("smoke-public"); expect(r.code).toBe(1); expect(r.stdout).toContain("partitore-tensione");
  });
  it("review: failure con diagnosis inventato non dà verde", async () => {
    const index = JSON.parse(remoti.get("sessions/index.json")!.toString()) as Array<{id: string; outcome: string}>;
    index.find(e => e.id === "rifiuto-domanda")!.outcome = "failure";
    remoti.set("sessions/index.json", Buffer.from(JSON.stringify(index)));
    const view = JSON.parse(remoti.get("sessions/rifiuto-domanda.json")!.toString());
    view.outcome = "failure"; view.refusal = null; view.failure = { diagnosis: "x" };
    remoti.set("sessions/rifiuto-domanda.json", Buffer.from(JSON.stringify(view)));
    const r = await cli("smoke-public"); expect(r.code).toBe(1);
  });
  it("coerenza: risposta diversa dalla risposta dichiarata nellindice non dà verde", async () => {
    cambia("sessions/partitore-tensione.json", v => { v.answer!.exact = "999"; });
    const r = await cli("smoke-public"); expect(r.code).toBe(1); expect(r.stdout).toContain("partitore-tensione");
  });
});


describe("profilo operativo esplicito", () => {
  it("anche un Failure canonico è un guasto operativo", async () => {
    const index = JSON.parse(remoti.get("sessions/index.json")!.toString());
    index.find((e: {id: string}) => e.id === "rifiuto-domanda").outcome = "failure";
    remoti.set("sessions/index.json", Buffer.from(JSON.stringify(index)));
    const view = JSON.parse(remoti.get("sessions/rifiuto-domanda.json")!.toString());
    view.outcome = "failure"; view.refusal = null; view.failure = { dove: "projection", messaggio: "Guasto sintetico" };
    remoti.set("sessions/rifiuto-domanda.json", Buffer.from(JSON.stringify(view)));
    const r = await cli("smoke-public"); expect(r.code).toBe(1); expect(r.stdout).toContain("failure");
  });
  it("gli spazi esterni ammessi dal confine browser non guastano una risposta sana", async () => {
    cambia("sessions/partitore-tensione.json", v => { v.answer!.exact = " 5 "; });
    const r = await cli("smoke-public"); expect(r.code).toBe(0);
  });
  it("un rifiuto con passi non è un catalogo sano", async () => {
    const view = JSON.parse(remoti.get("sessions/rifiuto-domanda.json")!.toString());
    view.steps = [{ id: "passo-inventato" }];
    remoti.set("sessions/rifiuto-domanda.json", Buffer.from(JSON.stringify(view)));
    const r = await cli("smoke-public"); expect(r.code).toBe(1); expect(r.stdout).toContain("rifiuto-domanda");
  });
});
