"""Forma canonica: ordinare ciò che è arbitrario, lasciare intatto ciò che non lo è.

L'ordine in cui i componenti compaiono in un elenco non dice nulla del circuito, e
per un resistore nemmeno l'ordine dei suoi due terminali. L'ordine dei terminali di
un **generatore** invece è la polarità, e riordinarlo cambierebbe il circuito.
"""

from fractions import Fraction

from kirchhoff.domain.ir import IR, Component, Magnitude, Request, canonicalize

Q = Fraction


def comp(cid: str, tipo: str, terminali: tuple[str, str], valore: int) -> Component:
    return Component.of(cid, tipo, terminali, Q(valore), cid)


def circuito(componenti, nodi) -> IR:
    return IR("1.0.0", "dc_resistive", "netlist", nodi, componenti,
              (Request("q1", "voltage", "R1"),))


def test_ordine_diverso_stessa_forma_canonica():
    e = comp("E1", "voltage_source_dc", ("A", "0"), 12)
    r1 = comp("R1", "resistor", ("A", "B"), 10)
    r2 = comp("R2", "resistor", ("B", "0"), 20)

    uno = circuito((e, r1, r2), ("0", "A", "B"))
    altro = circuito((r2, e, r1), ("B", "A", "0"))

    assert canonicalize(uno) == canonicalize(altro)


def test_il_confronto_dopo_la_canonicalizzazione_e_identico():
    e = comp("E1", "voltage_source_dc", ("A", "0"), 12)
    r1 = comp("R1", "resistor", ("A", "B"), 10)
    uno = circuito((e, r1), ("0", "A", "B"))
    altro = circuito((r1, e), ("A", "B", "0"))

    a, b = canonicalize(uno), canonicalize(altro)
    assert a.components == b.components
    assert a.nodes == b.nodes
    assert a == b


def test_bipolo_simmetrico_rovesciato_ha_la_stessa_forma():
    """Un resistore fra A e B è lo stesso resistore fra B e A."""
    dritto = circuito((comp("E1", "voltage_source_dc", ("A", "0"), 12),
                       comp("R1", "resistor", ("A", "B"), 10)), ("0", "A", "B"))
    rovescio = circuito((comp("E1", "voltage_source_dc", ("A", "0"), 12),
                         comp("R1", "resistor", ("B", "A"), 10)), ("0", "A", "B"))
    assert canonicalize(dritto) == canonicalize(rovescio)


def test_una_sorgente_rovesciata_e_un_altro_circuito():
    """L'ordine dei terminali di un generatore è la sua polarità: non si tocca."""
    dritto = circuito((comp("E1", "voltage_source_dc", ("A", "0"), 12),
                       comp("R1", "resistor", ("A", "0"), 10)), ("0", "A"))
    rovescio = circuito((comp("E1", "voltage_source_dc", ("0", "A"), 12),
                         comp("R1", "resistor", ("A", "0"), 10)), ("0", "A"))
    assert canonicalize(dritto) != canonicalize(rovescio)


def test_la_canonicalizzazione_e_idempotente():
    uno = circuito((comp("R2", "resistor", ("B", "0"), 20),
                    comp("E1", "voltage_source_dc", ("A", "0"), 12),
                    comp("R1", "resistor", ("B", "A"), 10)), ("B", "0", "A"))
    una_volta = canonicalize(uno)
    assert canonicalize(una_volta) == una_volta


def test_le_richieste_sono_ordinate():
    c = (comp("E1", "voltage_source_dc", ("A", "0"), 12),
         comp("R1", "resistor", ("A", "0"), 10))
    uno = IR("1.0.0", "dc_resistive", "netlist", ("0", "A"), c,
             (Request("q2", "current", "R1"), Request("q1", "voltage", "R1")))
    assert [r.id for r in canonicalize(uno).requests] == ["q1", "q2"]


def test_la_canonicalizzazione_non_altera_l_originale():
    """Pura: gli stadi restituiscono un nuovo IR, non mutano quello ricevuto."""
    uno = circuito((comp("R2", "resistor", ("B", "0"), 20),
                    comp("E1", "voltage_source_dc", ("A", "0"), 12),
                    comp("R1", "resistor", ("B", "A"), 10)), ("B", "0", "A"))
    prima = uno.components
    canonicalize(uno)
    assert uno.components is prima
    assert uno.nodes == ("B", "0", "A")


def test_circuiti_diversi_restano_diversi():
    uno = circuito((comp("E1", "voltage_source_dc", ("A", "0"), 12),
                    comp("R1", "resistor", ("A", "0"), 10)), ("0", "A"))
    altro = circuito((comp("E1", "voltage_source_dc", ("A", "0"), 12),
                      comp("R1", "resistor", ("A", "0"), 11)), ("0", "A"))
    assert canonicalize(uno) != canonicalize(altro)
