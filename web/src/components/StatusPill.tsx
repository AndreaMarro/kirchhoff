import type { TruthView } from "../session/types.ts";

const LABEL: Record<string, string> = {
  closed: "Risposta verificata",
  refusal: "Non certificata",
  failure: "Guasto",
};

export function StatusPill({ outcome }: { outcome: keyof typeof LABEL }): React.JSX.Element {
  const cls =
    outcome === "closed"
      ? "kf-pill kf-pill-verified"
      : outcome === "refusal"
        ? "kf-pill kf-pill-refusal"
        : "kf-pill kf-pill-failure";
  return (
    <span className={cls} role="status">
      <span className="kf-dot" aria-hidden="true" />
      {LABEL[outcome]}
    </span>
  );
}

export function TruthLine({ truth }: { truth: TruthView }): React.JSX.Element | null {
  if (truth.electrical_claim_status === null) return null;
  return (
    <span className="kf-mono" style={{ fontSize: "var(--kf-type-small)" }}>
      Claim {truth.electrical_claim_status} · Sessione {truth.backend_closure_status}
    </span>
  );
}
