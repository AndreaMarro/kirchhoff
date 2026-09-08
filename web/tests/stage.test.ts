import { describe, expect, it } from "vitest";
import {
  formatHash,
  frameShift,
  parseHash,
  parseViewBox,
  unionViewBox,
  viewBoxString,
} from "../src/session/stage.ts";

describe("parseViewBox", () => {
  it("legge il viewBox dalla radice", () => {
    expect(parseViewBox('<svg viewBox="-24 -36.8 543.4 224.8">')).toEqual({
      x: -24,
      y: -36.8,
      w: 543.4,
      h: 224.8,
    });
  });

  it("rifiuta viewBox assenti o degeneri", () => {
    expect(parseViewBox("<svg></svg>")).toBeNull();
    expect(parseViewBox('<svg viewBox="0 0 0 10">')).toBeNull();
    expect(parseViewBox('<svg viewBox="a b c d">')).toBeNull();
  });
});

describe("unionViewBox", () => {
  it("contiene entrambi i fotogrammi", () => {
    const a = { x: -24, y: -36.8, w: 543.4, h: 224.8 };
    const b = { x: -24, y: -28.8, w: 493.4, h: 216.8 };
    const u = unionViewBox(a, b);
    expect(u.x).toBeLessThanOrEqual(-24);
    expect(u.y).toBeLessThanOrEqual(-36.8);
    expect(u.x + u.w).toBeGreaterThanOrEqual(-24 + 543.4);
    expect(u.y + u.h).toBeGreaterThanOrEqual(-28.8 + 216.8);
  });

  it("lo spostamento fra fotogrammi lungimiranti resta piccolo", () => {
    const a = { x: -24, y: -36.8, w: 543.4, h: 224.8 };
    const b = { x: -24, y: -28.8, w: 493.4, h: 216.8 };
    expect(frameShift(a, b)).toBeLessThan(20);
  });

  it("serializza in forma compatta", () => {
    expect(viewBoxString({ x: -24, y: -36.8, w: 543.4, h: 224.8 })).toBe("-24 -36.8 543.4 224.8");
  });
});

describe("hash di stato", () => {
  it("gira in tondo", () => {
    const s = { exercise: "partitore-d1", step: 2, frame: "after" as const };
    expect(parseHash(formatHash(s))).toEqual(s);
  });

  it("ignora spazzatura senza esplodere", () => {
    expect(parseHash("#step=xx&frame=prima")).toEqual({});
    expect(parseHash("")).toEqual({});
  });
});

describe("labels", () => {
  it("traduce specie e grandezze note, mai inventa", async () => {
    const { kindLabel, quantityLabel } = await import("../src/session/labels.ts");
    expect(kindLabel("choose_reference")).toBe("Riferimento");
    expect(kindLabel("write_kcl")).toBe("KCL al nodo");
    expect(kindLabel("serie")).toBe("Serie");
    expect(kindLabel("operazione_futura")).toBe("operazione_futura");
    expect(quantityLabel("voltage")).toBe("tensione");
    expect(quantityLabel("current")).toBe("corrente");
    expect(quantityLabel("carica")).toBe("carica");
  });
});
