/* Harness solo di test: vero Workbench e viste del produttore, mai incluso
   nell'entrypoint o nella directory public dell'applicazione. */
import { StrictMode, useState } from "react";
import { createRoot } from "react-dom/client";
import { Workbench } from "../../src/features/proof-workbench/Workbench.tsx";
import { parseSession } from "../../src/session/guards.ts";
import closedPayload from "../../public/sessions/scala-tre-riduzioni.json";
import bridgePayload from "../../public/sessions/ponte-nodale.json";
import refusalPayload from "../../public/sessions/rifiuto-domanda.json";
import "../../src/design/tokens.css";
import "../../src/app/app.css";

const closed = parseSession(closedPayload);
// Collisione deliberata del solo ID di presentazione: il focus deve appartenere
// all'oggetto sessione corrente, senza assumere unicità autenticata H3.
const bridge = parseSession({ ...bridgePayload, session_id: closed.session_id });
const refusal = parseSession(refusalPayload);
const failure = parseSession({
  ...refusalPayload, outcome: "failure", refusal: null,
  failure: { dove: "projection", messaggio: "Guasto sintetico del harness" },
});

function Harness(): React.JSX.Element {
  const [kind, setKind] = useState<"closed" | "bridge" | "refusal" | "failure">("closed");
  const [step, setStep] = useState(3);
  const [frame, setFrame] = useState<"before" | "after">("before");
  const [replace, setReplace] = useState(false);
  const [replaceAtTarget, setReplaceAtTarget] = useState(false);
  const session = { closed, bridge, refusal, failure }[kind];
  function choose(next: typeof kind): void {
    setKind(next); setStep(next === "closed" ? 3 : -1); setFrame("before");
  }
  return <>
    <div role="group" aria-label="Controlli del harness">
      <button onClick={() => choose("closed")}>Sessione chiusa</button>
      <button onClick={() => choose("refusal")}>Sessione rifiutata</button>
      <button onClick={() => choose("failure")}>Sessione guasta</button>
      <label><input type="checkbox" checked={replace} onChange={e => setReplace(e.target.checked)}/>
        Sostituisci sessione al prossimo salto</label>
      <label><input type="checkbox" checked={replaceAtTarget} onChange={e => setReplaceAtTarget(e.target.checked)}/>
        Nuova sessione già al passo richiesto</label>
    </div>
    <main className="kf-main">
      <Workbench session={session} step={step} frame={frame} entity={null}
        onStep={next => {
          if (replace) {
            setKind("bridge"); setStep(replaceAtTarget ? next : -1); setFrame("before"); setReplace(false);
          }
          else setStep(next);
        }}
        onFrame={setFrame} onEntity={() => {}}
        onPrev={() => setStep(s => Math.max(-1, s - 1))}
        onNext={() => setStep(s => Math.min(session.steps.length - 1, s + 1))}/>
    </main>
  </>;
}

createRoot(document.getElementById("test-root")!).render(<StrictMode><Harness/></StrictMode>);
