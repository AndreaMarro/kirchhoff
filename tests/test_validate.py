"""Story 2.4 — un test per riga della matrice, piu' l'assenza di falsi positivi."""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

import pytest

from kirchhoff.domain.ir import IR, Component, Request
from kirchhoff.domain.refusal import Refusal
from kirchhoff.domain.validate import Suspicion, Validated, validate
from kirchhoff.eval.reference_set import from_json

F = Fraction


def _ir(*componenti: Component, nodes: tuple[str, ...], requests=(), source="netlist") -> IR:
    return IR("1.0.0", "dc_resistive", source, nodes, componenti, tuple(requests))


def _r(cid: str, a: str, b: str, ohm: int) -> Component:
    return Component.of(cid, "resistor", (a, b), F(ohm), cid)


def _v(cid: str, p: str, m: str, volt: int) -> Component:
    return Component.of(cid, "voltage_source_dc", (p, m), F(volt), cid)


def _i(cid: str, f: str, t: str, amp: int) -> Component:
    return Component.of(cid, "current_source_dc", (f, t), F(amp), cid)


PARTITORE = _ir(
    _v("V1", "n1", "0", 12), _r("R1", "n1", "n2", 10), _r("R2", "n2", "0", 20),
    nodes=("0", "n1", "n2"),
    requests=(Request("q1", "voltage", "R2"),),
)


class TestPromozione:
    def test_un_ir_valido_e_promosso(self):
        esito = validate(PARTITORE)
        assert isinstance(esito, Validated)
        assert esito.ir is PARTITORE
        assert esito.suspicions == ()

    def test_l_esito_e_deterministico(self):
        assert validate(PARTITORE) == validate(PARTITORE)


class TestTopologia:
    def test_grafo_non_connesso_nomina_il_nodo(self):
        ir = _ir(
            _v("V1", "n1", "0", 12), _r("R1", "n1", "0", 10),
            _r("R2", "n8", "n9", 10), _r("R3", "n8", "n9", 20),
            nodes=("0", "n1", "n8", "n9"),
        )
        esito = validate(ir)
        assert isinstance(esito, Refusal)
        assert esito.cause == "topology"
        assert esito.subject_kind == "node"
        assert esito.subject in ("n8", "n9")
        assert "non e' collegato" in esito.diagnosis

    def test_nodo_di_grado_uno_nomina_il_ramo_aperto(self):
        ir = _ir(
            _v("V1", "n1", "0", 12), _r("R1", "n1", "0", 10), _r("R2", "n1", "sospeso", 10),
            nodes=("0", "n1", "sospeso"),
        )
        esito = validate(ir)
        assert isinstance(esito, Refusal)
        assert esito.subject == "sospeso"
        assert "R2" in esito.diagnosis

    def test_maglia_di_soli_generatori_di_tensione(self):
        ir = _ir(
            _v("V1", "n1", "0", 12), _v("V2", "n1", "0", 5), _r("R1", "n1", "0", 10),
            nodes=("0", "n1"),
        )
        esito = validate(ir)
        assert isinstance(esito, Refusal)
        assert esito.cause == "topology"
        assert esito.subject == "V2"
        assert esito.subject_kind == "component"

    def test_nodo_di_soli_generatori_di_corrente_che_non_si_annullano(self):
        ir = _ir(
            _i("I1", "0", "n1", 2), _i("I2", "0", "n1", 3), _r("R1", "0", "n1", 5),
            nodes=("0", "n1"),
        )
        # n1 ha anche R1: il taglio non e' di soli generatori, quindi passa.
        assert isinstance(validate(ir), Validated)

        ir2 = _ir(
            _i("I1", "0", "nx", 2), _i("I2", "0", "nx", 3), _r("R1", "0", "n1", 5),
            _r("R2", "0", "n1", 5),
            nodes=("0", "n1", "nx"),
        )
        esito = validate(ir2)
        assert isinstance(esito, Refusal)
        assert esito.subject == "nx"
        assert "Kirchhoff" in esito.diagnosis


