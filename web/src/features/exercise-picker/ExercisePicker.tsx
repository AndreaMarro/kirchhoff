import type { ExerciseIndexEntry } from "../../session/types.ts";

interface Props {
  exercises: ExerciseIndexEntry[];
  current: string;
  onSelect: (id: string) => void;
}

export function ExercisePicker({ exercises, current, onSelect }: Props): React.JSX.Element {
  return (
    <nav className="kf-picker" aria-label="Esercizi">
      {exercises.map((ex) => (
        <button
          key={ex.id}
          type="button"
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
