"""H2.75 — il confine applicativo Proof Demo e' produzione, non imitazione.

`run_proof_session` e' l'unica via applicativa da (IR, Request) alla chiusura
durevole (ProofSession + registry): orchestra, propaga il Refusal identico,
costruisce il registro canonico, compone la sessione (che gia' valida live),
trattiene la chiusura. Niente publish AD-5, niente render, niente serialize,
niente hash, niente re-solve, niente doppia validazione.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import datetime, timezone
from fractions import Fraction

import pytest

from kirchhoff.domain.didactic.orchestrate import (
    CertifiedDidacticRun,
    orchestrate_didactic_run,
)
from kirchhoff.domain.identity import conia, verifica
from kirchhoff.domain.ir import IR
from kirchhoff.domain.refusal import Refusal
from kirchhoff.pipeline.failure import Failure
from kirchhoff.pipeline.netlist import leggi
from kirchhoff.pipeline.proof_run import (
    ProofSessionClosure,
    run_proof_session,
)

D1 = """\
V1 b 0 12 volt
R1 b a 100 ohm
R2 a 0 220 ohm
? current R1
"""

PONTE = """\
V1 b 0 12 volt
R1 b x 100 ohm
R2 x 0 200 ohm
R3 b y 300 ohm
R4 y 0 400 ohm
R5 x y 500 ohm
? current R5
"""

FUORI_CAPABILITY = """\
V1 b 0 12 volt
R1 b a 100 ohm
C1 a 0 1 farad
? current R1
"""

SHA_FIXTURE = "0123456789abcdef0123456789abcdef01234567"
ATTIMO = datetime(2026, 9, 3, 19, 0, 0, tzinfo=timezone.utc)
ATTIMO_MS = calendar.timegm((2026, 9, 3, 19, 0, 0, 0, 0, 0)) * 1000


@dataclass(frozen=True)
class OrologioFermo:
    attimo: datetime = ATTIMO

    def now(self) -> datetime:
        return self.attimo


def sorgente(*entropie: bytes):
    """EntropySource deterministica da sequenza finita (esaureibile)."""
    coda = list(entropie)

    def attingi() -> bytes:
        if not coda:
            raise StopIteration("entropia esaurita")
        return coda.pop(0)

    return attingi


def _entropia(n: int) -> bytes:
    return bytes((n + 101,)) * 10


def _serie(n: int, primo: int = 0):
    return sorgente(*(_entropia(primo + i) for i in range(n)))


def _ir_richiesta(netlist: str):
    ir = leggi(netlist)
    return ir, next(iter(ir.requests))


def _chiusura_d1(**kwargs):
    ir, richiesta = _ir_richiesta(D1)
    parametri = {
        "clock": OrologioFermo(),
        "entropy": _serie(20),
        "document_profile": "student-pdf.v0.1",
        "source_sha": SHA_FIXTURE,
        "detail": "fixture H2.75",
    }
    parametri.update(kwargs)
    return run_proof_session(ir, richiesta, **parametri)


# --- A: D1 end-to-end ------------------------------------------------------------


def test_a_d1_chiusura_backend():
    esito = _chiusura_d1()
    assert isinstance(esito, ProofSessionClosure)
    assert esito.session.publication_status == "CLOSED"
    assert esito.session.final_claim.status == "VERIFIED"
    assert esito.session.final_solution.value.amount == Fraction(3, 80)
    assert esito.session.final_solution.value.unit == "ampere"


# --- B: il registro resta ----------------------------------------------------------


def test_b_registro_trattenuto_e_risolvibile():
    from kirchhoff.pipeline.state_registry import StateRef

    esito = _chiusura_d1()
    assert isinstance(esito, ProofSessionClosure)
    registro = esito.registry
    assert registro.resolve(StateRef(esito.session.initial_state_ref)) is not None
    assert registro.resolve(StateRef(esito.session.final_state_ref)) is not None
    assert len(registro) >= len(esito.session.state_refs)


# --- C: Refusal identico, compositori mai chiamati ---------------------------------------


def test_c_rifiuto_identico_senza_comporre(monkeypatch):
    import kirchhoff.pipeline.proof_run as confine

    chiamate = []

    def _vietato(*args, **kwargs):
        chiamate.append(True)
        raise AssertionError("non deve essere chiamato dopo Refusal")

    monkeypatch.setattr(confine, "componi_registro", _vietato)
    monkeypatch.setattr(confine, "compose_proof_session", _vietato)
    ir, richiesta = _ir_richiesta(FUORI_CAPABILITY)
    esito = run_proof_session(
        ir, richiesta, clock=OrologioFermo(), entropy=_serie(20),
        document_profile="student-pdf.v0.1", source_sha=SHA_FIXTURE,
        detail="rifiuto H2.75")
    assert type(esito) is Refusal
    assert chiamate == []
    assert not isinstance(esito, (Failure, ProofSessionClosure))


def test_c_propagazione_per_identita(monkeypatch):
    import kirchhoff.pipeline.proof_run as confine

    sentinella = Refusal("unsolvable", "q9", "request", "sentinella")
    monkeypatch.setattr(
        confine, "orchestrate_didactic_run", lambda *a, **k: sentinella)
    ir, richiesta = _ir_richiesta(FUORI_CAPABILITY)
    esito = run_proof_session(
        ir, richiesta, clock=OrologioFermo(), entropy=_serie(20),
        document_profile="student-pdf.v0.1", source_sha=SHA_FIXTURE,
        detail="identita H2.75")
    assert esito is sentinella


# --- D: ponte zero-transform -------------------------------------------------------------


def test_d_ponte_chiuso():
    ir, richiesta = _ir_richiesta(PONTE)
    esito = run_proof_session(
        ir, richiesta, clock=OrologioFermo(), entropy=_serie(20),
        document_profile="student-pdf.v0.1", source_sha=SHA_FIXTURE,
        detail="ponte H2.75")
    assert isinstance(esito, ProofSessionClosure)
    assert esito.session.publication_status == "CLOSED"
    assert esito.session.final_claim.status == "VERIFIED"
    assert len(esito.session.state_refs) == 1
    from kirchhoff.pipeline.state_registry import StateRef

    assert esito.registry.resolve(
        StateRef(esito.session.final_state_ref)) == esito.registry.resolve(
            StateRef(esito.session.state_refs[0]))


# --- E: evidenza after letterale --------------------------------------------------------------


def test_e_after_letterale_trattenuto():
    esito = _chiusura_d1()
    assert isinstance(esito, ProofSessionClosure)
    ir, richiesta = _ir_richiesta(D1)
    from kirchhoff.domain.identity import conia as _conia

    run = orchestrate_didactic_run(
        ir, richiesta,
        state_ids=tuple(
            _conia("ir", 1700000000000 + i, bytes((i + 1,)) * 10)
            for i in range(3)))
    assert isinstance(run, CertifiedDidacticRun)
    dopo = run.transform_executions[0].after
    assert esito.registry.resolve(esito.registry.ref_for(dopo)) == dopo


# --- F/G: replay deterministico e fresh occurrence -----------------------------------------------


def test_f_replay_deterministico():
    prima = _chiusura_d1()
    seconda = _chiusura_d1()
    assert prima == seconda


def test_g_fresh_occurrence_stessa_semantica():
    ir, richiesta = _ir_richiesta(D1)
    prima = run_proof_session(
        ir, richiesta, clock=OrologioFermo(), entropy=_serie(20, primo=0),
        document_profile="student-pdf.v0.1", source_sha=SHA_FIXTURE,
        detail="occorrenza H2.75")
    ir, richiesta = _ir_richiesta(D1)
    seconda = run_proof_session(
        ir, richiesta, clock=OrologioFermo(), entropy=_serie(20, primo=50),
        document_profile="student-pdf.v0.1", source_sha=SHA_FIXTURE,
        detail="occorrenza H2.75")
    assert isinstance(prima, ProofSessionClosure)
    assert isinstance(seconda, ProofSessionClosure)
    assert (prima.session.final_solution.value
            == seconda.session.final_solution.value)
    # Stessa semantica di verifica (state_id e' occurrence, non semantica).
    for campo in ("claim_type", "subject_ids", "evidence_ids",
                  "verifier_id", "verifier_version", "status"):
        assert (getattr(prima.session.final_claim, campo)
                == getattr(seconda.session.final_claim, campo))
    assert prima.session.session_id != seconda.session.session_id
    assert prima.session.state_refs != seconda.session.state_refs
    assert prima != seconda


# --- H/I: entropia -----------------------------------------------------------------------


def test_h_entropia_duplicata_fallisce():
    esito = _chiusura_d1(entropy=sorgente(*([_entropia(0)] * 20)))
    assert type(esito) is Failure
    assert not isinstance(esito, Refusal)


def test_i_entropia_malformata_fallisce():
    for cattiva in ("casuale", b"corta", bytes(11)):
        esito = _chiusura_d1(
            entropy=sorgente(*([cattiva] * 20)))  # type: ignore[list-item]
        assert type(esito) is Failure, cattiva
        assert not isinstance(esito, Refusal)


def test_i_entropia_esaurita_fallisce_chiusa():
    esito = _chiusura_d1(entropy=sorgente())
    assert type(esito) is Failure
    assert "entrop" in esito.messaggio.lower()
    assert not isinstance(esito, Refusal)


def test_i_esaurimento_a_fasi_nominato():
    # D1 consuma 4 (supply) + 1 (evidenza) + 1 (sessione): l'esaurimento
    # in fase evidenza e in fase sessione mappa comunque a Failure entropy.
    assert type(_chiusura_d1(entropy=_serie(4))) is Failure
    assert type(_chiusura_d1(entropy=_serie(5))) is Failure


def test_i_fornitore_guasto_fallisce_chiuso():
    def _rotto() -> bytes:
        raise RuntimeError("sorgente rotta")

    esito = _chiusura_d1(entropy=_rotto)
    assert type(esito) is Failure
    assert esito.dove == "entropy"


def test_i_bytearray_accettato():
    esito = _chiusura_d1(entropy=sorgente(*(bytearray(_entropia(i)) for i in range(20))))
    assert isinstance(esito, ProofSessionClosure)


# --- J: orologio ---------------------------------------------------------------------------------


def test_j_orologio():
    esito = _chiusura_d1()
    assert isinstance(esito, ProofSessionClosure)

    class SenzaFuso:
        def now(self):
            return datetime(2026, 9, 3, 19, 0, 0)

    assert type(_chiusura_d1(clock=SenzaFuso())) is Failure

    class NonData:
        def now(self):
            return "ora"

    assert type(_chiusura_d1(clock=NonData())) is Failure

    class SenzaOra:
        pass

    assert type(_chiusura_d1(clock=SenzaOra())) is Failure

    @dataclass(frozen=True)
    class Passato:
        def now(self):
            return datetime(1960, 1, 1, tzinfo=timezone.utc)

    assert type(_chiusura_d1(clock=Passato())) is Failure


def test_j_conversione_istante_esatta():
    import kirchhoff.pipeline.proof_run as confine

    assert confine._millisecondi(OrologioFermo()) == ATTIMO_MS


# --- K: compositore chiamato una volta, nessuna doppia validazione ------------------------------------


def test_k_compositore_chiamato_una_volta(monkeypatch):
    import kirchhoff.pipeline.proof_run as confine
    from kirchhoff.pipeline import proof_session as compositore

    chiamate = []
    originale = compositore.compose_proof_session

    def spia(*args, **kwargs):
        chiamate.append(True)
        return originale(*args, **kwargs)

    monkeypatch.setattr(confine, "compose_proof_session", spia)
    esito = _chiusura_d1()
    assert isinstance(esito, ProofSessionClosure)
    assert len(chiamate) == 1


def test_k_nessuna_doppia_validazione():
    from pathlib import Path

    sorgente = Path("src/kirchhoff/pipeline/proof_run.py").read_text(
        encoding="utf-8")
    assert "validate_publication" not in sorgente


# --- L: nessuna ricomputazione semantica -----------------------------------------------------------------


def test_l_nessuna_ricomputazione():
    from pathlib import Path

    sorgente = Path("src/kirchhoff/pipeline/proof_run.py").read_text(
        encoding="utf-8")
    for chiamata in ("pianifica(", "execute_plan(", "transform(",
                      "truthfulness_gate(", "certify_execution(",
                      "solve_dc(", "solve_dc_tableau(", "verify(",
                      "render(", "deposita(",
                      "validate_persisted_publication(",
                      "validate_publication("):
        assert chiamata not in sorgente, chiamata
    # I tre proprietari compaiono in import senza parentesi + unica chiamata.
    assert sorgente.count("orchestrate_didactic_run(") == 1
    assert sorgente.count("componi_registro(") == 1
    assert sorgente.count("compose_proof_session(") == 1
    # sess_ resta coniato solo dal compositore; niente renderer qui dentro.
    assert 'conia("sess"' not in sorgente
    assert "from kirchhoff.render" not in sorgente
    assert "import render" not in sorgente


def test_l_validatore_durevole_mai_usato_live(monkeypatch):
    from kirchhoff.pipeline import proof_session as pubblicazione

    def _vietato(*args, **kwargs):
        raise AssertionError("il durevole non gira a composizione")

    monkeypatch.setattr(
        pubblicazione, "validate_persisted_publication", _vietato)
    assert isinstance(_chiusura_d1(), ProofSessionClosure)


# --- M: Failure di stadio -----------------------------------------------------------------------------------


def test_m_registro_corrotto_fallisce_nominato(monkeypatch):
    import kirchhoff.pipeline.proof_run as confine

    def _rotto(*args, **kwargs):
        raise ValueError("legame impossibile")

    monkeypatch.setattr(confine, "componi_registro", _rotto)
    esito = _chiusura_d1()
    assert type(esito) is Failure
    assert esito.dove == "registry"
    assert "legame impossibile" in esito.messaggio


def test_m_orchestrazione_interna_fallisce_nominata(monkeypatch):
    import kirchhoff.pipeline.proof_run as confine

    def _rotta(*args, **kwargs):
        raise RuntimeError("stato impossibile")

    monkeypatch.setattr(confine, "orchestrate_didactic_run", _rotta)
    esito = _chiusura_d1()
    assert type(esito) is Failure
    assert esito.dove == "orchestrate"


def test_m_input_corrotto_fallisce_orchestrazione():
    esito = run_proof_session(
        "non-un-ir", "non-una-request", clock=OrologioFermo(),
        entropy=_serie(20), document_profile="student-pdf.v0.1",
        source_sha=SHA_FIXTURE, detail="corrotto H2.75")
    assert type(esito) is Failure
    assert esito.dove == "orchestrate"


def test_m_request_incoerente_fallisce_orchestrazione():
    from kirchhoff.domain.ir import Request

    ir, _ = _ir_richiesta(D1)
    esito = run_proof_session(
        ir, Request("q9", "current", "R1"), clock=OrologioFermo(),
        entropy=_serie(20), document_profile="student-pdf.v0.1",
        source_sha=SHA_FIXTURE, detail="request incoerente H2.75")
    assert type(esito) is Failure
    assert esito.dove == "orchestrate"


def test_m_guasto_imprevisto_non_attraversa_il_confine(monkeypatch):
    import kirchhoff.pipeline.proof_run as confine

    def _boom(*args, **kwargs):
        raise RuntimeError("imprevisto")

    monkeypatch.setattr(confine, "compose_proof_session", _boom)
    esito = _chiusura_d1()
    assert type(esito) is Failure
    assert esito.dove == "boundary"
    assert not isinstance(esito, Refusal)


# --- N: metadati ---------------------------------------------------------------------------------------------


def test_n_metadati_malformati_falliscono():
    assert type(_chiusura_d1(source_sha="zzz")) is Failure
    assert type(_chiusura_d1(detail="   ")) is Failure
    assert type(_chiusura_d1(document_profile="banana")) is Failure


# --- O/P: chiusura e supply -----------------------------------------------------------------------------------


def test_o_chiusura_superficiale_ma_legata():
    chiusura = _chiusura_d1()
    assert isinstance(chiusura, ProofSessionClosure)
    with pytest.raises(TypeError):
        ProofSessionClosure(session="non-una-sessione", registry=chiusura.registry)
    with pytest.raises(TypeError):
        ProofSessionClosure(session=chiusura.session, registry="non-un-registro")
    altra_ir, altra_richiesta = _ir_richiesta(D1)
    altra = run_proof_session(
        altra_ir, altra_richiesta, clock=OrologioFermo(),
        entropy=_serie(20, primo=50),
        document_profile="student-pdf.v0.1", source_sha=SHA_FIXTURE,
        detail="altra H2.75")
    assert isinstance(altra, ProofSessionClosure)
    with pytest.raises(ValueError, match="legame"):
        ProofSessionClosure(session=chiusura.session, registry=altra.registry)


def test_p_supply_stati_limitata_e_valida(monkeypatch):
    import kirchhoff.pipeline.proof_run as confine

    viste = {}
    originale = confine.orchestrate_didactic_run

    def spia(ir: IR, richiesta, *, state_ids):
        viste["state_ids"] = state_ids
        return originale(ir, richiesta, state_ids=state_ids)

    monkeypatch.setattr(confine, "orchestrate_didactic_run", spia)
    ir, richiesta = _ir_richiesta(D1)
    esito = run_proof_session(
        ir, richiesta, clock=OrologioFermo(), entropy=_serie(20),
        document_profile="student-pdf.v0.1", source_sha=SHA_FIXTURE,
        detail="supply H2.75")
    assert isinstance(esito, ProofSessionClosure)
    attesa = len(ir.components) + 1
    assert len(viste["state_ids"]) == attesa
    assert len(set(viste["state_ids"])) == attesa
    for sid in viste["state_ids"]:
        verifica(sid, "ir")
