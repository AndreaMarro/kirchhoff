import { useEffect, useRef } from "react";
import {
  parseViewBox,
  unionViewBox,
  viewBoxString,
} from "../session/stage.ts";

export interface StageEntity {
  kind: string;
  id: string;
}

interface Props {
  svg: string;
  compareWith: string | null;
  selected: StageEntity | null;
  onSelectEntity: (e: StageEntity | null) => void;
  caption: string;
}

function entityNear(container: HTMLElement, x: number, y: number): StageEntity | null {
  const direct = entityFromElement(document.elementFromPoint(x, y));
  if (direct) return direct;
  // I tratti sono sottili: entro un raggio da tocco si sceglie l'entita'
  // piu' vicina. Comodita' del puntatore, mai semantica: la via da
  // tastiera resta l'elenco di bottoni e i byte non si toccano.
  interface Scored {
    e: StageEntity;
    d: number;
  }
  const scored: Scored[] = [];
  container.querySelectorAll("[data-component-id],[data-node-id]").forEach((el) => {
    const cid = el.getAttribute("data-component-id");
    const nid = el.getAttribute("data-node-id");
    const found: StageEntity | null = cid
      ? { kind: "component", id: cid }
      : nid
        ? { kind: "node", id: nid }
        : null;
    if (!found) return;
    const r = (el as unknown as SVGGraphicsElement).getBoundingClientRect();
    const dx = Math.max(r.x - x, 0, x - (r.x + r.width));
    const dy = Math.max(r.y - y, 0, y - (r.y + r.height));
    const d = Math.hypot(dx, dy);
    if (d <= 16) scored.push({ e: found, d });
  });
  let win: Scored | null = null;
  for (const s of scored) {
    if (win === null || s.d < win.d) win = s;
  }
  return win === null ? null : win.e;
}

function entityFromElement(el: Element | null): StageEntity | null {
  const comp = el?.closest("[data-component-id]");
  if (comp) {
    const id = comp.getAttribute("data-component-id");
    if (id) return { kind: "component", id };
  }
  const node = el?.closest("[data-node-id]");
  if (node) {
    const id = node.getAttribute("data-node-id");
    if (id) return { kind: "node", id };
  }
  const term = el?.closest("[data-terminal-component]");
  if (term) {
    const id = term.getAttribute("data-terminal-component");
    if (id) return { kind: "component", id };
  }
  return null;
}

function selectorFor(e: StageEntity): string {
  if (e.kind === "component") return `[data-component-id="${CSS.escape(e.id)}"]`;
  if (e.kind === "node") return `[data-node-id="${CSS.escape(e.id)}"]`;
  return `[data-terminal-component="${CSS.escape(e.id)}"]`;
}

export function CircuitStage({ svg, compareWith, selected, onSelectEntity, caption }: Props): React.JSX.Element {
  const frameRef = useRef<HTMLDivElement>(null);

  const ownVb = parseViewBox(svg);
  const otherVb = compareWith ? parseViewBox(compareWith) : null;
  const stableVb = ownVb && otherVb ? viewBoxString(unionViewBox(ownVb, otherVb)) : null;

  useEffect(() => {
    const frame = frameRef.current;
    if (!frame) return;
    frame.querySelectorAll(".kf-selected").forEach((el) => el.classList.remove("kf-selected"));
    if (!selected) {
      frame.classList.remove("has-selection");
      return;
    }
    const matches = frame.querySelectorAll(selectorFor(selected));
    // Se l'entita' non e' in questo fotogramma (p.es. R1R2eq in Prima),
    // non si oscura niente: l'evidenza appare passando all'altro.
    if (matches.length === 0) {
      frame.classList.remove("has-selection");
      return;
    }
    frame.classList.add("has-selection");
    matches.forEach((el) => el.classList.add("kf-selected"));
  }, [svg, selected]);

  useEffect(() => {
    const frame = frameRef.current;
    if (!frame || !stableVb) return;
    frame.querySelectorAll("svg").forEach((el) => el.setAttribute("viewBox", stableVb));
  }, [svg, stableVb]);

  return (
    <figure className="kf-stage-frame" style={{ margin: 0 }} ref={frameRef}>
      {/* Il click e' una scorciatoia per chi usa il puntatore; la via da
          tastiera e' l'elenco di entita' nell'ispettore (bottoni veri).
          L'SVG porta gia' il proprio role=img con titolo e descrizione. */}
      <div
        onClick={(ev) => {
          const frame = frameRef.current;
          if (!frame) return;
          onSelectEntity(entityNear(frame, ev.clientX, ev.clientY));
        }}
        // Le stringhe SVG sono byte certificati dal kernel (build-time),
        // mai input utente: l'iniezione qui e' il canale di proiezione.
        dangerouslySetInnerHTML={{ __html: svg }}
      />
      <figcaption className="kf-stage-caption">{caption}</figcaption>
    </figure>
  );
}
