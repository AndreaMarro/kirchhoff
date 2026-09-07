import { kindLabel } from "../session/labels.ts";
import type { StepView } from "../session/types.ts";

export function StepInspector({ step }: { step: StepView }): React.JSX.Element {
  return (
    <section className="kf-card" aria-label="Dettaglio del passo">
      <p className="kf-card-title-micro">
        {step.kind === "transform" ? "Trasformazione" : "Passo analitico"} {step.index + 1}
      </p>
      <h3>{kindLabel(step.action ?? step.kind)}</h3>
      {step.equation ? (
        <div className="kf-equation" role="math" aria-label={`Equazione: ${step.equation}`}>
          {step.equation}
        </div>
      ) : null}
      {step.equations.length > 1 ? (
        <dl className="kf-kv">
          {step.equations.slice(1).map((eq, i) => (
            <div key={i} style={{ display: "contents" }}>
              <dt>eq. {i + 2}</dt>
              <dd>
                <code>{eq}</code>
              </dd>
            </div>
          ))}
        </dl>
      ) : null}
    </section>
  );
}
