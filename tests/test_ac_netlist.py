"""An explicit AC netlist must retain frequency, phase and domain boundaries."""

from fractions import Fraction as F

import pytest

from kirchhoff.domain.exact import Cyc12, J
from kirchhoff.domain.independent_phasor import solve_phasor_tableau
from kirchhoff.domain.mna import solve_phasor
from kirchhoff.pipeline.lesson import create_lesson
from kirchhoff.pipeline.capabilities import product_capabilities
from kirchhoff.pipeline.netlist import leggi


AC = ("@ac 100 rad/s\nV1 a 0 10 volt 30deg\nR1 a b 3 ohm\n"
      "L1 b 0 1/25 henry\nC1 b 0 1/100 farad\n"
      "I1 0 a 2 ampere -60deg\n? current R1")


def test_typed_ac_netlist_reaches_both_exact_independent_assemblies():
    ir = leggi(AC)
    assert ir.domain == "ac_sinusoidal"
    assert ir.omega == F(100)
    assert ir.component("V1").type == "voltage_source_ac"
    assert ir.component("V1").phase_steps == 1
    assert ir.component("I1").type == "current_source_ac"
    assert ir.component("I1").phase_steps == -2
    mna = solve_phasor(ir)
    assert mna == solve_phasor_tableau(ir)
    assert mna["R1"]["voltage"] == Cyc12.of(3) * mna["R1"]["current"]
    assert mna["L1"]["voltage"] == J * Cyc12.of(4) * mna["L1"]["current"]
    assert create_lesson(AC)["outcome"] == "refusal"  # no AC lesson claim yet
    capabilities = product_capabilities(AC)
    assert capabilities["ac"] is False
    assert capabilities["circuit"]["outcome"] == "refusal"


@pytest.mark.parametrize("text,reason", [
    (AC.replace("@ac 100 rad/s", "@ac 0 rad/s"), "positiva"),
    (AC.replace("@ac 100 rad/s", "@ac 100 Hz"), "rad/s"),
    (AC.replace("30deg", "15deg"), "30"),
    (AC.replace("30deg", "30.5deg"), "30"),
    (AC.replace("V1 a 0 10 volt 30deg", "V1 a 0 10 volt"), "fase"),
    (AC.replace("@ac 100 rad/s\n", ""), "riga"),
    (AC.replace("R1 a b 3 ohm", "E1 a b a 0 2 siemens"), "attesa.*dimensionless"),
    (AC.replace("@ac 100 rad/s", "@ac 100 rad/s\n@ac 200 rad/s"), "una sola"),
    (AC.replace("@ac 100 rad/s\n", "V2 a 0 1 volt\n@ac 100 rad/s\n"), "prima"),
])
def test_ac_netlist_refuses_ambiguous_or_unsupported_inputs(text, reason):
    with pytest.raises(ValueError, match=reason):
        leggi(text)
