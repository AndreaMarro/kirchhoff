import { describe, expect, it } from "vitest";
import { readFileSync, mkdtempSync, writeFileSync, rmSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { spawnSync } from "node:child_process";
import { parseSession, STEP_IDENTITY_ATTRIBUTES } from "../src/session/guards.ts";

type Wire = Record<string, unknown>;
const web = join(import.meta.dirname, "..");
const obj = (v: unknown) => v as Wire;
const steps = (v: Wire) => v.steps as Wire[];
const first = (v: Wire) => steps(v).find(p => p.kind === "transform")!;
const why = (v: Wire) => obj(first(v).justification);
const cert = (v: Wire) => obj(why(v).certificate);
const analytical = (v: Wire) => steps(v).find(p => p.kind === "analytical")!;
function load(id = "partitore-d1"): Wire {
  return JSON.parse(readFileSync(join(web, "public/sessions", id + ".json"), "utf8"));
}
function legacy(id = "partitore-d1"): Wire {
  const v = load(id);
  for (const p of steps(v)) delete p.justification;
  return v;
}
function profile(id = "partitore-d1"): Wire {
  // Dati sintetici di trasporto: non certificano precondizioni o licenze.
  const v = legacy(id);
  for (const p of steps(v)) p.justification = p.kind === "analytical" ? null : {
    terminals: (p.preserved as Wire[]).filter(e => e.kind === "node"),
    preconditions: [" z ", "a"], formula: p.equation,
    certificate: { operation: p.action, checks: [" z ", "a"], attestations: [] },
  };
  return v;
}
function attestation(v: Wire): Wire {
  return { entity: (first(v).preserved as Wire[]).find(e => e.kind === "component"), changed: ["value", "type"] };
}
const script = `import {readFileSync} from 'node:fs';
import {validaVista} from './scripts/artifact-contract.mjs';
const {vista,voce}=JSON.parse(readFileSync(process.argv[1],'utf8'));
process.stdout.write(JSON.stringify(validaVista(vista,voce)));`;
function cli(v: Wire): Wire {
  // Gli id delle Request non sono gli id del catalogo; la voce corrisponde
  // alla fixture scelta, per domanda/esito/risposta, senza interpretare il circuito.
  const index = JSON.parse(readFileSync(join(web, "public/sessions/index.json"), "utf8")) as Wire[];
  const entry = index.find(e => obj(e.domanda).target === obj(v.question).target && obj(e.domanda).quantity === obj(v.question).quantity && e.outcome === v.outcome && e.risposta_esatta === `${obj(v.answer).exact} ${obj(v.answer).unit}`);
  expect(entry, "voce di catalogo della fixture").toBeDefined();
  // Il fixture resta identico: evita il blocco intermittente della pipe stdin
  // osservato con spawnSync su macOS, mantenendo processo e timeout del CLI.
  const directory = mkdtempSync(join(tmpdir(), "kirchhoff-contract-"));
  try {
    const input = join(directory, "request.json");
    writeFileSync(input, JSON.stringify({ vista: v, voce: entry }), "utf8");
    const r = spawnSync(process.execPath, ["--input-type=module", "-e", script, input], {
      cwd: web, encoding: "utf8", timeout: 10_000,
    });
    if (r.error) throw r.error;
    if (r.status !== 0) throw new Error(r.stderr);
    return JSON.parse(r.stdout);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
}
const bad: [string, (v: Wire) => void][] = [
  ["presenza parziale", v => { delete analytical(v).justification; }],
  ["solo null analitico presente", v => { for (const p of steps(v)) delete p.justification; analytical(v).justification = null; }],
  ["trasformazione null", v => { first(v).justification = null; }],
  ["trasformazione array", v => { first(v).justification = []; }],
  ["analitico oggetto", v => { analytical(v).justification = why(v); }],
  ["terminali mancanti", v => { delete why(v).terminals; }],
  ["terminali vuoti", v => { why(v).terminals = []; }],
  ["terminali scalare", v => { why(v).terminals = "0"; }],
  ["terminali duplicati", v => { why(v).terminals = [obj(why(v).terminals)[0], obj(why(v).terminals)[0]]; }],
  ["terminale componente preservato", v => { why(v).terminals = [attestation(v).entity]; }],
  ["terminale interno", v => { why(v).terminals = [{ kind: "node", id: "a" }]; }],
  ["terminale genere ignoto", v => { why(v).terminals = [{ kind: "altro", id: "0" }]; }],
  ["terminale id vuoto", v => { why(v).terminals = [{ kind: "node", id: " " }]; }],
  ["terminale id numerico", v => { why(v).terminals = [{ kind: "node", id: 0 }]; }],
  ["precondizioni mancanti", v => { delete why(v).preconditions; }],
  ["precondizioni vuote", v => { why(v).preconditions = []; }],
  ["precondizioni scalare", v => { why(v).preconditions = "a"; }],
  ["precondizione duplicata", v => { why(v).preconditions = ["a", "a"]; }],
  ["precondizione vuota", v => { why(v).preconditions = [" "]; }],
  ["precondizione non testo", v => { why(v).preconditions = [1]; }],
  ["formula mancante", v => { delete why(v).formula; }],
  ["formula diversa", v => { why(v).formula = "R = R1 * R2"; }],
  ["formula numerica", v => { why(v).formula = 1; }],
  ["certificato mancante", v => { delete why(v).certificate; }],
  ["certificato array", v => { why(v).certificate = []; }],
  ["operazione diversa", v => { cert(v).operation = "parallelo"; }],
  ["operazione vuota", v => { cert(v).operation = " "; }],
  ["controlli mancanti", v => { delete cert(v).checks; }],
  ["controlli vuoti", v => { cert(v).checks = []; }],
  ["controlli scalare", v => { cert(v).checks = "a"; }],
  ["controllo duplicato", v => { cert(v).checks = ["a", "a"]; }],
  ["controllo vuoto", v => { cert(v).checks = [" "]; }],
  ["controllo numerico", v => { cert(v).checks = [1]; }],
  ["attestazioni mancanti", v => { delete cert(v).attestations; }],
  ["attestazioni scalare", v => { cert(v).attestations = "a"; }],
  ["attestazione non oggetto", v => { cert(v).attestations = [null]; }],
  ["attestazione duplicata", v => { cert(v).attestations = [attestation(v), attestation(v)]; }],
  ["attestazione nodo", v => { cert(v).attestations = [{ entity: { kind: "node", id: "0" }, changed: ["value"] }]; }],
  ["attestazione non preservata", v => { cert(v).attestations = [{ entity: { kind: "component", id: "R1" }, changed: ["value"] }]; }],
  ["attributi vuoti", v => { cert(v).attestations = [{ ...attestation(v), changed: [] }]; }],
  ["attributi scalare", v => { cert(v).attestations = [{ ...attestation(v), changed: "value" }]; }],
  ["attributi duplicati", v => { cert(v).attestations = [{ ...attestation(v), changed: ["value", "value"] }]; }],
  ["attributo ignoto", v => { cert(v).attestations = [{ ...attestation(v), changed: ["provenance"] }]; }],
];

for (const [name, read] of [["browser", (v: Wire) => obj(parseSession(v))], ["CLI reale", cli]] as const) {
  describe(`K4 contratto ${name}`, () => {
    it("accetta legacy con derivation_ref presente senza inventare giustificazioni", () => {
      const v = read(legacy());
      expect(Object.hasOwn(steps(v)[0], "justification")).toBe(false);
      expect(Object.hasOwn(steps(v)[0], "derivation_ref")).toBe(true);
    });
    it.each(["partitore-d1", "scala-due-riduzioni", "due-rami-parallelo", "ponte-nodale"])("accetta profilo completo %s, conserva quattro campi e null analitici", id => {
      const v = profile(id), out = read(v);
      expect(steps(out).map(p => p.justification)).toEqual(steps(v).map(p => p.justification));
      expect(obj(out.truth).product_verified).toBe(false);
    });
    it("accetta subset, ordine e testo opaco senza normalizzare o autenticare licenze", () => {
      const v = profile();
      why(v).terminals = (why(v).terminals as unknown[]).slice(0, 1);
      cert(v).attestations = [attestation(v)];
      expect(steps(read(v))[0].justification).toEqual(first(v).justification);
    });
    it.each(bad)("respinge %s dopo controllo sano adiacente", (_label, mutate) => {
      expect(() => read(profile())).not.toThrow();
      const v = profile(); mutate(v);
      expect(() => read(v)).toThrow(/giustificazione|certificato|attestazione/);
    });
    it("accetta chiavi future nel reader senza attribuirvi nuova semantica", () => {
      const v = profile(); why(v).future = "dato extra";
      expect(() => read(v)).not.toThrow();
    });
  });
}

for (const [name, read] of [["browser", (v: Wire) => obj(parseSession(v))], ["CLI reale", cli]] as const) {
  describe(`K4 indipendenza delle estensioni ${name}`, () => {
    it("accetta entrambe le estensioni assenti e conserva l'assenza", () => {
      const v = legacy(); for (const p of steps(v)) delete p.derivation_ref;
      const out = read(v);
      expect(steps(out).every(p => !Object.hasOwn(p, "justification") && !Object.hasOwn(p, "derivation_ref"))).toBe(true);
    });
    it("accetta giustificazioni complete senza derivation_ref", () => {
      const v = profile(); for (const p of steps(v)) delete p.derivation_ref;
      expect(steps(read(v)).map(p => p.justification)).toEqual(steps(v).map(p => p.justification));
    });
    it("respinge una giustificazione incoerente anche senza derivation_ref", () => {
      const v = profile(); for (const p of steps(v)) delete p.derivation_ref;
      expect(() => read(v)).not.toThrow();
      why(v).formula = "formula diversa";
      expect(() => read(v)).toThrow(/giustificazione.*formula/);
    });
    it("respinge un mapping H5 parziale anche con giustificazioni sane", () => {
      const v = profile(); expect(() => read(v)).not.toThrow();
      delete analytical(v).derivation_ref;
      expect(() => read(v)).toThrow(/derivazione.*parziale/);
    });
    it.each(STEP_IDENTITY_ATTRIBUTES)("trasporta attributo strutturale %s senza concedere una licenza", attribute => {
      const v = profile(); cert(v).attestations = [{ ...attestation(v), changed: [attribute] }];
      expect(steps(read(v))[0].justification).toEqual(first(v).justification);
    });
    it("respinge lo scambio delle giustificazioni fra due serie", () => {
      const v = profile("scala-due-riduzioni"); expect(() => read(v)).not.toThrow();
      const p = steps(v).filter(p => p.kind === "transform");
      expect(p).toHaveLength(2); expect(p.map(p => p.action)).toEqual(["serie", "serie"]);
      expect(obj(p[0].justification).formula).not.toEqual(obj(p[1].justification).formula);
      expect(obj(p[0].justification).terminals).not.toEqual(obj(p[1].justification).terminals);
      [p[0].justification, p[1].justification] = [p[1].justification, p[0].justification];
      expect(() => read(v)).toThrow(/giustificazione.*formula/);
    });
  });
}
