import { CircuitStage } from "../../components/CircuitStage.tsx";
import type { StageEntity } from "../../components/CircuitStage.tsx";
import { EntityInspector } from "../../components/EntityInspector.tsx";
import { EvidencePanel } from "../../components/EvidencePanel.tsx";
import { ExactAnswer } from "../../components/ExactAnswer.tsx";
import { ProofRail } from "../../components/ProofRail.tsx";
import { TruthLine } from "../../components/StatusPill.tsx";
import { StepControls } from "../../components/StepControls.tsx";
import { StepInspector } from "../../components/StepInspector.tsx";
import { FailureView, RefusalView } from "../refusal/RefusalView.tsx";
import { kindLabel, quantityLabel } from "../../session/labels.ts";
import type { StudentSessionView } from "../../session/types.ts";

export interface WorkbenchProps {
  session: StudentSessionView;
  step: number;
  frame: "before" | "after";
  entity: StageEntity | null;
  onStep: (s: number) => void;
  onFrame: (f: "before" | "after") => void;
  onEntity: (e: StageEntity | null) => void;
  onPrev: () => void;
  onNext: () => void;
}

export function Workbench(s: WorkbenchProps): React.JSX.Element {
  const { session } = s;
  if (session.outcome === "refusal" && session.refusal) {
    return <RefusalView refusal={session.refusal} question={session.question} />;
  }
  if (session.outcome === "failure" && session.failure) {
    return <FailureView failure={session.failure} />;
  }
  const current = s.step >= 0 ? session.steps[s.step] : null;
  const svg = current
    ? ((s.frame === "before" ? current.before_svg : current.after_svg) ??
      stateSvg(session, current.before_ref))
    : (session.states[0]?.svg ?? "");
  const compare =
    current?.before_svg && current.after_svg
      ? (s.frame === "before" ? current.after_svg : current.before_svg)
      : null;
  const caption =
    current !== null
      ? `${kindLabel(current.action ?? current.kind)} — ${s.frame === "before" ? "prima" : "dopo"}`
      : "Apertura — il circuito prima dell'azione";
  const openingEntities = current === null ? stateEntities(svg) : [];
  return (
    <>
      <ProofRail steps={session.steps} selected={s.step} onSelect={s.onStep} />
      <div className="kf-stage-wrap">
        <div className="kf-stage-head">
          <span className="kf-stage-question">
            {session.question ? (
              <code>
                {quantityLabel(session.question.quantity)} di {session.question.target}
              </code>
            ) : (
              "Sessione"
            )}
          </span>
          <TruthLine truth={session.truth} />
        </div>
        <div className="kf-stage">
          <CircuitStage
            svg={svg}
            compareWith={compare}
            selected={s.entity}
            onSelectEntity={s.onEntity}
            caption={caption}
          />
        </div>
      </div>
      <div className="kf-inspector">
        {session.answer ? <ExactAnswer answer={session.answer} /> : null}
        {current ? <StepInspector step={current} /> : null}
        {current ? (
          <EntityInspector
            affected={current.affected}
            preserved={current.preserved}
            selected={s.entity}
            onSelect={s.onEntity}
          />
        ) : (
          <OpeningEntities
            svg={svg}
            entities={openingEntities}
            answerTarget={session.answer?.target ?? null}
            answerExact={session.answer ? `${session.answer.exact} ${session.answer.unit}` : null}
            selected={s.entity}
            onSelect={s.onEntity}
          />
        )}
        {session.verification ? (
          <EvidencePanel verification={session.verification} provenance={session.provenance} />
        ) : null}
      </div>
      <StepControls
        canPrev={s.step > -1}
        canNext={s.step < session.steps.length - 1}
        frame={s.frame}
        frameEnabled={Boolean(current?.before_svg && current.after_svg)}
        onPrev={s.onPrev}
        onNext={s.onNext}
        onFrame={s.onFrame}
        answerCompact={session.answer ? `${session.answer.exact} ${session.answer.unit}` : null}
      />
    </>
  );
}

function stateSvg(session: StudentSessionView, ref: string): string {
  return session.states.find((st) => st.ref === ref)?.svg ?? "";
}

/** Entita' dello stato d'apertura, lette come stringhe dai byte esposti.
 *  Solo dicitura per l'interazione: nessun valore, salvo la risposta
 *  certificata quando l'entita' e' il bersaglio della domanda. */
function stateEntities(svg: string): { kind: string; id: string }[] {
  const seen = new Set<string>();
  const out: { kind: string; id: string }[] = [];
  for (const m of svg.matchAll(/data-component-id="([^"]+)"/g)) {
    const key = `component:${m[1]}`;
    if (!seen.has(key)) {
      seen.add(key);
      out.push({ kind: "component", id: m[1] });
    }
  }
  for (const m of svg.matchAll(/data-node-id="([^"]+)"/g)) {
    const key = `node:${m[1]}`;
    if (!seen.has(key)) {
      seen.add(key);
      out.push({ kind: "node", id: m[1] });
    }
  }
  return out;
}

function OpeningEntities(props: {
  svg: string;
  entities: { kind: string; id: string }[];
  answerTarget: string | null;
  answerExact: string | null;
  selected: { kind: string; id: string } | null;
  onSelect: (e: { kind: string; id: string } | null) => void;
}): React.JSX.Element {
  const { entities, answerTarget, answerExact, selected, onSelect } = props;
  if (entities.length === 0) return <></>;
  return (
    <section className="kf-card" aria-label="Entita' dello stato">
      <h3>Entità</h3>
      <div className="kf-entity-list">
        {entities.map((e) => (
          <button
            key={`${e.kind}:${e.id}`}
            type="button"
            className="kf-entity-btn"
            aria-pressed={selected !== null && selected.kind === e.kind && selected.id === e.id}
            onClick={() => onSelect(selected !== null && selected.kind === e.kind && selected.id === e.id ? null : e)}
          >
            <span className="kf-entity-kind" aria-hidden="true">
              {e.kind === "component" ? "▣" : "●"}
            </span>
            {e.id}
          </button>
        ))}
      </div>
      {selected ? (
        <dl className="kf-kv">
          <dt>Selezionata</dt>
          <dd>
            <code>
              {selected.kind === "component" ? "componente" : "nodo"}:{selected.id}
            </code>
          </dd>
          {answerTarget !== null && selected.id === answerTarget && answerExact !== null ? (
            <>
              <dt>Risposta</dt>
              <dd>
                <code>{answerExact}</code>
              </dd>
            </>
          ) : null}
        </dl>
      ) : null}
    </section>
  );
}