class TestGrandezzeRichieste:
    def test_richiesta_su_componente_inesistente(self):
        # L'IR stesso rifiuta il caso alla costruzione: il gate deve comunque avere
        # il proprio controllo, perche' un IR puo' arrivargli per altre vie.
        with pytest.raises(ValueError, match="inesistente"):
            _ir(_r("R1", "n1", "0", 10), _r("R2", "n1", "0", 10),
                nodes=("0", "n1"), requests=(Request("q1", "voltage", "R9"),))

    def test_il_controllo_del_gate_scatta_su_un_ir_costruito_di_lato(self):
        ir = object.__new__(IR)
        object.__setattr__(ir, "ir_version", "1.0.0")
        object.__setattr__(ir, "domain", "dc_resistive")
        object.__setattr__(ir, "source_kind", "netlist")
        object.__setattr__(ir, "nodes", ("0", "n1"))
        object.__setattr__(ir, "components", (_r("R1", "n1", "0", 10), _r("R2", "n1", "0", 20)))
        object.__setattr__(ir, "requests", (Request("q1", "voltage", "R9"),))
        object.__setattr__(ir, "omega", Fraction(0))
        esito = validate(ir)
        assert isinstance(esito, Refusal)
        assert esito.cause == "unsolvable"
        assert esito.subject == "R9"
        assert esito.subject_kind == "request"


class TestUnita:
    def test_unita_incoerente_col_tipo_e_respinta_dallo_schema(self):
        with pytest.raises(ValueError, match="attesa l'unita'|attesa l'unità"):
            Component("R1", "resistor", ("n1", "0"),
                      __import__("kirchhoff.domain.ir", fromlist=["Magnitude"]).Magnitude(F(10), "farad"),
                      "R1")

    def test_il_gate_ha_comunque_il_proprio_controllo(self):
        rotto = object.__new__(Component)
        from kirchhoff.domain.ir import Magnitude
        for campo, valore in (("id", "R1"), ("type", "resistor"), ("terminals", ("n1", "0")),
                              ("value", Magnitude(F(10), "farad")), ("symbolic", "R1"),
                              ("phase_steps", 0), ("provenance", None)):
            object.__setattr__(rotto, campo, valore)
        ir = object.__new__(IR)
        for campo, valore in (("ir_version", "1.0.0"), ("domain", "dc_resistive"),
                              ("source_kind", "netlist"), ("nodes", ("0", "n1")),
                              ("components", (rotto,)), ("requests", ()), ("omega", Fraction(0))):
            object.__setattr__(ir, campo, valore)
        esito = validate(ir)
        assert isinstance(esito, Refusal)
        assert esito.cause == "units"
        assert esito.subject == "R1"
        assert "farad" in esito.diagnosis and "ohm" in esito.diagnosis


class TestSospetti:
    def _manoscritto(self, ohm: int) -> IR:
        from kirchhoff.domain.ir import Provenance
        prov = Provenance(F(1, 10), F(1, 10), F(1, 10), F(1, 10))
        comps = (
            Component.of("V1", "voltage_source_dc", ("n1", "0"), F(12), "V1", provenance=prov),
            Component.of("R1", "resistor", ("n1", "n2"), F(ohm), "R1", provenance=prov),
            Component.of("R2", "resistor", ("n2", "0"), F(220), "R2", provenance=prov),
        )
        return IR("1.0.0", "dc_resistive", "image", ("0", "n1", "n2"), comps, ())

    def test_valore_fuori_serie_e_sospetto_ma_non_blocca(self):
        esito = validate(self._manoscritto(37))
        assert isinstance(esito, Validated)
        assert [s.subject for s in esito.suspicions] == ["R1"]
        assert isinstance(esito.suspicions[0], Suspicion)
        assert "E12/E24" in esito.suspicions[0].note

    @pytest.mark.parametrize("ohm", [10, 47, 100, 220, 4700, 91000, 12])
    def test_i_valori_in_serie_non_sono_sospetti(self, ohm: int):
        assert validate(self._manoscritto(ohm)).suspicions == ()

    def test_fuori_da_una_sorgente_fotografica_nessun_sospetto(self):
        ir = _ir(_v("V1", "n1", "0", 12), _r("R1", "n1", "n2", 37), _r("R2", "n2", "0", 220),
                 nodes=("0", "n1", "n2"))
        assert validate(ir).suspicions == ()


