import { useEffect, useRef } from "react";
import type { ExerciseIndexEntry } from "../../session/types.ts";

interface Props {
  exercises: ExerciseIndexEntry[];
  current: string;
  onSelect: (id: string) => void;
}

export function ExercisePicker({ exercises, current, onSelect }: Props): React.JSX.Element {
  const corrente = useRef<HTMLButtonElement | null>(null);
  /* Con 11 voci la barra scorre in orizzontale: la scelta corrente resta
     visibile senza ridisegno del selettore. Solo scorrimento del contenitore,
     mai della pagina (block: nearest su riga gia' visibile non sposta nulla). */
  useEffect(() => {
    corrente.current?.scrollIntoView({ block: "nearest", inline: "nearest" });
  }, [current]);
  return (
    <nav className="kf-picker" aria-label="Esercizi">
      {exercises.map((ex) => (
        <button
          key={ex.id}
          type="button"
          ref={ex.id === current ? corrente : undefined}
          className="kf-chip"
          aria-current={ex.id === current}
          onClick={() => onSelect(ex.id)}
          title={ex.titolo}
        >
          {ex.titolo}
        </button>
      ))}
    </nav>
  );
}
