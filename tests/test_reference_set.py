import json
from fractions import Fraction
from pathlib import Path

import pytest

from kirchhoff.domain.exact import SQRT3, ZETA, Cyc12, zeta_pow
from kirchhoff.domain.transient import is_natural_frequency
from kirchhoff.eval import (
    generator_ac,
    generator_three_phase,
    generator_transient,
    metrics,
    reference_set,
)
from kirchhoff.eval.generator import generate_case
from kirchhoff.eval.transformations import REFERENCE_TRANSFORMATIONS

CLASSI = [c for c, _ in reference_set.CLASSES]


# -- il criterio centrale: l'oracolo non si autocertifica -----------------------


def test_ogni_caso_verificato_da_metodo_indipendente():
    for seed in range(1, 40):
        ir, expected, _ = generate_case(seed)
        assert reference_set.verify_independently(ir, expected) == []


@pytest.mark.parametrize("genera", [
    generator_transient.generate_case,
    generator_three_phase.generate_case,
])
def test_le_classi_senza_sorteggio_degenere_sono_tutte_verificate(genera):
    for seed in range(1, 25):
        ir, expected, _ = genera(seed)
        assert reference_set.verify_independently(ir, expected) == []


def test_regime_sinusoidale_verificato_o_scartato():
    """Un sorteggio puo' produrre una risonanza esatta: si scarta, non si aggiusta."""
    verificati = 0
    for seed in range(1, 25):
        try:
            ir, expected, _ = generator_ac.generate_case(seed)
        except ZeroDivisionError:
            continue
        assert reference_set.verify_independently(ir, expected) == []
        verificati += 1
    assert verificati > 0


def test_generazione_riproducibile():
    a, _, sa = generate_case(7)
    b, _, sb = generate_case(7)
    assert [c.id for c in a.components] == [c.id for c in b.components]
    assert [c.value for c in a.components] == [c.value for c in b.components]
    assert sa == sb


@pytest.mark.parametrize("genera,cid", [
    (generate_case, "R1"),
    (generator_ac.generate_case, None),
    (generator_three_phase.generate_case, "Ra"),
])
def test_disaccordo_viene_rilevato(genera, cid):
    """Se la risposta-per-costruzione e' sbagliata, la verifica deve accorgersene."""
    ir, expected, _ = genera(3)
    target = cid if cid in expected else next(k for k in expected if k != "E1")
    corrotto = dict(expected)
    corrotto[target] = {**expected[target],
                        "voltage": expected[target]["voltage"] + 1}
    assert reference_set.verify_independently(ir, corrotto) != []


def test_disaccordo_nel_transitorio_viene_rilevato():
    ir, expected, _ = generator_transient.generate_case(0)      # RC del primo ordine
    corrotto = dict(expected)
    corrotto["C1"] = {**expected["C1"], "final_value": expected["C1"]["final_value"] + 1}
    assert reference_set.verify_independently(ir, corrotto) != []


# -- sequenze di Trasformazioni ------------------------------------------------


def test_ogni_caso_porta_una_sequenza_di_trasformazioni_dal_catalogo():
    cases, _ = reference_set.build(8, seed0=900)
    for c in cases:
        assert c.transformations
        assert set(c.transformations) <= REFERENCE_TRANSFORMATIONS


def test_un_nome_fuori_catalogo_e_un_errore():
    from kirchhoff.eval.transformations import validate
    with pytest.raises(ValueError, match="fuori catalogo"):
        validate(("serie", "trucco_magico"))


# -- copertura delle quattro classi --------------------------------------------


def test_le_quattro_classi_sono_tutte_presenti():
    cases, _ = reference_set.build(12, seed0=500)
    assert {c.domain_class for c in cases} == set(CLASSI)


def test_split_stratificato_per_classe(tmp_path: Path):
    """Senza stratificazione la parte trattenuta conterrebbe solo le ultime classi."""
    cases, _ = reference_set.build(12, seed0=600)
    counts = reference_set.write(cases, tmp_path, split=0.5)
    assert counts == {"dev": 8, "holdout": 4}     # 3 casi per classe, taglio a meta' per eccesso
    dev = reference_set.load(tmp_path, "dev")
    holdout = reference_set.load(tmp_path, "holdout", allow_holdout=True)
    assert {c.domain_class for c in dev} == set(CLASSI)
    assert {c.domain_class for c in holdout} == set(CLASSI)


def test_split_e_roundtrip(tmp_path: Path):
    cases, _ = reference_set.build(10, seed0=100)
    counts = reference_set.write(cases, tmp_path, split=0.6)
    assert counts == {"dev": 6, "holdout": 4}
    dev = reference_set.load(tmp_path, "dev")
    assert len(dev) == 6
    for c in dev:
        assert reference_set.verify_independently(c.ir, c.expected) == []


def test_holdout_non_leggibile_in_sviluppo(tmp_path: Path):
    cases, _ = reference_set.build(6, seed0=200)
    reference_set.write(cases, tmp_path, split=0.5)
    with pytest.raises(reference_set.HoldoutAccessError):
        reference_set.load(tmp_path, "holdout")
    assert len(reference_set.load(tmp_path, "holdout", allow_holdout=True)) == 2


# -- serializzazione: nessun valore degrada a virgola mobile -------------------


