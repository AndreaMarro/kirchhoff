import type { ProvenanceView, VerificationView } from "../session/types.ts";

interface Props {
  verification: VerificationView;
  provenance: ProvenanceView | null;
}

export function EvidencePanel({ verification, provenance }: Props): React.JSX.Element {
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
    </details>
  );
}
