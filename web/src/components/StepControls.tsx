interface Props {
  canPrev: boolean;
  canNext: boolean;
  frame: "before" | "after";
  frameEnabled: boolean;
  onPrev: () => void;
  onNext: () => void;
  onFrame: (f: "before" | "after") => void;
  answerCompact: string | null;
}

export function StepControls({
  canPrev,
  canNext,
  frame,
  frameEnabled,
  onPrev,
  onNext,
  onFrame,
  answerCompact,
}: Props): React.JSX.Element {
  return (
    <div className="kf-controls">
      <button type="button" className="kf-btn" disabled={!canPrev} onClick={onPrev} aria-label="Passo precedente">
        ← <span aria-hidden="true">Indietro</span>
      </button>
      <button type="button" className="kf-btn" disabled={!canNext} onClick={onNext} aria-label="Passo successivo">
        <span aria-hidden="true">Avanti</span> →
      </button>
      <div className="kf-segment" role="group" aria-label="Prima o dopo">
        <button
          type="button"
          aria-pressed={frame === "before"}
          disabled={!frameEnabled}
          onClick={() => onFrame("before")}
        >
          Prima
        </button>
        <button
          type="button"
          aria-pressed={frame === "after"}
          disabled={!frameEnabled}
          onClick={() => onFrame("after")}
        >
          Dopo
        </button>
      </div>
      {answerCompact ? (
        <span className="kf-controls-answer" aria-label={`Risposta esatta ${answerCompact}`}>
          {answerCompact}
        </span>
      ) : null}
      <span className="kf-controls-hint" aria-hidden="true">
        <kbd>←</kbd> <kbd>→</kbd> passi · <kbd>B</kbd> prima · <kbd>A</kbd> dopo
      </span>
    </div>
  );
}
