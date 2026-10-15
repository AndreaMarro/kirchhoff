import { kindLabel } from "../session/labels.ts";
import type { ProvenanceView, StepView, VerificationView } from "../session/types.ts";

interface Props {
  verification: VerificationView;
  provenance: ProvenanceView | null;
  steps: StepView[];
  onStep: (index: number) => void;
}

export function EvidencePanel({ verification, provenance, steps, onStep }: Props): React.JSX.Element {
  // parseSession ha già verificato unicità, completezza e corrispondenza.
  // Gli ID restano opachi: nessuna cifra viene convertita in un indice.
  const targets = verification.evidence_ids.map(id => ({
    id, step: steps.find(step => step.kind === "analytical" && step.derivation_ref === id),
  }));
  const linked = targets.every(target => target.step !== undefined);
  return (
    <details className="kf-card kf-evidence">
      <summary>Perché fidarsi</summary>
      <div className="kf-evidence-row">
        <span className="kf-check" aria-hidden="true">
          ✓
        </span>
        <span>
          Claim elettrico: <strong>{verification.claim_status}</strong> · Sessione backend:{" "}
          <strong>{verification.session_status}</strong>
        </span>
      </div>
      <div className="kf-evidence-row">
        <span className="kf-check" aria-hidden="true">
          ✓
        </span>
        <span className="kf-mono">
          {verification.claim_verifier} {verification.claim_version}
        </span>
      </div>
      <div className="kf-evidence-row">
        <span className="kf-check" aria-hidden="true">
          ✓
        </span>
        <span>
          Soggetti: <code>{verification.claim_subjects.join(", ")}</code>
        </span>
      </div>
      <section className="kf-evidence-provenance" aria-label="Provenienza dichiarata">
        <h3 className="kf-card-title-micro">Provenienza dichiarata</h3>
        {provenance ? <>
          <dl>
            <dt>Produttore</dt>
            <dd><code>{provenance.producer.trim() ? provenance.producer : "Non dichiarato"}</code></dd>
            <dt>Revisione sorgente</dt>
            <dd><code>{provenance.source_sha.trim() ? provenance.source_sha : "Non dichiarata"}</code></dd>
            <dt>Contesto</dt>
            <dd>{provenance.detail.trim() ? provenance.detail : "Non dichiarato"}</dd>
          </dl>
          <p className="kf-evidence-unavailable">
            Questi metadati sono dichiarati dal produttore; non attestano l’autenticità della sessione.
          </p>
        </> : <p className="kf-evidence-unavailable">Provenienza non disponibile per questa sessione.</p>}
      </section>
      <div className="kf-evidence-steps">
        <p className="kf-card-title-micro">Derivazioni del Claim</p>
        {!linked ? <p className="kf-evidence-unavailable">
          Questa sessione non espone il collegamento tra derivazione e passo.
        </p> : null}
        <ul className="kf-evidence-links">
          {targets.map(({ id, step }) => <li key={id}>
            {linked && step ? <button type="button" onClick={() => onStep(step.index)}>
              {id} — {kindLabel(step.action ?? step.kind)} · passo {step.index + 1}
            </button> : <code>{id}</code>}
          </li>)}
        </ul>
      </div>
    </details>
  );
}
