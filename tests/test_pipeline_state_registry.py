"""Registro autorevole CircuitIR <-> StateRef (application boundary).

Un proof_node nomina un'esecuzione, non uno stato: prima di questo modulo
non esisteva alcun legame validato fra un identificatore e il CircuitIR che
denota, e il compositore provvisorio riusava il proof_node per before e after.
Questi test impongono il legame esplicito su una trasformazione D1 reale.
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
    # Politica documentata: i ref nominano occorrenze, non contenuti. Anche un
    # rebind identico fallisce esplicitamente invece di passare in silenzio:
    # come LayoutStore, un deposito doppio accusa un conio doppio.
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
    ir, _ = _d1()
    ref_a, ref_b = _refs(2)
    base = CircuitStateRegistry((StateBinding(ref_a, ir),))
    esteso = base.con_binding(StateBinding(ref_b, ir))
    assert esteso != base
    assert len(base) == 1
    assert len(esteso) == 2
    assert esteso.resolve(ref_a) == ir
    assert esteso.resolve(ref_b) == ir
    assert esteso.refs() == (ref_a, ref_b)


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
    ir, _ = _d1()
    refs_a = _refs(2)
    refs_b = _refs(2)
    assert refs_a == refs_b
    ra = CircuitStateRegistry(tuple(StateBinding(r, ir) for r in refs_a))
    rb = CircuitStateRegistry(tuple(StateBinding(r, ir) for r in refs_b))
    assert ra == rb
    assert hash(ra) == hash(rb)
    invertito = CircuitStateRegistry(tuple(StateBinding(r, ir) for r in reversed(refs_a)))
    assert invertito != ra


def test_proof_node_non_lega_automaticamente():
    # Il proof_node e' un ir_ ben formato ma nomina l'esecuzione, non lo stato:
    # senza legame esplicito non risolve nulla.
    execution = _d1_execution()
    dal_proof_node = StateRef(execution.proof_node)
    assert isinstance(dal_proof_node.identifier, str)
    ref_before, ref_after = _refs(2)
    registro = CircuitStateRegistry((
        StateBinding(ref_before, execution.before),
        StateBinding(ref_after, execution.after),
    ))
    with pytest.raises(KeyError, match="non e' legato"):
        registro.resolve(dal_proof_node)
