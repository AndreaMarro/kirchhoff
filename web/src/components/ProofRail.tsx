import { kindLabel } from "../session/labels.ts";
import type { StepView } from "../session/types.ts";

interface Props {
  steps: StepView[];
  selected: number;
  onSelect: (step: number) => void;
}

function label(step: StepView): string {
  if (step.kind === "transform") return kindLabel(step.action ?? "trasformazione");
  return kindLabel(step.action ?? "passo analitico");
}

function sub(step: StepView): string | null {
  if (step.kind === "transform") return step.equation;
  const eq = step.equations[0];
  return eq ?? null;
}

export function ProofRail({ steps, selected, onSelect }: Props): React.JSX.Element {
  return (
    <nav className="kf-rail" aria-label="Passi della dimostrazione">
      <div className="kf-rail-title" aria-hidden="true">
        Dimostrazione
      </div>
      <button
        type="button"
        className="kf-rail-step"
        aria-current={selected === -1}
        onClick={() => onSelect(-1)}
      >
        <span className="kf-rail-index" aria-hidden="true">
          ○
        </span>
        <span className="kf-rail-label">Apertura</span>
      </button>
      {steps.map((step, i) => (
        <button
          key={step.index}
          type="button"
          className="kf-rail-step"
          aria-current={selected === i}
          onClick={() => onSelect(i)}
        >
          <span className="kf-rail-index" aria-hidden="true">
            {i + 1}
          </span>
          <span className="kf-rail-label">
            {label(step)}
            {sub(step) ? <small>{sub(step)}</small> : null}
          </span>
        </button>
      ))}
    </nav>
  );
}
