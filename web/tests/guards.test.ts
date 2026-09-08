import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { parseIndex, parseSession } from "../src/session/guards.ts";

const dir = join(import.meta.dirname, "..", "public", "sessions");

function load(id: string): unknown {
  return JSON.parse(readFileSync(join(dir, `${id}.json`), "utf-8"));
}

describe("guards sul confine", () => {
  it("l'indice elenca undici esercizi onesti", () => {
    const index = parseIndex(JSON.parse(readFileSync(join(dir, "index.json"), "utf-8")));
    expect(index.map((e) => e.id)).toEqual([
      "partitore-d1",
      "scala-due-riduzioni",
      "ponte-nodale",
      "rifiuto-reattivo",
      "partitore-tensione",
      "due-rami-parallelo",
      "serie-parallelo-misto",
      "scala-tre-riduzioni",
      "ramo-derivato",
      "generatore-flottante",
      "rifiuto-domanda",
    ]);
  });

  it("ogni vista chiusa passa le guardie e mostra l'esatto", () => {
    for (const id of [
      "partitore-d1",
      "scala-due-riduzioni",
      "ponte-nodale",
      "partitore-tensione",
      "due-rami-parallelo",
      "serie-parallelo-misto",
      "scala-tre-riduzioni",
      "ramo-derivato",
      "generatore-flottante",
    ]) {
      const vista = parseSession(load(id));
      expect(vista.outcome).toBe("closed");
      expect(vista.answer?.exact).toMatch(/^\d+(\/\d+)?$/);
      expect(vista.truth.product_verified).toBe(false);
    }
  });

  it("il rifiuto non ha risposta e ha diagnosi", () => {
    for (const id of ["rifiuto-reattivo", "rifiuto-domanda"]) {
      const vista = parseSession(load(id));
      expect(vista.outcome).toBe("refusal");
      expect(vista.answer).toBeNull();
      expect(vista.refusal?.diagnosis.length).toBeGreaterThan(20);
    }
  });

  it("uno schema sconosciuto non entra", () => {
    const vista = load("partitore-d1") as Record<string, unknown>;
    expect(() => parseSession({ ...vista, schema_version: "x" })).toThrow();
  });

  it("una chiusura senza risposta non entra", () => {
    const vista = load("partitore-d1") as Record<string, unknown>;
    expect(() => parseSession({ ...vista, answer: null })).toThrow();
  });
});
