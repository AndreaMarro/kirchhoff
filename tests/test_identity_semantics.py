"""Semantica di identita' della trace didattica (G1).

Contratto esplicito, letto dall'architettura e non dai nomi delle variabili:

- ``TransformExecution.proof_node`` e ``NodalExecution.proof_node`` nominano lo
  stato circuitale consumato/analizzato, cioe' un nodo del ``ProofGraph``
  (AD-29: nodi = stati circuitali; ``ProofNode.identifier`` e' l'``ir_`` dello
  stato). Non nominano un'esecuzione.
- ``CertifiedDidacticRun.state_ids[i]`` nomina l'i-esimo stato operativo
  consumato: ``transform_executions[i].before`` per ogni passo, ``final_ir``
  per l'ultimo. La continuita' (``before == stato corrente``) e il Claim P1-K
  (``claim.state_id == proof_node`` finale) lo impongono.
- L'``after`` letterale di un passo e' il prodotto intermedio certificato
  (evidenza), non uno stato della timeline: con un retarget differisce dallo
  stato operativo per le Request rilegate, e non gli si assegna un arco fittizio.
- L'identita' di stato e' il valore IR intero, Request incluse: nessun
  ridisegno dell'IR, nessun secondo criterio.
- Il registro e' canonico: un valore, un ref (come ``ProofGraph`` rifiuta due
  nodi sullo stesso identificatore). La proiezione applicativa
  (``componi_registro``) deriva solo da dati pubblici immutabili della run:
  mai da ``orchestrate._bind_successor_request`` o altri dettagli privati.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from inspect import signature
from pathlib import Path

import pytest

from kirchhoff.domain.didactic.orchestrate import (
    CertifiedDidacticRun,
    orchestrate_didactic_run,
)
from kirchhoff.domain.identity import conia
from kirchhoff.domain.ir import IR, Request
from kirchhoff.domain.proof.graph import ProofEdge, ProofGraph, ProofNode
from kirchhoff.pipeline import state_registry as registro_modulo
from kirchhoff.pipeline.netlist import leggi
from kirchhoff.pipeline.state_registry import (
    CircuitStateRegistry,
    StateBinding,
    StateRef,
    componi_registro,
    stati_operativi,
)


D1 = """\
V1 b 0 12 volt
R1 b a 100 ohm
R2 a 0 220 ohm
"""

MULTI_SERIE = """\
V1 d 0 12 volt
R1 d a 100 ohm
R2 a b 220 ohm
R3 b c 330 ohm
R4 c 0 470 ohm
I1 0 c 1 ampere
"""

SERIE = """\
V1 c 0 12 volt
R1 c a 100 ohm
R2 a b 220 ohm
R3 b 0 330 ohm
I1 0 b 1 ampere
"""

TERMINALE = """\
V1 b 0 12 volt
R1R2eq b 0 320 ohm
"""


def _ids(number: int, *, start: int = 100) -> tuple[str, ...]:
    return tuple(
        conia("ir", start + index, bytes(range(index, index + 10)))
        for index in range(number)
    )


def _evidence(number: int, *, start: int = 5000) -> tuple[StateRef, ...]:
    return tuple(
        StateRef(conia("ir", start + index, bytes(range(50 + index, 60 + index))))
        for index in range(number)
    )


def _input(netlist: str, target: str, quantity: str, *, request_id: str = "q1"):
    request = Request(request_id, quantity, target)  # type: ignore[arg-type]
    return replace(leggi(netlist), requests=(request,)), request


def _d1_run() -> CertifiedDidacticRun:
    request = Request("q_d1", "current", "R1")  # type: ignore[arg-type]
    ir = replace(leggi(D1), requests=(request,))
    run = orchestrate_didactic_run(ir, request, state_ids=_ids(2))
    assert isinstance(run, CertifiedDidacticRun)
    return run


def _multi_run() -> CertifiedDidacticRun:
    ir, request = _input(MULTI_SERIE, "R1", "current")
    run = orchestrate_didactic_run(ir, request, state_ids=_ids(3))
    assert isinstance(run, CertifiedDidacticRun)
    assert len(run.transform_executions) == 2
    return run


def _identity_run() -> CertifiedDidacticRun:
    ir, request = _input(SERIE, "V1", "voltage")
    run = orchestrate_didactic_run(ir, request, state_ids=_ids(2))
    assert isinstance(run, CertifiedDidacticRun)
    assert len(run.transform_executions) == 1
    assert run.transform_executions[0].observation_effect.kind == "identity"
    return run


def _zero_run() -> CertifiedDidacticRun:
    request = Request("q_t", "voltage", "R1R2eq")  # type: ignore[arg-type]
    ir = replace(leggi(TERMINALE), requests=(request,))
    run = orchestrate_didactic_run(ir, request, state_ids=_ids(1))
    assert isinstance(run, CertifiedDidacticRun)
    assert run.transform_executions == ()
    return run


# --- 1/2/3. la mappa state_ids -> stati operativi ---------------------------


def test_state_ids_nominano_gli_stati_consumati_d1():
    run = _d1_run()
    primo = run.transform_executions[0]
    assert run.state_ids[0] == primo.proof_node
    assert primo.before == run.initial_ir
    registro = componi_registro(run, _evidence(1))
    assert registro.resolve(StateRef(run.state_ids[0])) == primo.before
    assert registro.resolve(StateRef(run.state_ids[0])) == run.initial_ir


def test_stato_finale_risolve_final_ir_e_ancora_il_claim():
    run = _d1_run()
    registro = componi_registro(run, _evidence(1))
    assert registro.resolve(StateRef(run.state_ids[-1])) == run.final_ir
    assert run.final_execution.execution.proof_node == run.state_ids[-1]
    assert run.final_execution.claim.state_id == run.state_ids[-1]
    assert run.final_execution.claim.status == "VERIFIED"
    assert run.final_execution.execution.resolved.value.amount == Fraction(3, 80)
    assert run.final_execution.execution.resolved.value.unit == "ampere"


def test_timeline_multi_passo_mappa_ogni_before_e_il_finale():
    run = _multi_run()
    registro = componi_registro(run, _evidence(2))
    assert len(run.state_ids) == 3
    for i, esecuzione in enumerate(run.transform_executions):
        assert run.state_ids[i] == esecuzione.proof_node
        assert registro.resolve(StateRef(run.state_ids[i])) == esecuzione.before
    assert registro.resolve(StateRef(run.state_ids[-1])) == run.final_ir
    # Lo stato operativo dopo il passo i e' il before del passo i+1.
    assert run.transform_executions[1].before != run.transform_executions[0].after
    assert [c.id for c in run.transform_executions[1].before.components] == [
        c.id for c in run.transform_executions[0].after.components]
    assert run.transform_executions[1].before.requests == (
        run.transform_executions[0].successor_request,)
    assert run.final_execution.claim.status == "VERIFIED"


# --- 5/6/7. letterale contro operativo, retarget esplicito ------------------


def test_dopo_letterale_conservato_come_evidenza_distinta_dall_operativo():
    run = _d1_run()
    passo = run.transform_executions[0]
    assert passo.successor_request is not None
    assert passo.observation_effect.kind == "retarget"
    assert passo.successor_request.target == "R1R2eq"
    assert passo.after.requests == ()
    registro = componi_registro(run, _evidence(1))
    letterale = registro.ref_for(passo.after)
    operativo_finale = StateRef(run.state_ids[-1])
    assert letterale != operativo_finale
    assert registro.resolve(letterale) == passo.after
    assert registro.resolve(operativo_finale) == run.final_ir
    assert registro.resolve(operativo_finale).requests == (passo.successor_request,)


def test_identity_letterale_e_operativo_coincidono_un_solo_ref():
    run = _identity_run()
    passo = run.transform_executions[0]
    assert passo.successor_request is run.original_request
    registro = componi_registro(run, _evidence(1))
    # Nessun ref di evidenza consumato: il letterale e' gia' lo stato operativo.
    assert registro.ref_for(passo.after) == StateRef(run.state_ids[-1])
    assert registro.resolve(StateRef(run.state_ids[-1])) == run.final_ir
    assert len(registro) == 2


def test_run_senza_trasformazioni_un_solo_stato_operativo():
    run = _zero_run()
    assert stati_operativi(run) == (run.final_ir,)
    registro = componi_registro(run)
    assert len(registro) == 1
    assert registro.resolve(StateRef(run.state_ids[0])) == run.final_ir


# --- 8/16. ruolo semantico del proof_node e compatibilita' ProofGraph -------


def test_proof_node_e_identificatore_di_stato_in_tutte_le_sedi():
    run = _multi_run()
    for esecuzione in run.transform_executions:
        nodo = ProofNode(identifier=esecuzione.proof_node, layout=_lay())
        assert nodo.identifier == esecuzione.proof_node
    finale = run.final_execution.execution
    assert finale.derivation.proof_node == finale.proof_node
    assert finale.proof_node == run.state_ids[-1]


def _lay(start: int = 9000) -> str:
    return conia("lay", start, bytes(range(70, 80)))


def test_stati_operativi_formano_un_proofgraph_valido():
    run = _d1_run()
    registro = componi_registro(run, _evidence(1))
    stati = stati_operativi(run)
    assert len(stati) == 2
    assert all(
        registro.ref_for(stato) == StateRef(sid)
        for sid, stato in zip(run.state_ids, stati))
    layout_a = conia("lay", 9100, bytes(range(70, 80)))
    layout_b = conia("lay", 9101, bytes(range(71, 81)))
    toppa = conia("patch", 9200, bytes(range(72, 82)))
    grafo = ProofGraph(
        nodes=(
            ProofNode(identifier=run.state_ids[0], layout=layout_a),
            ProofNode(identifier=run.state_ids[1], layout=layout_b),
        ),
        edges=(
            ProofEdge(
                source=run.state_ids[0],
                target=run.state_ids[1],
                operation=run.transform_executions[0].plan.actions[0].kind,
                patch=toppa,
            ),
        ),
    )
    assert grafo.layout_di(run.state_ids[0]) == layout_a
    assert grafo.nodo_di(layout_b) == run.state_ids[1]


# --- proiezione da dati pubblici soltanto -----------------------------------


def test_stati_operativi_derivano_dalla_run_pubblica():
    run = _multi_run()
    assert stati_operativi(run) == (
        run.transform_executions[0].before,
        run.transform_executions[1].before,
        run.final_ir,
    )
    assert stati_operativi(run)[0] == run.initial_ir


def test_stati_operativi_rifiutano_oggetti_estranei():
    with pytest.raises(TypeError, match="CertifiedDidacticRun"):
        stati_operativi(object())  # type: ignore[arg-type]


def test_compositore_non_dipende_da_helper_privati_del_dominio():
    sorgente = Path(registro_modulo.__file__).read_text(encoding="utf-8")
    assert "_bind_successor_request" not in sorgente
    assert "conia(" not in sorgente
    assert list(signature(componi_registro).parameters) == ["run", "refs_evidenza"]


def test_evidenza_insufficiente_fallisce_chiuso():
    run = _d1_run()
    with pytest.raises(ValueError, match="evidenza"):
        componi_registro(run)


def test_evidenza_sovrabbondante_ignorata_senza_legami_spuri():
    run = _d1_run()
    registro = componi_registro(run, _evidence(3))
    assert len(registro) == 3
    assert registro.refs() == (
        StateRef(run.state_ids[0]),
        StateRef(run.state_ids[1]),
        registro.ref_for(run.transform_executions[0].after),
    )


def test_ref_evidenza_mal_tipizzato_fallisce():
    run = _d1_run()
    with pytest.raises(TypeError, match="StateRef"):
        componi_registro(run, ("non-un-ref",))  # type: ignore[arg-type]


def test_ref_evidenza_che_ricicla_uno_state_id_fallisce_chiuso():
    # Avversario: la fornitura di evidenza riusa l'identificatore di uno stato
    # operativo. Il registro canonico lo rifiuta invece di rilegarlo.
    run = _d1_run()
    riciclato = StateRef(run.state_ids[0])
    with pytest.raises(ValueError, match="gia' legato"):
        componi_registro(run, (riciclato,))


# --- 13/14. niente stato globale, niente orologi ----------------------------


def test_due_proiezioni_della_stessa_run_sono_indipendenti_e_deterministiche():
    run = _d1_run()
    prima = componi_registro(run, _evidence(1))
    seconda = componi_registro(run, _evidence(1))
    assert prima == seconda
    assert hash(prima) == hash(seconda)
    altra = componi_registro(run, _evidence(1, start=6000))
    assert altra != prima
    assert prima.resolve(StateRef(run.state_ids[0])) == run.initial_ir
    assert altra.resolve(StateRef(run.state_ids[0])) == run.initial_ir


def test_fornitura_mutabile_non_tocca_il_registro_composto():
    run = _d1_run()
    fornitura = list(_evidence(2))
    registro = componi_registro(run, tuple(fornitura))
    fornitura.clear()
    assert len(registro) == 3
    assert registro.resolve(StateRef(run.state_ids[-1])) == run.final_ir
