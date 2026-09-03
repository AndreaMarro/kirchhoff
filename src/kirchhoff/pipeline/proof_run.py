"""Confine applicativo Proof Demo: da (IR, Request) alla chiusura durevole.

`run_proof_session` e' l'unica via applicativa canonica verso la chiusura di
backend (`ProofSessionClosure` = sessione + registro): orchestra, propaga il
Refusal identico, costruisce il registro canonico, compone la sessione — che
giunge gia' validata live dal compositore — e trattiene la chiusura per H3.

Non e' il gate finale AD-5 (che resta futuro e riserva il nome publish):
niente badge prodotto, niente render, niente serializzazione, niente hash,
niente re-solve, niente seconda validazione live, niente validazione durevole
anticipata. Ogni stadio semantico resta del suo proprietario: orchestrazione
al dominio didattico, registro a `componi_registro`, sessione al compositore.

Mappa dei guasti (AD-13): Refusal = esito onesto di dominio, propagato
identico e mai costruito qui; Failure = difetto applicativo o ingresso
corrotto, nominato per stadio (`clock`, `entropy`, `orchestrate`, `registry`,
`boundary`; `compose` passa l'originale del compositore). Le guardie ampie
sono solo due e documentate: fornitore di entropia e orologio sono ingressi
non fidati del chiamante, e il confine esterno non lascia mai attraversare
un'eccezione imprevista senza causa conservata.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from kirchhoff.domain.didactic.orchestrate import (
    CertifiedDidacticRun,
    orchestrate_didactic_run,
)
from kirchhoff.domain.identity import conia
from kirchhoff.domain.ir import IR, Request
from kirchhoff.domain.proof.session import ProofSession
from kirchhoff.domain.refusal import Refusal
from kirchhoff.pipeline.failure import Failure
from kirchhoff.pipeline.proof_session import compose_proof_session
from kirchhoff.pipeline.state_registry import (
    CircuitStateRegistry,
    StateRef,
    componi_registro,
)
from kirchhoff.ports.clock import ClockPort

#: Entropia iniettata dal chiamante, dieci byte freschi per ogni attinta.
#: Niente EntropyPort: lo spine non ne ha uno e un port nuovo sarebbe
#: un'estensione architetturale oltre questo gate (D-H2.75).
EntropySource = Callable[[], bytes]

_ENTROPIA_BYTE = 10
_EPOCA = datetime(1970, 1, 1, tzinfo=timezone.utc)
_MASSIMO_ULID = 1 << 48


class _ErroreEntropia(ValueError):
    """Fornitore di entropia guasto o riusato: sempre Failure, mai Refusal."""


@dataclass(frozen=True, slots=True)
class ProofSessionClosure:
    """Sessione pubblicata + registro che la rende autosufficiente (H2.5).

    Guardie superficiali soltanto: tipi e risolvibilita' di ogni state ref
    (il legame vive qui, non un duplicato delle invarianti di sessione).
    La coerenza profonda e' garantita dal compositore a monte: questa
    chiusura nasce solo da `run_proof_session` dopo composizione riuscita.
    """

    session: ProofSession
    registry: CircuitStateRegistry

    def __post_init__(self) -> None:
        if not isinstance(self.session, ProofSession):
            raise TypeError(
                f"chiusura con {type(self.session).__name__} invece di "
                "ProofSession")
        if not isinstance(self.registry, CircuitStateRegistry):
            raise TypeError(
                f"chiusura con {type(self.registry).__name__} invece di "
                "CircuitStateRegistry")
        for ref in self.session.state_refs:
            try:
                self.registry.resolve(StateRef(ref))
            except KeyError as exc:
                raise ValueError(
                    f"state ref {ref} senza legame nel registro: "
                    "chiusura incoerente") from exc


class _SorgenteEntropia:
    """Attinge byte freschi dal fornitore del chiamante.

    Ogni attinta valida tipo, lunghezza e freschezza dentro la run: un riuso
    conierebbe identificatori duplicati e il registro solleverebbe
    un'accusa contro chi deposita per un difetto di chi fornisce entropia.
    """

    def __init__(self, entropy: EntropySource) -> None:
        self._sorgente = entropy
        self._usate: set[bytes] = set()

    def attingi(self) -> bytes:
        try:
            blob = self._sorgente()
        except StopIteration as exc:
            raise _ErroreEntropia(
                "entropia esaurita: il fornitore non ha piu' byte") from exc
        except Exception as exc:
            raise _ErroreEntropia(
                f"fornitore di entropia guasto: {exc!r}") from exc
        if not isinstance(blob, (bytes, bytearray)):
            raise _ErroreEntropia(
                f"entropia {type(blob).__name__} invece di bytes")
        blob = bytes(blob)
        if len(blob) != _ENTROPIA_BYTE:
            raise _ErroreEntropia(
                f"entropia di {len(blob)} byte invece di {_ENTROPIA_BYTE}")
        if blob in self._usate:
            raise _ErroreEntropia(
                "entropia duplicata dentro la stessa run: dieci byte freschi "
                "a ogni conio")
        self._usate.add(blob)
        return blob

    def nuovo_id(self, istante: int) -> str:
        return conia("ir", istante, self.attingi())

    def nuovo_ref(self, istante: int) -> StateRef:
        return StateRef(self.nuovo_id(istante))


def _millisecondi(clock: ClockPort) -> int:
    """L'istante ULID dall'orologio iniettato, con aritmetica esatta.

    Niente `timestamp()` float: differenza di datetime divisa per
    millisecondo, intero esatto. Il limite superiore ULID e' irraggiungibile
    da un datetime (anno max 9999 << 2^48 ms) e non si controlla cio' che non
    puo' accadere; il negativo si rifiuta qui perche' conia lo rifiuterebbe
    fuori dal confine nominato.
    """
    attimo = clock.now()
    if not isinstance(attimo, datetime):
        raise TypeError(
            f"orologio con {type(attimo).__name__} invece di datetime")
    if attimo.tzinfo is None or attimo.utcoffset() is None:
        raise ValueError("orologio senza fuso UTC esplicito")
    ms = (attimo - _EPOCA) // timedelta(milliseconds=1)
    if ms < 0:
        raise ValueError("istante prima dell'epoca ULID")
    return ms


def _limite_stati(initial_ir: IR) -> int:
    """Quanti state-id bastano: componenti iniziali + 1.

    Ogni trasformazione riduce strettamente i componenti (l'orchestratore lo
    impone: senza riduzione e' ValueError), quindi gli stati operativi sono
    al piu' componenti+1. Niente 6/10/100 dal folklore delle fixture: il
    limite si dimostra dall'invariante che lo stesso orchestratore fa valere.
    """
    return len(initial_ir.components) + 1


def run_proof_session(
    initial_ir: IR,
    original_request: Request,
    *,
    clock: ClockPort,
    entropy: EntropySource,
    document_profile: str,
    source_sha: str,
    detail: str,
) -> ProofSessionClosure | Refusal | Failure:
    """Dalla richiesta alla chiusura durevole: un solo percorso applicativo.

    Il chiamante fornisce IR, Request, metadati dichiarati e due ingressi
    iniettati (orologio, entropia). Il confine possiede: supply degli
    identificatori, propagazione del Refusal, costruzione del registro,
    input di occurrence, invocazione del compositore, ritenzione della
    chiusura. Non pianifica, non risolve, non certifica, non disegna.
    """
    try:
        istante = _millisecondi(clock)
    except Exception as exc:
        return Failure("clock", f"orologio non utilizzabile: {exc}")
    sorgente = _SorgenteEntropia(entropy)
    try:
        n_stati = _limite_stati(initial_ir)
    except AttributeError as exc:
        return Failure(
            "orchestrate", f"ingresso non valido per l'orchestrazione: {exc}")
    try:
        state_ids = tuple(sorgente.nuovo_id(istante) for _ in range(n_stati))
        run = orchestrate_didactic_run(
            initial_ir, original_request, state_ids=state_ids)
    except _ErroreEntropia as exc:
        return Failure("entropy", str(exc))
    except (TypeError, ValueError, RuntimeError) as exc:
        return Failure("orchestrate", f"orchestrazione impossibile: {exc}")
    if isinstance(run, Refusal):
        return run
    assert isinstance(run, CertifiedDidacticRun)
    try:
        evidence = tuple(
            sorgente.nuovo_ref(istante)
            for _ in range(len(run.transform_executions)))
        registro = componi_registro(run, refs_evidenza=evidence)
    except _ErroreEntropia as exc:
        return Failure("entropy", str(exc))
    except (TypeError, ValueError, RuntimeError, AttributeError, KeyError) as exc:
        return Failure("registry", f"registro non componibile: {exc}")
    try:
        sessione = compose_proof_session(
            run, registro, session_instant_ms=istante,
            session_entropy=sorgente.attingi(),
            document_profile=document_profile,
            source_sha=source_sha, detail=detail)
    except _ErroreEntropia as exc:
        return Failure("entropy", str(exc))
    except Exception as exc:
        return Failure(
            "boundary", f"guasto imprevisto al confine applicativo: {exc!r}")
    if isinstance(sessione, Failure):
        return sessione
    return ProofSessionClosure(session=sessione, registry=registro)
