import { quantityLabel } from "../session/labels.ts";
import type { AnswerView } from "../session/types.ts";

export function ExactAnswer({ answer }: { answer: AnswerView }): React.JSX.Element {
  return (
    <section className="kf-card kf-answer" aria-label="Risposta esatta">
      <p className="kf-card-title-micro">Risposta esatta</p>
      <div className="kf-answer-exact">
        {answer.exact} {answer.unit}
      </div>
      <div className="kf-answer-decimal">
        ≈ {answer.decimal} {answer.unit} · {quantityLabel(answer.quantity)} di {answer.target}
      </div>
    </section>
  );
}
