/* Specchio TypeScript di StudentSessionView (student-session.v0.1).
   Solo stato di presentazione: mai leggi di Kirchhoff, mai soluzioni. */

export const SCHEMA_VERSION = "student-session.v0.1";

export type Outcome = "closed" | "refusal" | "failure";

export interface QuestionView {
  request_id: string;
  quantity: string;
  target: string;
}

export interface AnswerView {
  target: string;
  quantity: string;
  exact: string;
  decimal: string;
  unit: string;
}

export interface TruthView {
  electrical_claim_status: string | null;
  backend_closure_status: string | null;
  product_verified: boolean;
}

export interface StateView {
  ref: string;
  svg: string;
  description: string;
}

export interface EntityView {
  kind: string;
  id: string;
}

export interface StepView {
  index: number;
  kind: string;
  before_ref: string;
  after_ref: string;
  action: string | null;
  equation: string | null;
  equations: string[];
  affected: EntityView[];
  preserved: EntityView[];
  evidence_refs: string[];
  before_svg: string | null;
  after_svg: string | null;
}

export interface VerificationView {
  claim_status: string | null;
  claim_verifier: string | null;
  claim_version: string | null;
  claim_subjects: string[];
  session_status: string | null;
  evidence_ids: string[];
}

export interface ProvenanceView {
  producer: string;
  source_sha: string;
  detail: string;
}

export interface RefusalView {
  cause: string;
  subject: string;
  subject_kind: string;
  diagnosis: string;
}

export interface FailureView {
  dove: string;
  messaggio: string;
}

export interface StudentSessionView {
  schema_version: string;
  session_id: string;
  outcome: Outcome;
  question: QuestionView | null;
  answer: AnswerView | null;
  truth: TruthView;
  states: StateView[];
  steps: StepView[];
  verification: VerificationView | null;
  provenance: ProvenanceView | null;
  refusal: RefusalView | null;
  failure: FailureView | null;
}

export interface ExerciseIndexEntry {
  id: string;
  titolo: string;
  outcome: Outcome;
  domanda: { quantity: string; target: string };
  risposta_esatta?: string;
  rifiuto?: { cause: string; diagnosis: string };
}
