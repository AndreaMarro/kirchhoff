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

  it.each(["", " \n "])("non mostra come verificata una sessione nodale senza disegno: %j", (svg) => {
    const vista = parseSession(load("ponte-nodale"));
    expect(() => parseSession({ ...vista, states: vista.states.map((s) => ({ ...s, svg })) })).toThrow();
  });
});

type Mut = (x: Record<string, unknown>) => void;

function muta(id: string, fn: Mut): Record<string, unknown> {
  const x = structuredClone(load(id)) as Record<string, unknown>;
  fn(x);
  return x;
}

function campo(x: Record<string, unknown>, nome: string): Record<string, unknown> {
  return x[nome] as Record<string, unknown>;
}

describe("contratto P1-A: contraddizioni respinte", () => {
  it("product_verified true non entra", () => {
    expect(() =>
      parseSession(muta("partitore-d1", (x) => {
        campo(x, "truth").product_verified = true;
      })),
    ).toThrow();
  });

  it("chiusura backend VERIFIED non entra", () => {
    expect(() =>
      parseSession(muta("partitore-d1", (x) => {
        campo(x, "truth").backend_closure_status = "VERIFIED";
      })),
    ).toThrow();
  });

  it("claim contraddittorio non entra", () => {
    expect(() =>
      parseSession(muta("partitore-d1", (x) => {
        campo(x, "verification").claim_status = "UNVERIFIED";
      })),
    ).toThrow();
    expect(() =>
      parseSession(muta("partitore-d1", (x) => {
        campo(x, "verification").session_status = "VERIFIED";
      })),
    ).toThrow();
  });

  it("domanda assente nella closed non entra", () => {
    expect(() =>
      parseSession(muta("partitore-d1", (x) => {
        x.question = null;
      })),
    ).toThrow();
  });

  it("risposta incoerente con la domanda non entra", () => {
    expect(() =>
      parseSession(muta("partitore-d1", (x) => {
        campo(x, "answer").target = "R999";
      })),
    ).toThrow();
    expect(() =>
      parseSession(muta("partitore-d1", (x) => {
        campo(x, "answer").quantity = "voltage";
      })),
    ).toThrow();
  });

  it("unita' incompatibile non entra", () => {
    expect(() =>
      parseSession(muta("partitore-d1", (x) => {
        campo(x, "answer").unit = "volt";
      })),
    ).toThrow();
  });

  it.each([
    "1/0", "5/0", "1/00", "abc", "", " ", "3.14", "1e3", "1E-3",
    "1/2/3", "3/", "/4", "tre/80", "3 /80", "3/ 80", "50%", "0x10",
    "NaN", "Infinity",
  ])("exact illecito %p non entra", (esatto) => {
    expect(() =>
      parseSession(muta("partitore-d1", (x) => {
        campo(x, "answer").exact = esatto;
      })),
    ).toThrow();
  });

  it.each(["3/80", "0", "5", "-3/80", "-7", "10/4", " 3/80 "])(
    "exact lecito %p entra",
    (esatto) => {
      const vista = parseSession(muta("partitore-d1", (x) => {
        campo(x, "answer").exact = esatto;
      }));
      expect(vista.outcome).toBe("closed");
    },
  );

  it("stati vuoti, duplicati o pendenti non entrano", () => {
    expect(() =>
      parseSession(muta("partitore-d1", (x) => {
        x.states = [];
      })),
    ).toThrow();
    expect(() =>
      parseSession(muta("partitore-d1", (x) => {
        const states = x.states as unknown[];
        x.states = [...states, states[0]];
      })),
    ).toThrow();
    expect(() =>
      parseSession(muta("partitore-d1", (x) => {
        const steps = campo(x, "steps") as unknown as Record<string, unknown>;
        void steps;
        (x.steps as Record<string, unknown>[])[0].before_ref = "ir_pendente";
      })),
    ).toThrow();
  });

  it.each([true, false, 1.5, -1, Number.POSITIVE_INFINITY, Number.NaN, "0"])(
    "indice illecito %p non entra",
    (indice) => {
      expect(() =>
        parseSession(muta("partitore-d1", (x) => {
          (x.steps as Record<string, unknown>[])[0].index = indice as unknown;
        })),
      ).toThrow();
    },
  );

  it("indici duplicati o non consecutivi non entrano", () => {
    expect(() =>
      parseSession(muta("partitore-d1", (x) => {
        const steps = x.steps as Record<string, unknown>[];
        steps[1].index = steps[0].index;
      })),
    ).toThrow();
    expect(() =>
      parseSession(muta("partitore-d1", (x) => {
        const steps = x.steps as Record<string, unknown>[];
        steps[steps.length - 1].index = 99;
      })),
    ).toThrow();
  });

  it("closed con refusal o failure non entra", () => {
    expect(() =>
      parseSession(muta("partitore-d1", (x) => {
        x.refusal = {
          cause: "unsolvable",
          subject: "q1",
          subject_kind: "request",
          diagnosis: "contraddizione",
        };
      })),
    ).toThrow();
    expect(() =>
      parseSession(muta("partitore-d1", (x) => {
        x.failure = { dove: "render", messaggio: "x" };
      })),
    ).toThrow();
  });

  it.each(["refusal", "failure"] as const)(
    "esito %p con attestazioni positive non entra",
    (esito) => {
      const id = "rifiuto-reattivo";
      const base = load(id) as Record<string, unknown>;
      expect(base.outcome).toBe("refusal");
      const sorgente = esito === "refusal" ? base : {
        ...structuredClone(base),
        outcome: "failure",
        refusal: null,
        failure: { dove: "render", messaggio: "filo rotto" },
      };
      expect(() =>
        parseSession({
          ...structuredClone(sorgente),
          verification: campo(load("partitore-d1") as Record<string, unknown>, "verification"),
        }),
      ).toThrow();
      expect(() =>
        parseSession({
          ...structuredClone(sorgente),
          answer: campo(load("partitore-d1") as Record<string, unknown>, "answer"),
        }),
      ).toThrow();
      expect(() =>
        parseSession({
          ...structuredClone(sorgente),
          states: (load("partitore-d1") as Record<string, unknown>).states,
          steps: (load("partitore-d1") as Record<string, unknown>).steps,
        }),
      ).toThrow();
    },
  );

  it("passo analitico con ref diversi non entra", () => {
    expect(() =>
      parseSession(muta("partitore-d1", (x) => {
        const steps = x.steps as Record<string, unknown>[];
        const analitico = steps.find((s) => s.kind === "analytical") as Record<string, unknown>;
        const states = x.states as Record<string, unknown>[];
        const altro = (states.find((s) => s.ref !== analitico.before_ref) as Record<string, unknown>).ref;
        analitico.after_ref = altro;
      })),
    ).toThrow();
  });

  it("evidence_ids vuote respinte, controllo lecito adiacente verde", () => {
    const base = load("partitore-d1") as Record<string, unknown>;
    expect(
      (campo(base, "verification").evidence_ids as unknown[]).length,
    ).toBeGreaterThan(0);
    expect(() =>
      parseSession(muta("partitore-d1", (x) => {
        campo(x, "verification").evidence_ids = [];
      })),
    ).toThrow();
    expect(parseSession(base).outcome).toBe("closed");
  });

  it("kind passo fuori vocabolario non entra", () => {
    expect(() =>
      parseSession(muta("partitore-d1", (x) => {
        (x.steps as Record<string, unknown>[])[0].kind = "misterioso";
      })),
    ).toThrow();
  });

  it.each(["refusal", "failure"] as const)(
    "esito %p: status non positivo tollerato, chiusura positiva respinta",
    (esito) => {
      const base = load("rifiuto-reattivo") as Record<string, unknown>;
      const sorgente = esito === "refusal" ? base : {
        ...structuredClone(base),
        outcome: "failure",
        refusal: null,
        failure: { dove: "render", messaggio: "filo rotto" },
      };
      const tollerata = parseSession({
        ...structuredClone(sorgente),
        truth: { ...(campo(sorgente, "truth")), backend_closure_status: "FAILURE" },
      });
      expect(tollerata.outcome).toBe(esito);
      for (const chiusura of ["CLOSED", "VERIFIED"]) {
        expect(() =>
          parseSession({
            ...structuredClone(sorgente),
            truth: { ...(campo(sorgente, "truth")), backend_closure_status: chiusura },
          }),
        ).toThrow();
      }
      expect(() =>
        parseSession({
          ...structuredClone(sorgente),
          truth: { ...(campo(sorgente, "truth")), electrical_claim_status: "VERIFIED" },
        }),
      ).toThrow();
    },
  );

  it("controlli leciti: scala, ponte, rifiuto, guasto senza domanda", () => {
    const scala = parseSession(load("scala-due-riduzioni"));
    expect(scala.outcome).toBe("closed");
    expect(scala.answer?.target).toBe(scala.question?.target);
    const ponte = parseSession(load("ponte-nodale"));
    expect(ponte.outcome).toBe("closed");
    const rifiuto = parseSession(load("rifiuto-reattivo"));
    expect(rifiuto.outcome).toBe("refusal");
    const base = load("rifiuto-reattivo") as Record<string, unknown>;
    const guasto = parseSession({
      ...structuredClone(base),
      outcome: "failure",
      refusal: null,
      failure: { dove: "render", messaggio: "filo rotto" },
      question: null,
    });
    expect(guasto.outcome).toBe("failure");
  });
});

// Il payload e' una sequenza, non un insieme di indici corretti riordinabile.
it("rifiuta passi fuori ordine anche con indici completi", () => {
  const vista = parseSession(load("partitore-d1"));
  expect(vista.steps.length).toBeGreaterThan(1);
  expect(() => parseSession({ ...vista, steps: [...vista.steps].reverse() })).toThrow(/ordine/);
});
