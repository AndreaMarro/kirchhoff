"""Lo schema dell'IR: nessun numero nudo, nessuna versione ambigua.

«Sempre coppia magnitudine + unità, mai numero nudo» è una convenzione dello spine.
Qui smette di essere una convenzione: senza unità il componente non si costruisce, e
con l'unità sbagliata nemmeno. Dieci ohm e dieci farad non si possono più confondere,
perché non sono più entrambi `Fraction(10)`.
"""

from fractions import Fraction

import pytest

from kirchhoff.domain.ir import (
    EXPECTED_UNIT,
    IR,
    Component,
    Magnitude,
    Provenance,
    Request,
)

Q = Fraction


def resistore(**override) -> Component:
    campi = {"id": "R1", "type": "resistor", "terminals": ("A", "0"),
             "value": Magnitude(Q(10), "ohm"), "symbolic": "R_1"}
    return Component(**{**campi, **override})


def ir(**override) -> IR:
    campi = {
        "ir_version": "1.0.0",
        "domain": "dc_resistive",
        "source_kind": "netlist",
        "nodes": ("0", "A"),
        "components": (
            Component("E1", "voltage_source_dc", ("A", "0"), Magnitude(Q(12), "volt"), "E_1"),
            resistore(),
        ),
        "requests": (Request("q1", "voltage", "R1"),),
    }
    return IR(**{**campi, **override})


# -- magnitudine e unità -------------------------------------------------------


def test_ogni_componente_porta_magnitudine_unita_e_forma_simbolica():
    c = resistore()
    assert c.value.amount == Q(10)
    assert c.value.unit == "ohm"
    assert c.symbolic == "R_1"


def test_valore_nudo_respinto():
    """Un numero senza unità non entra nell'IR: e' la riga che rende vera la convenzione."""
    with pytest.raises(TypeError, match="senza unità"):
        resistore(value=Q(10))


def test_unita_incoerente_col_tipo_respinta():
    with pytest.raises(ValueError, match="farad"):
        resistore(value=Magnitude(Q(10), "farad"))


def test_il_messaggio_dice_l_unita_attesa():
    with pytest.raises(ValueError, match="ohm"):
        resistore(value=Magnitude(Q(10), "farad"))


def test_ogni_tipo_ha_la_propria_unita():
    assert EXPECTED_UNIT["capacitor"] == "farad"
    assert EXPECTED_UNIT["inductor"] == "henry"
    assert EXPECTED_UNIT["current_source_dc"] == "ampere"
    assert EXPECTED_UNIT["voltage_source_ac"] == "volt"


def test_magnitudine_in_virgola_mobile_respinta():
    with pytest.raises(TypeError, match="Fraction"):
        Magnitude(0.1, "ohm")          # type: ignore[arg-type]


def test_unita_vuota_respinta():
    with pytest.raises(ValueError, match="unità"):
        Magnitude(Q(1), "")


def test_scorciatoia_di_costruzione_deduce_l_unita_dal_tipo():
    c = Component.of("R2", "resistor", ("A", "0"), Q(47), "R_2")
    assert c.value == Magnitude(Q(47), "ohm")


# -- versione ------------------------------------------------------------------


def test_versione_semantica_richiesta():
    assert ir().ir_version == "1.0.0"
    with pytest.raises(ValueError, match="semantica"):
        ir(ir_version="1.0")
    with pytest.raises(ValueError, match="semantica"):
        ir(ir_version="uno")


# -- provenienza ---------------------------------------------------------------


AREA = Provenance(Q(1, 10), Q(1, 5), Q(1, 4), Q(1, 4))


def test_sorgente_immagine_esige_provenienza():
    """Senza area, la conferma dell'utente non ha nulla da ancorare (FR-5)."""
    with pytest.raises(ValueError, match="provenienza"):
        ir(source_kind="image")

    con_area = tuple(
        Component(c.id, c.type, c.terminals, c.value, c.symbolic, provenance=AREA)
        for c in ir().components
    )
    assert IR("1.0.0", "dc_resistive", "image", ("0", "A"), con_area,
              (Request("q1", "voltage", "R1"),)).source_kind == "image"


def test_provenienza_su_sorgente_non_fotografica_respinta():
    """Una provenienza inventata è peggio di nessuna provenienza."""
    with pytest.raises(ValueError, match="provenienza"):
        ir(components=(resistore(provenance=AREA),),
           requests=(Request("q1", "voltage", "R1"),))


def test_area_fuori_dai_limiti_respinta():
    with pytest.raises(ValueError, match="lato"):
        Provenance(Q(0), Q(0), Q(0), Q(1, 2))
    with pytest.raises(ValueError, match="riquadro"):
        Provenance(Q(9, 10), Q(0), Q(1, 2), Q(1, 2))
    with pytest.raises(ValueError, match="riquadro"):
        Provenance(Q(-1, 10), Q(0), Q(1, 2), Q(1, 2))


def test_sorgente_di_tipo_sconosciuto_respinta():
    with pytest.raises(ValueError, match="sorgente"):
        ir(source_kind="telepatia")


# -- la validazione preesistente non si perde ----------------------------------


def test_valore_non_positivo_ancora_respinto():
    with pytest.raises(ValueError, match="non positivo"):
        resistore(value=Magnitude(Q(0), "ohm"))


def test_terminali_coincidenti_ancora_respinti():
    with pytest.raises(ValueError, match="coincidenti"):
        resistore(terminals=("A", "A"))


def test_identificatori_ripetuti_respinti():
    """La soluzione e' indicizzata per id: due omonimi, e il secondo sparisce in silenzio."""
    with pytest.raises(ValueError, match="ripetuti: R1"):
        ir(components=(
            Component.of("E1", "voltage_source_dc", ("A", "0"), Q(12), "E_1"),
            Component.of("R1", "resistor", ("A", "0"), Q(10), "R_1"),
            Component.of("R1", "resistor", ("A", "0"), Q(20), "R_1'"),
        ))
