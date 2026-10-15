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
      {provenance ? (
        <div className="kf-evidence-row">
          <span className="kf-check" aria-hidden="true">
            ✓
          </span>
          <span>
            revisione <code>{provenance.source_sha.slice(0, 12)}</code> · {provenance.detail}
          </span>
        </div>
      ) : null}
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
