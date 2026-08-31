"""Query di applicabilità serie/parallelo: unica fonte delle guardie topologiche."""
from __future__ import annotations

from fractions import Fraction

from kirchhoff.domain.ir import IR, Component
from kirchhoff.domain.transform import SUPPORTED, implemented
from kirchhoff.domain.transform.applicability import (
    ExecutableTransform,
    enumerate_executable_transforms,
    motivo_non_parallelo,
    motivo_non_serie,
    parallelo_applicabile,
    serie_applicabile,
)
from kirchhoff.pipeline.netlist import leggi

from test_percorso_b import PARALLELO, PARTITORE, PONTE

F = Fraction


def _ir(nodes, comps) -> IR:
    return IR("1.0.0", "dc", "netlist", tuple(nodes), tuple(comps), ())


def test_serie_applicabile_sul_partitore():
    ir = leggi(PARTITORE)
    r1, r2 = ir.component("R1"), ir.component("R2")
    assert motivo_non_serie(ir, r1, r2) is None
    assert serie_applicabile(ir, r1, r2)
    assert not parallelo_applicabile(r1, r2)
    assert "stessi due nodi" in motivo_non_parallelo(r1, r2)


def test_parallelo_applicabile_sulla_coppia_condivisa():
    ir = leggi(PARALLELO)
    r1, r2 = ir.component("R1"), ir.component("R2")
    assert motivo_non_parallelo(r1, r2) is None
    assert parallelo_applicabile(r1, r2)
    assert not serie_applicabile(ir, r1, r2)
    assert "2 nodi" in motivo_non_serie(ir, r1, r2)
    massa = _ir(("0", "a", "b"), (
        Component.of("V1", "voltage_source_dc", ("a", "b"), F(1), "V1"),
        Component.of("R1", "resistor", ("a", "0"), F(2), "R1"),
        Component.of("R2", "resistor", ("0", "b"), F(3), "R2"),
    ))
    assert "riferimento" in motivo_non_serie(
        massa, massa.component("R1"), massa.component("R2"))


def test_serie_rifiuta_disgiunti_e_stella():
    disgiunti = _ir(("0", "a", "b", "c"), (
        Component.of("R1", "resistor", ("a", "b"), F(2), "R1"),
        Component.of("R2", "resistor", ("c", "0"), F(3), "R2"),
    ))
    assert "condividono" in motivo_non_serie(
        disgiunti, disgiunti.component("R1"), disgiunti.component("R2"))
    stella = _ir(("0", "a", "b", "c"), (
        Component.of("V1", "voltage_source_dc", ("a", "0"), F(1), "V1"),
        Component.of("R1", "resistor", ("a", "b"), F(2), "R1"),
        Component.of("R2", "resistor", ("b", "c"), F(3), "R2"),
        Component.of("R3", "resistor", ("b", "0"), F(4), "R3"),
    ))
    assert "grado" in motivo_non_serie(stella, stella.component("R1"), stella.component("R2"))


def test_enumerate_ordine_canonico_e_solo_resistori():
    part = leggi(PARTITORE)
    elenco = enumerate_executable_transforms(part)
    assert elenco == tuple(sorted(elenco))
    assert all(t.operation == "serie" for t in elenco)
    assert ExecutableTransform("serie", "R2", "R1").operands == ("R2", "R1")
    invertito = _ir(("0", "a", "b"), (
        Component.of("R2", "resistor", ("a", "0"), F(220), "R2"),
        Component.of("R1", "resistor", ("b", "a"), F(100), "R1"),
        Component.of("V1", "voltage_source_dc", ("b", "0"), F(12), "V1"),
    ))
    assert enumerate_executable_transforms(invertito) == elenco
    par = leggi(PARALLELO)
    elenco_p = enumerate_executable_transforms(par)
    assert all(t.operation == "parallelo" for t in elenco_p)
    assert enumerate_executable_transforms(leggi(PONTE)) == ()


def test_enumerate_ignora_non_resistori_e_resta_vuoto_senza_coppie():
    solo_v = _ir(("0", "a"), (
        Component.of("V1", "voltage_source_dc", ("a", "0"), F(5), "V1"),
    ))
    assert enumerate_executable_transforms(solo_v) == ()
    un_r = _ir(("0", "a"), (
        Component.of("V1", "voltage_source_dc", ("a", "0"), F(5), "V1"),
        Component.of("R1", "resistor", ("a", "0"), F(2), "R1"),
    ))
    assert enumerate_executable_transforms(un_r) == ()


def test_nome_supportato_senza_corpo_non_compare_fra_le_eseguibili():
    assert "partitore_di_tensione" in SUPPORTED
    assert "partitore_di_tensione" not in implemented()
    trovate = enumerate_executable_transforms(leggi(PARTITORE))
    assert all(t.operation != "partitore_di_tensione" for t in trovate)
    assert "serie" in implemented() and "parallelo" in implemented()
