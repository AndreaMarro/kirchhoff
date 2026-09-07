/* Matematica pura del palco: viewport stabile e stato nell'URL.
   Niente DOM qui dentro: tutto e' testato in vitest senza browser. */

export interface ViewBox {
  x: number;
  y: number;
  w: number;
  h: number;
}

export function parseViewBox(svg: string): ViewBox | null {
  const m = svg.match(/<svg[^>]*\bviewBox="([^"]+)"/);
  if (!m) return null;
  const parts = m[1].trim().split(/[\s,]+/).map(Number);
  if (parts.length !== 4 || parts.some((n) => !Number.isFinite(n))) return null;
  const [x, y, w, h] = parts;
  if (w <= 0 || h <= 0) return null;
  return { x, y, w, h };
}

export function unionViewBox(a: ViewBox, b: ViewBox): ViewBox {
  const x = Math.min(a.x, b.x);
  const y = Math.min(a.y, b.y);
  const right = Math.max(a.x + a.w, b.x + b.w);
  const bottom = Math.max(a.y + a.h, b.y + b.h);
  return { x, y, w: right - x, h: bottom - y };
}

export function viewBoxString(vb: ViewBox): string {
  const fmt = (n: number): string =>
    Number.isInteger(n) ? String(n) : String(Math.round(n * 100) / 100);
  return `${fmt(vb.x)} ${fmt(vb.y)} ${fmt(vb.w)} ${fmt(vb.h)}`;
}

/** Il movimento apparente massimo che la viewport unita puo' causare.
 *  Usato nei test: un preservato non deve teletrasportarsi per un
 *  semplice riscalamento fra prima e dopo. */
export function frameShift(a: ViewBox, b: ViewBox): number {
  return Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));
}

export interface WorkbenchHash {
  exercise: string;
  step: number;
  frame: "before" | "after";
}

export function parseHash(hash: string): Partial<WorkbenchHash> {
  const out: Partial<WorkbenchHash> = {};
  const h = hash.startsWith("#") ? hash.slice(1) : hash;
  for (const part of h.split("&")) {
    const [k, v] = part.split("=");
    if (k === "exercise" && v) out.exercise = decodeURIComponent(v);
    if (k === "step" && v && /^\d+$/.test(v)) out.step = Number(v);
    if (k === "frame" && (v === "before" || v === "after")) out.frame = v;
  }
  return out;
}

export function formatHash(s: WorkbenchHash): string {
  return `#exercise=${encodeURIComponent(s.exercise)}&step=${s.step}&frame=${s.frame}`;
}
