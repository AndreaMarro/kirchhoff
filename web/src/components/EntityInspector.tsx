import type { EntityView } from "../session/types.ts";
import type { StageEntity } from "./CircuitStage.tsx";

interface Props {
  affected: EntityView[];
  preserved: EntityView[];
  selected: StageEntity | null;
  onSelect: (e: StageEntity | null) => void;
}

function same(a: StageEntity | EntityView, b: StageEntity | EntityView): boolean {
  return a.kind === b.kind && a.id === b.id;
}

function kindLabel(kind: string): string {
  return kind === "component" ? "componente" : kind === "node" ? "nodo" : kind;
}

export function EntityInspector({ affected, preserved, selected, onSelect }: Props): React.JSX.Element {
  if (affected.length === 0 && preserved.length === 0) return <></>;
  const toggle = (e: EntityView): void => {
    onSelect(selected && same(selected, e) ? null : { kind: e.kind, id: e.id });
  };
  return (
    <section className="kf-card" aria-label="Entita' del passo">
      <h3>Entità</h3>
      {affected.length > 0 ? (
        <>
          <p className="kf-card-title-micro">Coinvolte</p>
          <div className="kf-entity-list">
            {affected.map((e) => (
              <button
                key={`${e.kind}:${e.id}`}
                type="button"
                className="kf-entity-btn"
                aria-pressed={selected !== null && same(selected, e)}
                onClick={() => toggle(e)}
              >
                <span className="kf-entity-kind" aria-hidden="true">
                  {e.kind === "component" ? "▣" : "●"}
                </span>
                {e.id}
              </button>
            ))}
          </div>
        </>
      ) : null}
      {preserved.length > 0 ? (
        <>
          <p className="kf-card-title-micro">Preservate</p>
          <div className="kf-entity-list">
            {preserved.map((e) => (
              <button
                key={`${e.kind}:${e.id}`}
                type="button"
                className="kf-entity-btn"
                aria-pressed={selected !== null && same(selected, e)}
                onClick={() => toggle(e)}
              >
                <span className="kf-entity-kind" aria-hidden="true">
                  {e.kind === "component" ? "▣" : "●"}
                </span>
                {e.id}
              </button>
            ))}
          </div>
        </>
      ) : null}
      {selected ? (
        <dl className="kf-kv">
          <dt>Selezionata</dt>
          <dd>
            <code>
              {kindLabel(selected.kind)}:{selected.id}
            </code>
          </dd>
        </dl>
      ) : null}
    </section>
  );
}