def test_il_giro_di_serializzazione_conserva_il_campo_ciclotomico(tmp_path: Path):
    ir, expected, seq = generator_three_phase.generate_case(1)   # triangolo
    caso = reference_set.Case("3f-test", ir, expected, "three_phase", seq)
    riletto = reference_set.from_json(json.loads(json.dumps(reference_set.to_json(caso))))
    assert riletto.expected == caso.expected
    assert riletto.ir == caso.ir
    assert riletto.transformations == seq
    valore = next(iter(riletto.expected["Rab"].values()))
    assert isinstance(valore, Cyc12)


def test_un_valore_atteso_di_tipo_estraneo_non_si_serializza():
    with pytest.raises(TypeError, match="non serializzabile"):
        reference_set._enc(0.5)


# -- proprieta' che solo l'aritmetica esatta puo' soddisfare -------------------


def test_le_tre_correnti_di_fase_sommano_esattamente_a_zero():
    ir, expected, _ = generator_three_phase.generate_case(0)   # stella
    somma = expected["Ra"]["current"] + expected["Rb"]["current"] + expected["Rc"]["current"]
    assert somma == 0
    assert expected["VN"]["current"] == 0


def test_la_tensione_concatenata_porta_sqrt_di_tre():
    ir, expected, _ = generator_three_phase.generate_case(1)   # triangolo
    e = next(c.value.amount for c in ir.components if c.id == "Ea")
    v_ab = expected["Rab"]["voltage"] + expected["Lab"]["voltage"]
    assert v_ab == Cyc12.of(e) * SQRT3 * ZETA
    assert generator_three_phase.concatenata(e) == v_ab


def test_le_radici_del_secondo_ordine_annullano_la_matrice():
    for seed in (2, 3, 6, 7):
        ir, expected, _ = generator_transient.generate_case(seed)
        radici = [v for d in expected.values() for k, v in d.items() if k.startswith("root_")]
        assert len(radici) == 2
        for s in radici:
            assert s < 0
            assert is_natural_frequency(ir, s)


def test_la_costante_di_tempo_del_primo_ordine_e_una_frequenza_naturale():
    for seed in (0, 1, 4, 5):
        ir, expected, _ = generator_transient.generate_case(seed)
        tau = next(d["time_constant"] for d in expected.values() if "time_constant" in d)
        assert tau > 0
        assert is_natural_frequency(ir, -1 / tau)


def test_lo_sfasamento_e_un_intero_di_passi_da_trenta_gradi():
    ir, _, _ = generator_three_phase.generate_case(0)
    passi = sorted(c.phase_steps for c in ir.components if c.id in ("Ea", "Eb", "Ec"))
    assert passi == [-4, 0, 4]
    assert zeta_pow(-4) * zeta_pow(4) == 1


# -- l'harness misura davvero --------------------------------------------------


def test_harness_rileva_un_errore_silenzioso():
    """Un solver che pubblica un valore sbagliato deve produrre SER > 0."""
    cases, _ = reference_set.build(8, seed0=300)

    def bugged(ir):
        good = metrics.reference_solver(ir)
        sbagliati = {k: v + Fraction(1, 1000) for k, v in good.values.items()}
        return metrics.Outcome(published=True, values=sbagliati)

    rep = metrics.run(cases, bugged, "test")
    assert rep.ser == 1.0
    assert rep.vsr == 0.0


def test_harness_su_solver_corretto():
    cases, _ = reference_set.build(12, seed0=400)
    rep = metrics.run(cases, metrics.reference_solver, "test")
    assert rep.ser == 0.0
    assert rep.vsr == 1.0
    assert rep.published == rep.total


def test_ricostruire_non_lascia_casi_vecchi(tmp_path: Path):
    """Un caso rimasto da una costruzione precedente misurerebbe un sistema che non c'e' piu'."""
    grandi, _ = reference_set.build(12, seed0=700)
    reference_set.write(grandi, tmp_path, split=0.5)
    piccoli, _ = reference_set.build(4, seed0=800)
    reference_set.write(piccoli, tmp_path, split=0.5)
    riletti = (reference_set.load(tmp_path, "dev")
               + reference_set.load(tmp_path, "holdout", allow_holdout=True))
    assert len(riletti) == 4
    assert {c.case_id for c in riletti} == {c.case_id for c in piccoli}


def test_la_provenienza_sopravvive_al_giro_di_serializzazione():
    """Quando la sorgente e' un'immagine, l'area va e torna esatta: e' cio' che la
    conferma dell'utente ancora (FR-5)."""
    from kirchhoff.domain.ir import IR, Component, Magnitude, Provenance, Request

    area = Provenance(Fraction(1, 10), Fraction(1, 5), Fraction(1, 4), Fraction(3, 8))
    comps = (
        Component("E1", "voltage_source_dc", ("A", "0"),
                  Magnitude(Fraction(12), "volt"), "E_1", provenance=area),
        Component("R1", "resistor", ("A", "0"),
                  Magnitude(Fraction(10), "ohm"), "R_1", provenance=area),
    )
    ir = IR("1.0.0", "dc_resistive", "image", ("0", "A"), comps,
            (Request("q1", "voltage", "R1"),))
    caso = reference_set.Case("img-00001", ir, {}, "dc_resistive", ("legge_di_ohm",))

    riletto = reference_set.from_json(json.loads(json.dumps(reference_set.to_json(caso))))
    assert riletto.ir == caso.ir
    assert riletto.ir.component("R1").provenance == area
    assert riletto.ir.component("R1").value.unit == "ohm"
