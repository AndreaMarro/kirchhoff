import { createRequire } from "node:module";
import { describe, expect, it } from "vitest";

// Esercita la copia risolta dal consumer reale Vite -> PostCSS, anche se non
// fosse hoisted alla radice. Non aggiunge una dipendenza diretta al prodotto.
const require = createRequire(import.meta.url);
const viteRequire = createRequire(require.resolve("vite/package.json"));
const postcssRequire = createRequire(viteRequire.resolve("postcss/package.json"));
const { SourceMapConsumer, SourceNode } = postcssRequire("source-map-js");

const basic = {
  version: 3,
  sources: ["input.css"],
  sourcesContent: ["a { color: blue; }"],
  names: [],
  mappings: "AAAA",
};
const indexed = (map: object, line: number, column = 0) => ({
  version: 3,
  sections: [{ offset: { line, column }, map }],
});

describe("mappe indicizzate nella toolchain CSS", () => {
  // Solo costruzione: non appiattisce o serializza gli offset fuori limite.
  // Il controesempio resta piccolo e non tenta di esaurire CPU o memoria.
  it.each([
    ["una linea oltre il limite upstream", indexed(basic, 10_000_001)],
    ["una linea negativa", indexed(basic, -1)],
    ["una linea frazionaria", indexed(basic, 1.5)],
    ["una colonna negativa", indexed(basic, 0, -1)],
    ["una colonna frazionaria", indexed(basic, 0, 1.5)],
    ["la somma fuori limite di due sezioni", indexed(indexed(basic, 6_000_000), 6_000_000)],
  ])("rifiuta %s nel costruttore", (_label, map) => {
    expect(() => new SourceMapConsumer(JSON.stringify(map))).toThrow();
  });

  it.each([0, 3])("conserva la posizione e il contenuto con offset sano %i", (line) => {
    const consumer = new SourceMapConsumer(JSON.stringify(indexed(basic, line)));
    const position = { source: "input.css", line: 1, column: 0, name: null };
    expect(consumer.originalPositionFor({ line: line + 1, column: 1 })).toEqual(position);
    expect(consumer.sourceContentFor("input.css")).toBe(basic.sourcesContent[0]);

    // Qui si serializzano solo zero o tre righe di offset.
    const generatedCode = "\n".repeat(line) + basic.sourcesContent[0];
    const node = SourceNode.fromStringWithSourceMap(generatedCode, consumer);
    const emitted = node.toStringWithSourceMap({ file: "output.css" });
    expect(emitted.code).toBe(generatedCode);
    const flattened = emitted.map.toString();
    expect(JSON.parse(flattened).mappings.length).toBeLessThan(50);
    const reopened = new SourceMapConsumer(flattened);
    expect(reopened.originalPositionFor({ line: line + 1, column: 1 })).toEqual(position);
    expect(reopened.sourceContentFor("input.css")).toBe(basic.sourcesContent[0]);
  });
});
