"""Registro canonico CircuitIR <-> StateRef (application boundary).

Un proof_node nomina lo stato circuitale consumato, cioe' un nodo del
ProofGraph (AD-29), non un'esecuzione: ``CertifiedDidacticRun.state_ids``
assegna un identificatore per stato operativo distinto, e il Claim P1-K lo
ancora come ``state_id``. Prima di questo modulo non esisteva alcun legame
validato fra un identificatore e il CircuitIR che denota: questi test
impongono il legame esplicito e canonico (un valore, un ref) su una
trasformazione D1 reale.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction

import pytest

import kirchhoff.domain.didactic.orchestrate as orchestrate
from kirchhoff.domain.didactic.execute import TransformExecution, execute_plan
from kirchhoff.domain.didactic.orchestrate import orchestrate_didactic_run
from kirchhoff.domain.didactic.planner import pianifica
from kirchhoff.domain.identity import conia
from kirchhoff.domain.ir import Component, IR, Request
from kirchhoff.pipeline.netlist import leggi
from kirchhoff.pipeline.state_registry import (
    CircuitStateRegistry,
    StateBinding,
    StateRef,
)


D1 = """\
V1 b 0 12 volt
R1 b a 100 ohm
R2 a 0 220 ohm
"""


def _refs(number: int, *, start: int = 1000) -> tuple[StateRef, ...]:
    return tuple(
        StateRef(conia("ir", start + index, bytes(range(index, index + 10))))
        for index in range(number)
    )


def _d1() -> tuple[IR, Request]:
    request = Request("q_d1", "current", "R1")  # type: ignore[arg-type]
    return replace(leggi(D1), requests=(request,)), request


def _d1_execution() -> TransformExecution:
    ir, request = _d1()
    plan = pianifica(ir, request)
    execution = execute_plan(
        ir, request, plan, proof_node=_refs(1, start=7000)[0].identifier)
    assert isinstance(execution, TransformExecution)
    return execution


def test_due_stati_distinti_due_ref():
    prima, richiesta = _d1()
    dopo = replace(leggi("V1 b 0 12 volt\nR1R2eq b 0 320 ohm\n"),
                   requests=(Request("q_d1", "current", "R1R2eq"),))
    assert prima != dopo
    ref_prima, ref_dopo = _refs(2)
    assert ref_prima != ref_dopo
    registro = CircuitStateRegistry((
        StateBinding(ref_prima, prima),
        StateBinding(ref_dopo, dopo),
    ))
    assert registro.resolve(ref_prima) == prima
    assert registro.resolve(ref_dopo) == dopo
    assert richiesta.id == "q_d1"


def test_stesso_ref_stesso_stato_politica_esplicita():
    # Politica canonica: un valore ha un solo ref, un ref un solo valore.
    # Anche un rebind identico fallisce esplicitamente invece di passare in
    # silenzio: come LayoutStore, un deposito doppio accusa un conio doppio.
    ir, _ = _d1()
    ref = _refs(1)[0]
    with pytest.raises(ValueError, match="gia' legato"):
        CircuitStateRegistry((
            StateBinding(ref, ir),
            StateBinding(ref, ir),
        ))
    registro = CircuitStateRegistry((StateBinding(ref, ir),))
    with pytest.raises(ValueError, match="gia' legato"):
        registro.con_binding(StateBinding(ref, ir))


def test_stesso_ref_stato_diverso_fallisce():
    ir, request = _d1()
    altro = replace(
        leggi(D1.replace("R2 a 0 220 ohm", "R2 a 0 221 ohm")),
        requests=(request,))
    assert altro != ir
    ref = _refs(1)[0]
    with pytest.raises(ValueError, match="gia' legato"):
        CircuitStateRegistry((
            StateBinding(ref, ir),
            StateBinding(ref, altro),
        ))


def test_ref_sconosciuto_fallisce():
    ir, _ = _d1()
    ref, ignoto = _refs(2)
    registro = CircuitStateRegistry((StateBinding(ref, ir),))
    with pytest.raises(KeyError, match="non e' legato"):
        registro.resolve(ignoto)
    assert ignoto not in registro
    assert ref in registro


def test_ref_duplicato_nel_costruttore_fallisce():
    ir, _ = _d1()
    ref = _refs(1)[0]
    with pytest.raises(ValueError, match="gia' legato"):
        CircuitStateRegistry((
            StateBinding(ref, ir),
            StateBinding(StateRef(conia(
                "ir", 2000, bytes(range(10)))), ir),
            StateBinding(ref, ir),
        ))


def test_ref_malformato_fallisce():
    with pytest.raises(ValueError, match="cifre dopo il prefisso"):
        StateRef("ir_corto")
    with pytest.raises(ValueError, match="prefisso"):
        StateRef(conia("lay", 3000, bytes(range(10))))
    with pytest.raises(TypeError, match="invece di str"):
        StateRef(123)  # type: ignore[arg-type]
    ir, _ = _d1()
    registro = CircuitStateRegistry((StateBinding(_refs(1)[0], ir),))
    with pytest.raises(TypeError, match="invece di StateRef"):
        registro.resolve("ir_qualcosa")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="invece di StateRef"):
        registro.resolve(None)  # type: ignore[arg-type]


def test_binding_tipizzato():
    ir, _ = _d1()
    ref = _refs(1)[0]
    with pytest.raises(TypeError, match="invece di StateRef"):
        StateBinding("ir_x", ir)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="invece di IR"):
        StateBinding(ref, "circuito")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="invece di StateBinding"):
        CircuitStateRegistry((ref,))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="invece di StateBinding"):
        CircuitStateRegistry((StateBinding(ref, ir),)).con_binding(ref)  # type: ignore[arg-type]


def test_transform_before_after_ref_distinti():
    execution = _d1_execution()
    assert execution.before != execution.after
    ref_before, ref_after = _refs(2)
    assert ref_before != ref_after
    registro = CircuitStateRegistry((
        StateBinding(ref_before, execution.before),
        StateBinding(ref_after, execution.after),
    ))
    assert registro.resolve(ref_before) == execution.before
    assert registro.resolve(ref_after) == execution.after


def test_d1_binding_reale_esatto():
    # after letterale (requests vuote) e stato operativo (successore rilegato)
    # sono valori canonici distinti: tre valori, tre ref. Lo stato omesso dal
    # passo resterebbe comunque identificabile dal suo ref in evidenza.
    execution = _d1_execution()
    assert execution.successor_request is not None
    operativo = orchestrate._bind_successor_request(
        execution.after, execution.successor_request)
    assert execution.after != operativo
    assert operativo.requests == (execution.successor_request,)
    ref_before, ref_letterale, ref_operativo = _refs(3)
    registro = CircuitStateRegistry((
        StateBinding(ref_before, execution.before),
        StateBinding(ref_letterale, execution.after),
        StateBinding(ref_operativo, operativo),
    ))
    assert registro.resolve(ref_before) == execution.before
    assert registro.resolve(ref_letterale) == execution.after
    assert registro.resolve(ref_operativo) == operativo

    ir, request = _d1()
    run = orchestrate_didactic_run(ir, request, state_ids=tuple(
        conia("ir", 5000 + i, bytes(range(i, i + 10))) for i in range(2)))
    assert registro.resolve(ref_operativo) == run.final_ir
    assert len(registro) == 3
    assert registro.refs() == (ref_before, ref_letterale, ref_operativo)


def test_con_binding_estende_senza_modificare():
    prima, _ = _d1()
    dopo = replace(leggi("V1 b 0 12 volt\nR1R2eq b 0 320 ohm\n"), requests=())
    assert prima != dopo
    ref_a, ref_b = _refs(2)
    base = CircuitStateRegistry((StateBinding(ref_a, prima),))
    esteso = base.con_binding(StateBinding(ref_b, dopo))
    assert esteso != base
    assert len(base) == 1
    assert len(esteso) == 2
    assert esteso.resolve(ref_a) == prima
    assert esteso.resolve(ref_b) == dopo
    assert esteso.refs() == (ref_a, ref_b)


def test_stesso_valore_con_ref_diverso_fallisce():
    # Registro canonico, non occorrenze: lo stesso valore IR non riceve due
    # ref distinti, come ProofGraph non ha due nodi sullo stesso stato.
    ir, _ = _d1()
    ref_a, ref_b = _refs(2)
    with pytest.raises(ValueError, match="un solo ref"):
        CircuitStateRegistry((
            StateBinding(ref_a, ir),
            StateBinding(ref_b, ir),
        ))


def test_con_binding_stesso_valore_fallisce():
    ir, _ = _d1()
    ref_a, ref_b = _refs(2)
    base = CircuitStateRegistry((StateBinding(ref_a, ir),))
    with pytest.raises(ValueError, match="un solo ref"):
        base.con_binding(StateBinding(ref_b, ir))
    assert len(base) == 1
    assert base.resolve(ref_a) == ir


def test_input_mutabile_non_tocca_registro():
    ir, _ = _d1()
    ref = _refs(1)[0]
    lista = [StateBinding(ref, ir)]
    registro = CircuitStateRegistry(lista)  # type: ignore[arg-type]
    lista.clear()
    lista.append(StateBinding(_refs(1, start=9000)[0], ir))
    assert len(registro) == 1
    assert registro.resolve(ref) == ir
    assert isinstance(registro.refs(), tuple)


def test_uguaglianza_deterministica():
    prima, _ = _d1()
    dopo = replace(leggi("V1 b 0 12 volt\nR1R2eq b 0 320 ohm\n"), requests=())
    assert prima != dopo
    refs_a = _refs(2)
    refs_b = _refs(2)
    assert refs_a == refs_b
    ra = CircuitStateRegistry((
        StateBinding(refs_a[0], prima), StateBinding(refs_a[1], dopo)))
    rb = CircuitStateRegistry((
        StateBinding(refs_b[0], prima), StateBinding(refs_b[1], dopo)))
    assert ra == rb
    assert hash(ra) == hash(rb)
    invertito = CircuitStateRegistry((
        StateBinding(refs_a[1], dopo), StateBinding(refs_a[0], prima)))
    assert invertito != ra


def test_ref_for_risolve_inverso_e_fallisce_su_sconosciuto():
    prima, _ = _d1()
    dopo = replace(leggi("V1 b 0 12 volt\nR1R2eq b 0 320 ohm\n"), requests=())
    ref_prima, ref_dopo = _refs(2)
    registro = CircuitStateRegistry((
        StateBinding(ref_prima, prima),
        StateBinding(ref_dopo, dopo),
    ))
    assert registro.ref_for(prima) == ref_prima
    assert registro.ref_for(dopo) == ref_dopo
    altro = replace(
        leggi(D1.replace("R2 a 0 220 ohm", "R2 a 0 221 ohm")),
        requests=(Request("q_d1", "current", "R1"),))
    with pytest.raises(KeyError, match="nessun ref"):
        registro.ref_for(altro)
    with pytest.raises(TypeError, match="invece di IR"):
        registro.ref_for("non-un-ir")  # type: ignore[arg-type]


def test_proof_node_lega_lo_stato_quando_la_run_e_proiettata():
    # Correzione G1: il proof_node nomina lo stato circuitale consumato
    # (nodo del ProofGraph), non un'esecuzione. Legato esplicitamente allo
    # stato operativo della run, risolve quello stato.
    ir, request = _d1()
    run = orchestrate_didactic_run(ir, request, state_ids=tuple(
        conia("ir", 5000 + i, bytes(range(i, i + 10))) for i in range(2)))
    primo = run.transform_executions[0]
    assert primo.proof_node == run.state_ids[0]
    registro = CircuitStateRegistry((
        StateBinding(StateRef(run.state_ids[0]), primo.before),
        StateBinding(StateRef(run.state_ids[1]), run.final_ir),
    ))
    assert registro.resolve(StateRef(primo.proof_node)) == primo.before
    assert registro.resolve(StateRef(primo.proof_node)) == run.initial_ir
    assert registro.ref_for(run.final_ir) == StateRef(run.state_ids[-1])
