import type { FailureView, QuestionView, RefusalView } from "../../session/types.ts";
import { quantityLabel } from "../../session/labels.ts";

export function RefusalView({
  refusal,
  question,
}: {
  refusal: RefusalView;
  question: QuestionView | null;
}): React.JSX.Element {
  return (
    <div className="kf-notice kf-notice-refusal" role="status">
      <h2>Non certificata</h2>
      <p>
        Kirchhoff ha lavorato onestamente e si rifiuta di mostrare una risposta autorevole
        {question ? (
          <>
            {" "}
            per{" "}
            <code>
              {quantityLabel(question.quantity)} di {question.target}
            </code>
          </>
        ) : null}
        .
      </p>
      <div className="kf-diagnosis">{refusal.diagnosis}</div>
      <dl className="kf-kv">
        <dt>Controllo</dt>
        <dd>
          <code>{refusal.cause}</code>
        </dd>
        <dt>Soggetto</dt>
        <dd>
          <code>
            {refusal.subject_kind}:{refusal.subject}
          </code>
        </dd>
      </dl>
      <p>
        Non e' un errore tuo e non e' un guasto: e' il sistema che dice di non poter
        certificare. Nessun numero parziale viene inventato.
      </p>
    </div>
  );
}

export function FailureView({ failure }: { failure: FailureView }): React.JSX.Element {
  return (
    <div className="kf-notice kf-notice-failure" role="alert">
      <h2>Guasto</h2>
      <p>Qualcosa nell'applicazione non ha funzionato. Non e' un rifiuto onesto: e' un difetto.</p>
      <dl className="kf-kv">
        <dt>Stadio</dt>
        <dd>
          <code>{failure.dove}</code>
        </dd>
        <dt>Dettaglio</dt>
        <dd>
          <code>{failure.messaggio}</code>
        </dd>
      </dl>
    </div>
  );
}
