import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { parseSession } from "../src/session/guards.ts";

type RawView = Record<string, unknown> & {
  steps: Record<string, unknown>[];
  verification: { evidence_ids: string[] };
};

function raw(): RawView {
  return JSON.parse(readFileSync(join(import.meta.dirname, "../public/sessions/scala-tre-riduzioni.json"), "utf8"));
}

function mapped(): RawView {
  const view = raw();
  // Identificatori opachi: il consumer non può ricavare il passo da una cifra.
  view.verification.evidence_ids = ["derivazione-alfa", "derivazione-omega"];
  for (const step of view.steps) {
    step.derivation_ref = step.index === 3 ? "derivazione-alfa" : step.index === 4 ? "derivazione-omega" : null;
  }
  return view;
}

describe("Claim, derivazione e passo: confine di presentazione", () => {
  it("conserva il riferimento esplicito, distinto dagli IR e dall'indice", () => {
    const view = parseSession(mapped());
    expect(view.steps.map(s => (s as unknown as Record<string, unknown>).derivation_ref)).toEqual([
      null, null, null, "derivazione-alfa", "derivazione-omega",
    ]);
    expect(view.steps[3].kind).toBe("analytical");
    expect(view.steps[3].index).toBe(3);
  });

  it("legge il legacy senza ricreare un legame che il payload non espone", () => {
    const payload = raw();
    payload.steps.forEach(s => { delete s.derivation_ref; });
    const view = parseSession(payload);
    expect(view.steps.every(s => !Object.hasOwn(s, "derivation_ref"))).toBe(true);
    expect(view.answer?.exact).toBeTruthy();
  });

  const invalid: Array<[string, (v: RawView) => void]> = [
    ["presenza su un solo passo", v => { v.steps.forEach((s, i) => { if (i !== 3) delete s.derivation_ref; }); }],
    ["un passo omesso nel profilo nuovo", v => { delete v.steps[0].derivation_ref; }],
    ["tutti null", v => { v.steps.forEach(s => { s.derivation_ref = null; }); }],
    ["analitico null", v => { v.steps[3].derivation_ref = null; }],
    ["analitico blank", v => { v.steps[3].derivation_ref = " \n "; }],
    ["analitico numerico", v => { v.steps[3].derivation_ref = 3; }],
    ["analitico booleano", v => { v.steps[3].derivation_ref = false; }],
    ["riferimento su trasformazione", v => { v.steps[0].derivation_ref = "derivazione-alfa"; }],
    ["riferimenti duplicati", v => { v.steps[4].derivation_ref = "derivazione-alfa"; }],
    ["duplicati anche nel Claim", v => { v.steps[4].derivation_ref = "derivazione-alfa"; v.verification.evidence_ids = ["derivazione-alfa", "derivazione-alfa"]; }],
    ["riferimento estraneo", v => { v.steps[3].derivation_ref = "D0"; }],
    ["ordine delle evidenze scambiato", v => { v.verification.evidence_ids.reverse(); }],
    ["evidenza in più", v => { v.verification.evidence_ids.push("derivazione-extra"); }],
    ["evidenza in meno", v => { v.verification.evidence_ids.pop(); }],
    ["spazi non normalizzati negli ID", v => { v.steps[3].derivation_ref = " derivazione-alfa "; }],
  ];
  it.each(invalid)("rifiuta il mapping incoerente: %s", (_name, mutate) => {
    expect(() => parseSession(mapped())).not.toThrow();
    const bad = mapped();
    mutate(bad);
    expect(() => parseSession(bad)).toThrow();
  });
});
