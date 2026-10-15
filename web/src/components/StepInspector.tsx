import { kindLabel } from "../session/labels.ts";
import type { StepView } from "../session/types.ts";

export function StepInspector({ step, focusRef }: {
  step: StepView;
  focusRef?: React.Ref<HTMLElement>;
}): React.JSX.Element {
  const why = step.justification;
  return (
    <section ref={focusRef} tabIndex={-1} className="kf-card" aria-label="Dettaglio del passo">
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
      {step.kind === "transform" ? why ? (
        <details className="kf-justification">
          <summary>Perché posso farlo?</summary>
          <dl className="kf-kv">
            <dt>Terminali</dt>
            <dd><ul>{why.terminals.map(e => <li key={JSON.stringify([e.kind, e.id])}>
              Nodo <code>{e.id}</code>
            </li>)}</ul></dd>
            <dt>Precondizioni</dt>
            <dd><ol>{why.preconditions.map(condition => <li key={condition}>{condition}</li>)}</ol></dd>
            <dt>Formula</dt>
            <dd><code>{why.formula}</code></dd>
            <dt>Certificato</dt>
            <dd>
              <p>Operazione: <code>{why.certificate.operation}</code></p>
              <p>Controlli dichiarati:</p>
              <ul>{why.certificate.checks.map(check => <li key={check}><code>{check}</code></li>)}</ul>
              {why.certificate.attestations.length ? <>
                <p>Attestazioni di identità:</p>
                <ul>{why.certificate.attestations.map(a => <li key={JSON.stringify([a.entity.kind, a.entity.id])}>
                  <code>{a.entity.kind}:{a.entity.id}</code> · attributi: <code>{a.changed.join(", ")}</code>
                </li>)}</ul>
              </> : <p>Nessuna attestazione di identità dichiarata.</p>}
            </dd>
          </dl>
        </details>
      ) : <p className="kf-evidence-unavailable">Questa sessione non espone la giustificazione del passo.</p> : null}
    </section>
  );
}