class TestNessunFalsoPositivo:
    """Terzo criterio di accettazione: sull'insieme di sviluppo, zero rifiuti."""

    def test_l_intero_split_dev_e_promosso(self):
        radice = Path(__file__).resolve().parent.parent / "reference-set" / "dev"
        casi = sorted(radice.glob("*.json"))
        assert len(casi) >= 30, f"insieme di sviluppo troppo piccolo: {len(casi)} casi"
        rifiutati = []
        for percorso in casi:
            caso = from_json(json.loads(percorso.read_text()))
            esito = validate(caso.ir)
            if isinstance(esito, Refusal):
                rifiutati.append((caso.case_id, esito.cause, esito.subject, esito.diagnosis))
        assert rifiutati == [], f"falsi positivi su {len(rifiutati)} casi: {rifiutati[:5]}"


class TestRefusalSiDifende:
    """AD-19: l'enumerazione e' chiusa e il soggetto e' obbligatorio. Le quattro
    guardie del costruttore sono la sola cosa che lo rende vero."""

    def test_causa_fuori_dall_enumerazione(self):
        with pytest.raises(ValueError, match="enumerazione chiusa"):
            Refusal("segni", "R1", "component", "diagnosi")  # type: ignore[arg-type]

    def test_genere_di_soggetto_sconosciuto(self):
        with pytest.raises(ValueError, match="genere di soggetto"):
            Refusal("topology", "R1", "ramo", "diagnosi")  # type: ignore[arg-type]

    def test_senza_soggetto_non_e_una_domanda_mirata(self):
        with pytest.raises(ValueError, match="senza soggetto"):
            Refusal("topology", "", "component", "diagnosi")

    def test_senza_diagnosi(self):
        with pytest.raises(ValueError, match="senza diagnosi"):
            Refusal("topology", "R1", "component", "")


class TestSerieSottoLaDecade:
    """La normalizzazione della mantissa deve salire, non solo scendere: un 4,7 ohm
    e' in serie E24 quanto un 47 k."""

    def _manoscritto_ohm(self, amount: Fraction) -> IR:
        from kirchhoff.domain.ir import Provenance
        prov = Provenance(F(1, 10), F(1, 10), F(1, 10), F(1, 10))
        comps = (
            Component.of("V1", "voltage_source_dc", ("n1", "0"), F(12), "V1", provenance=prov),
            Component.of("R1", "resistor", ("n1", "n2"), amount, "R1", provenance=prov),
            Component.of("R2", "resistor", ("n2", "0"), F(220), "R2", provenance=prov),
        )
        return IR("1.0.0", "dc_resistive", "image", ("0", "n1", "n2"), comps, ())

    def test_quattro_virgola_sette_ohm_e_in_serie(self):
        assert validate(self._manoscritto_ohm(F(47, 10))).suspicions == ()

    def test_tre_virgola_sette_ohm_non_lo_e(self):
        esito = validate(self._manoscritto_ohm(F(37, 10)))
        assert [s.subject for s in esito.suspicions] == ["R1"]


class TestTaglioDiCorrenteCoerente:
    """Il controllo cerca una contraddizione della KCL, non una difficolta' di
    risoluzione. Due generatori di corrente in serie con la stessa corrente sono
    coerenti: il nodo non e' risolvibile da solo, ma non e' contraddittorio, e la
    Validazione elettrica non e' il posto dove dirlo."""

    def test_correnti_che_si_annullano_non_sono_un_rifiuto(self):
        ir = _ir(
            _i("I1", "0", "nx", 2), _i("I2", "nx", "0", 2),
            _r("R1", "0", "n1", 5), _r("R2", "0", "n1", 5),
            nodes=("0", "n1", "nx"),
        )
        assert isinstance(validate(ir), Validated)
