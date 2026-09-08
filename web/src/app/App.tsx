import { useCallback, useEffect, useState } from "react";
import { loadIndex, loadSession } from "../session/source.ts";
import type { ExerciseIndexEntry, StudentSessionView } from "../session/types.ts";
import { ExercisePicker } from "../features/exercise-picker/ExercisePicker.tsx";
import { Workbench } from "../features/proof-workbench/Workbench.tsx";
import type { StageEntity } from "../components/CircuitStage.tsx";
import { StatusPill } from "../components/StatusPill.tsx";
import { useSelection, useTheme } from "./state.ts";

export function App(): React.JSX.Element {
  const [index, setIndex] = useState<ExerciseIndexEntry[] | null>(null);
  const [session, setSession] = useState<StudentSessionView | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [entity, setEntity] = useState<StageEntity | null>(null);
  const [theme, toggleTheme] = useTheme();
  const ids = (index ?? []).map((e) => e.id);
  const [selection, setSelection] = useSelection(ids);

  useEffect(() => {
    loadIndex().then(setIndex).catch((e: unknown) => setError(String(e)));
  }, []);

  useEffect(() => {
    if (index === null) return;
    const target = index.some((e) => e.id === selection.exercise) ? selection.exercise : index[0]?.id;
    if (!target) return;
    if (target !== selection.exercise) {
      setSelection({ exercise: target, step: -1, frame: "before" });
      return;
    }
    setSession(null);
    setEntity(null);
    loadSession(target).then(setSession).catch((e: unknown) => setError(String(e)));
  }, [index, selection.exercise, setSelection]);

  const stepCount = session?.steps.length ?? 0;
  const step = session && (selection.step < -1 || selection.step >= stepCount) ? -1 : selection.step;

  const goStep = useCallback(
    (delta: number) => {
      const next = Math.min(stepCount - 1, Math.max(-1, step + delta));
      setSelection({ ...selection, step: next });
    },
    [step, selection, setSelection, stepCount],
  );

  useEffect(() => {
    const onKey = (ev: KeyboardEvent): void => {
      if (ev.metaKey || ev.ctrlKey || ev.altKey) return;
      if (ev.key === "ArrowRight") goStep(1);
      else if (ev.key === "ArrowLeft") goStep(-1);
      else if (ev.key === "b" || ev.key === "B") setSelection({ ...selection, frame: "before" });
      else if (ev.key === "a" || ev.key === "A") setSelection({ ...selection, frame: "after" });
      else return;
      ev.preventDefault();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [goStep, selection, setSelection]);

  return (
    <>
      <header className="kf-bar">
        <div className="kf-brand">
          Kirchhoff <span>Proof Workbench</span>
        </div>
        <div className="kf-bar-title">{session ? exerciseTitle(index, selection.exercise) : ""}</div>
        {session ? <StatusPill outcome={session.outcome} /> : null}
        <CopyLink />
        <button type="button" className="kf-theme-toggle" onClick={toggleTheme} aria-label="Cambia tema">
          {theme === "dark" ? "Tema chiaro" : "Tema scuro"}
        </button>
      </header>
      {index ? (
        <ExercisePicker
          exercises={index}
          current={selection.exercise}
          onSelect={(id) => setSelection({ exercise: id, step: -1, frame: "before" })}
        />
      ) : null}
      <main className="kf-main">
        {error ? (
          <div className="kf-notice kf-notice-failure" role="alert">
            <h2>Guasto</h2>
            <p className="kf-mono">{error}</p>
          </div>
        ) : session ? (
          <Workbench
            session={session}
            step={step}
            frame={selection.frame}
            entity={entity}
            onStep={(s) => setSelection({ ...selection, step: s })}
            onFrame={(f) => setSelection({ ...selection, frame: f })}
            onEntity={setEntity}
            onPrev={() => goStep(-1)}
            onNext={() => goStep(1)}
          />
        ) : (
          <div className="kf-center">Caricamento della sessione certificata…</div>
        )}
      </main>
    </>
  );
}

function exerciseTitle(index: ExerciseIndexEntry[] | null, id: string): string {
  return index?.find((e) => e.id === id)?.titolo ?? "";
}

function CopyLink(): React.JSX.Element {
  const [copiato, setCopiato] = useState(false);
  return (
    <button
      type="button"
      className="kf-theme-toggle"
      aria-label="Copia il link a questo passo"
      aria-live="polite"
      onClick={() => {
        const href = window.location.href;
        const done = (): void => {
          setCopiato(true);
          window.setTimeout(() => setCopiato(false), 2000);
        };
        if (navigator.clipboard?.writeText) {
          navigator.clipboard.writeText(href).then(done, () => undefined);
        }
      }}
    >
      {copiato ? "Copiato" : "Copia link"}
    </button>
  );
}
