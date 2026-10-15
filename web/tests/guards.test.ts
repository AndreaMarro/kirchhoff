import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { parseIndex, parseSession } from "../src/session/guards.ts";
import type { TruthView, VerificationView } from "../src/session/types.ts";

const dir = join(import.meta.dirname, "..", "public", "sessions");

function load(id: string): unknown {
  return JSON.parse(readFileSync(join(dir, `${id}.json`), "utf-8"));
}

describe("guards sul confine", () => {
  it("l'indice elenca quattro esercizi onesti", () => {
    const index = parseIndex(JSON.parse(readFileSync(join(dir, "index.json"), "utf-8")));
    expect(index.map((e) => e.id)).toEqual([
      "partitore-d1",
      "scala-due-riduzioni",
      "ponte-nodale",
      "rifiuto-reattivo",
    ]);
  });

  it("ogni vista chiusa passa le guardie e mostra l'esatto", () => {
    for (const id of ["partitore-d1", "scala-due-riduzioni", "ponte-nodale"]) {
      const vista = parseSession(load(id));
      expect(vista.outcome).toBe("closed");
      expect(vista.answer?.exact).toMatch(/^\d+\/\d+$/);
      expect(vista.truth.product_verified).toBe(false);
    }
  });

  it("il rifiuto non ha risposta e ha diagnosi", () => {
    const vista = parseSession(load("rifiuto-reattivo"));
    expect(vista.outcome).toBe("refusal");
    expect(vista.answer).toBeNull();
    expect(vista.refusal?.diagnosis.length).toBeGreaterThan(20);
  });

  it("uno schema sconosciuto non entra", () => {
    const vista = load("partitore-d1") as Record<string, unknown>;
    expect(() => parseSession({ ...vista, schema_version: "x" })).toThrow();
  });

  it("una chiusura senza risposta non entra", () => {
    const vista = load("partitore-d1") as Record<string, unknown>;
    expect(() => parseSession({ ...vista, answer: null })).toThrow();
  });

  it.each<[string, { truth?: Partial<TruthView>; verification?: Partial<VerificationView>; states?: never[] }]>([
    ["claim non verificato", { truth: { electrical_claim_status: "UNVERIFIED", backend_closure_status: "CLOSED", product_verified: false } }],
    ["sessione non chiusa", { truth: { electrical_claim_status: "VERIFIED", backend_closure_status: "DRAFT", product_verified: false } }],
    ["prova respinta", { verification: { claim_status: "REJECTED" } }],
    ["prova non chiusa", { verification: { session_status: "DRAFT" } }],
    ["verificatore assente", { verification: { claim_verifier: null } }],
    ["versione assente", { verification: { claim_version: "" } }],
    ["evidenze assenti", { verification: { evidence_ids: [] } }],
    ["soggetti assenti", { verification: { claim_subjects: [] } }],
    ["stati visuali assenti", { states: [] }],
  ])("non presenta come verificata una chiusura con %s", (_name, override) => {
    const original = parseSession(load("partitore-d1"));
    const payload = {
      ...original,
      ...override,
      truth: { ...original.truth, ...override.truth },
      verification: { ...original.verification, ...override.verification },
    };
    expect(() => parseSession(payload)).toThrow();
  });

  it.each([
    ["riferimento prima assente", { before_ref: "ir_assente" }],
    ["riferimento dopo assente", { after_ref: "ir_assente" }],
    ["tipo sconosciuto", { kind: "futuro" }],
    ["indice frazionario", { index: 0.5 }],
    ["indice fuori sequenza", { index: 4 }],
    ["prima senza disegno", { before_svg: null }],
    ["dopo senza disegno", { after_svg: "" }],
    ["trasformazione senza cambio di stato", { after_ref: "same" }],
  ])("rifiuta un passo incoerente: %s", (_name, override) => {
    const vista = parseSession(load("partitore-d1"));
    const first = { ...vista.steps[0], ...override };
    if (first.after_ref === "same") first.after_ref = first.before_ref;
    expect(() => parseSession({ ...vista, steps: [first, ...vista.steps.slice(1)] })).toThrow();
  });

  it("rifiuta riferimenti di stato duplicati", () => {
    const vista = parseSession(load("partitore-d1"));
    expect(() => parseSession({ ...vista, states: [vista.states[0], vista.states[0]] })).toThrow();
  });

  it("un passo analitico resta ancorato allo stesso stato", () => {
    const vista = parseSession(load("partitore-d1"));
    const steps = vista.steps.map((s) => s.kind === "analytical" ? { ...s, after_ref: vista.states[0].ref } : s);
    expect(() => parseSession({ ...vista, steps })).toThrow();
  });
});
