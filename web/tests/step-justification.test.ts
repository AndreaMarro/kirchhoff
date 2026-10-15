import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { StepInspector } from "../src/components/StepInspector.tsx";
import { parseSession } from "../src/session/guards.ts";
import type { StepView } from "../src/session/types.ts";

const legacy = parseSession(JSON.parse(readFileSync(join(import.meta.dirname, "../public/sessions/partitore-d1.json"), "utf8")));
function step(): StepView {
  const base = legacy.steps.find(p => p.kind === "transform")!;
  // Fixture solo di rendering: non sostituisce la prova del producer canonico.
  return { ...base, justification: {
    terminals: [{ kind: "node", id: "0" }, { kind: "node", id: "b" }],
    preconditions: ["Prima condizione", "Seconda condizione"], formula: base.equation!,
    certificate: { operation: base.action!, checks: ["check-a", "check-b"], attestations: [] },
  } };
}
const render = (s: StepView) => renderToStaticMarkup(createElement(StepInspector, { step: s }));
describe("K4 quattro campi del passo", () => {
  it("espone il disclosure nativo con i quattro campi nell'ordine dell'autorita'", () => {
    const html = render(step());
    expect(html).toContain("<summary>Perché posso farlo?</summary>");
    const labels = [...html.matchAll(/<dt>(.*?)<\/dt>/g)].map(m => m[1]);
    expect(labels).toEqual(["Terminali", "Precondizioni", "Formula", "Certificato"]);
    expect(html).not.toMatch(/<details[^>]*\bopen(?:=|>)/);
    expect(html).toContain("Prima condizione"); expect(html).toContain("Seconda condizione");
    expect(html.indexOf("Prima condizione")).toBeLessThan(html.indexOf("Seconda condizione"));
  });
  it("mostra formula e certificato completi inclusa l'assenza dichiarata di attestazioni", () => {
    const html = render(step());
    expect(html).toContain("check-a"); expect(html).toContain("check-b");
    expect(html).toContain("Nessuna attestazione di identità dichiarata.");
    expect(html).not.toContain("kf-check"); expect(html).not.toContain("Product Verified");
  });
  it("conserva un'attestazione sintetica e i suoi attributi, senza trasformarla in licenza", () => {
    const s = step(); s.justification!.certificate.attestations = [{ entity: { kind: "component", id: "V1" }, changed: ["value", "type"] }];
    const html = render(s);
    expect(html).toContain("V1"); expect(html).toContain("value, type");
    expect(html).not.toContain("Nessuna attestazione di identità dichiarata.");
  });
  it("tratta precondizioni e identificatori come testo inerte", () => {
    const s = step(); const token = '<img src=x onerror="window.bad=1">';
    s.justification!.preconditions = [token]; s.justification!.terminals[0].id = token;
    const html = render(s);
    expect(html).toContain("&lt;img"); expect(html).not.toContain("<img");
    expect(html).not.toContain("dangerouslySetInnerHTML");
  });
  it("dichiara il limite legacy senza fabbricare i quattro campi", () => {
    const s = step(); delete s.justification;
    const html = render(s);
    expect(html).toContain("Questa sessione non espone la giustificazione del passo.");
    expect(html).not.toContain("Perché posso farlo?");
  });
  it("non apre una giustificazione topologica per un passo analitico", () => {
    const s = legacy.steps.find(p => p.kind === "analytical")!;
    const html = render({ ...s, justification: null });
    expect(html).toContain("Passo analitico");
    expect(html).not.toContain("Perché posso farlo?");
    expect(html).not.toContain("non espone la giustificazione");
  });
});
