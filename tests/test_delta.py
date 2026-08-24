"""Contratto di `Delta`. Ogni invariante ha un test che l'ha visto sollevare."""

from __future__ import annotations

from fractions import Fraction

import pytest

from kirchhoff.domain.ir import IR, Component
from kirchhoff.domain.transform import (
    CATALOG, Delta, DeltaViolation, EntityRef, StructuralDerivation,
    check_delta, entities_of, preserve_set,
)
from kirchhoff.eval.transformations import REFERENCE_TRANSFORMATIONS

F = Fraction
C = lambda i: EntityRef("component", i)      # noqa: E731
N = lambda i: EntityRef("node", i)           # noqa: E731


def _r(cid: str, a: str, b: str, ohm: int) -> Component:
    return Component.of(cid, "resistor", (a, b), F(ohm), cid)


def _ir(*comps: Component, nodes: tuple[str, ...]) -> IR:
    return IR("1.0.0", "dc_resistive", "netlist", nodes, comps, ())


class TestCatalogo:
    def test_il_catalogo_del_dominio_e_quello_di_riferimento_coincidono(self):
        """La riconciliazione promessa da eval/transformations.py, come gate."""
        assert CATALOG == REFERENCE_TRANSFORMATIONS

    def test_operazione_fuori_catalogo_rifiutata(self):
        with pytest.raises(ValueError, match="fuori dal catalogo chiuso"):
            StructuralDerivation("REMOVE_LOAD", (C("RL"),), ())  # type: ignore[arg-type]


class TestEntityRef:
    def test_genere_sconosciuto(self):
        with pytest.raises(ValueError, match="genere di entita'"):
            EntityRef("ramo", "b1")  # type: ignore[arg-type]

    def test_senza_identificatore(self):
        with pytest.raises(ValueError, match="senza identificatore"):
            EntityRef("component", "")

    def test_nessuna_geometria_nel_tipo(self):
        """Invariante 7: non c'e' un campo dove infilare una coordinata."""
        campi = set(EntityRef.__slots__) | set(StructuralDerivation.__slots__) | set(Delta.__slots__)
        vietati = {"x", "y", "position", "bbox", "order", "color", "layer", "anchor"}
        assert campi & vietati == set()


class TestDerivazione:
    def test_rimozione_uscite_vuote_ammessa(self):
        d = StructuralDerivation("resistenza_equivalente_di_thevenin", (C("RL"),), ())
        assert d.outputs == ()

    def test_una_derivazione_senza_ingressi_e_rifiutata(self):
        """Decisione esplicita, non omissione: nel catalogo chiuso non esiste oggi
        una creazione senza ascendenza. Se comparira', questo test cambia."""
        with pytest.raises(ValueError, match="senza entita' in ingresso"):
            StructuralDerivation("serie", (), (C("Req"),))

    def test_ingresso_ripetuto(self):
        with pytest.raises(ValueError, match="ingresso ripetuto"):
            StructuralDerivation("serie", (C("R1"), C("R1")), (C("Req"),))

    def test_uscita_ripetuta(self):
        with pytest.raises(ValueError, match="uscita ripetuta"):
            StructuralDerivation("serie", (C("R1"),), (C("Req"), C("Req")))

    def test_gli_insiemi_sono_ordinati_canonicamente_alla_costruzione(self):
        a = StructuralDerivation("serie", (C("R2"), C("R1")), (C("Req"),))
        b = StructuralDerivation("serie", (C("R1"), C("R2")), (C("Req"),))
        assert a == b
        assert a.inputs == (C("R1"), C("R2"))


class TestDelta:
    SERIE = StructuralDerivation("serie", (C("R1"), C("R2")), (C("Req"),))
    PARALLELO = StructuralDerivation("parallelo", (C("R3"), C("R4")), (C("Rp"),))

    def test_ordine_canonico_indipendente_dall_inserimento(self):
        """Invariante 6: stesso contenuto, ordine diverso, stesso oggetto e stessa
        serializzazione. Senza questo, replay e certificate divergono per rumore."""
        uno = Delta((self.SERIE, self.PARALLELO))
        due = Delta((self.PARALLELO, self.SERIE))
        assert uno == due
        assert [str(d) for d in uno.derivations] == [str(d) for d in due.derivations]

    def test_derivazione_ripetuta_identica(self):
        with pytest.raises(ValueError, match="ripetuta identica"):
            Delta((self.SERIE, self.SERIE))

    def test_entita_consumata_due_volte(self):
        altra = StructuralDerivation("parallelo", (C("R1"), C("R9")), (C("Rp"),))
        with pytest.raises(ValueError, match="consumata due volte"):
            Delta((self.SERIE, altra))

    def test_entita_prodotta_da_due_derivazioni(self):
        altra = StructuralDerivation("parallelo", (C("R3"), C("R4")), (C("Req"),))
        with pytest.raises(ValueError, match="prodotta da due derivazioni"):
            Delta((self.SERIE, altra))

    def test_delta_vuoto_e_legittimo(self):
        assert Delta().derivations == ()


class TestInterrogabilita:
    """Invariante 8: entrambe le direzioni cadono dal modello, senza indice parallelo."""

    D = Delta((StructuralDerivation("serie", (C("R1"), C("R2")), (C("Req"),)),))

    def test_che_fine_ha_fatto_R1(self):
        d = self.D.what_happened_to(C("R1"))
        assert d is not None
        assert d.operation == "serie"
        assert d.outputs == (C("Req"),)

    def test_da_cosa_deriva_Req(self):
        assert self.D.derived_from(C("Req")) == (C("R1"), C("R2"))

    def test_su_un_entita_estranea_non_inventa_nulla(self):
        assert self.D.what_happened_to(C("R9")) is None
        assert self.D.derived_from(C("R9")) == ()


class TestCoerenzaColCircuito:
    PRIMA = _ir(_r("R1", "a", "b", 10), _r("R2", "b", "0", 20), nodes=("0", "a", "b"))
    DOPO = _ir(_r("Req", "a", "0", 30), nodes=("0", "a"))

    def test_una_fusione_in_serie_regge(self):
        delta = Delta((
            StructuralDerivation("serie", (C("R1"), C("R2")), (C("Req"),)),
            StructuralDerivation("serie", (N("b"),), ()),
        ))
        assert check_delta(delta, self.PRIMA, self.DOPO) == ()

    def test_preserve_set_si_calcola_dai_circuiti_non_dal_delta(self):
        """CV1: nessuno dei due insiemi si deduce dall'altro."""
        assert preserve_set(self.PRIMA, self.DOPO) == frozenset({N("0"), N("a")})

    def test_sparizione_non_spiegata(self):
        delta = Delta((StructuralDerivation("serie", (C("R1"), C("R2")), (C("Req"),)),))
        codici = [v.code for v in check_delta(delta, self.PRIMA, self.DOPO)]
        assert "sparizione_non_spiegata" in codici

    def test_comparsa_non_spiegata(self):
        delta = Delta((StructuralDerivation("serie", (C("R1"), C("R2")), ()),
                       StructuralDerivation("parallelo", (N("b"),), ())))
        codici = [v.code for v in check_delta(delta, self.PRIMA, self.DOPO)]
        assert "comparsa_non_spiegata" in codici

    def test_input_inesistente(self):
        delta = Delta((
            StructuralDerivation("serie", (C("R1"), C("R2"), C("R9")), (C("Req"),)),
            StructuralDerivation("serie", (N("b"),), ()),
        ))
        v = [x for x in check_delta(delta, self.PRIMA, self.DOPO) if x.code == "input_inesistente"]
        assert [x.subject for x in v] == ["component:R9"]

    def test_output_inesistente(self):
        delta = Delta((
            StructuralDerivation("serie", (C("R1"), C("R2")), (C("Req"), C("Rz"))),
            StructuralDerivation("serie", (N("b"),), ()),
        ))
        v = [x for x in check_delta(delta, self.PRIMA, self.DOPO) if x.code == "output_inesistente"]
        assert [x.subject for x in v] == ["component:Rz"]

    def test_una_preservata_non_puo_essere_consumata(self):
        delta = Delta((
            StructuralDerivation("serie", (C("R1"), C("R2")), (C("Req"),)),
            StructuralDerivation("serie", (N("b"), N("a")), ()),
        ))
        v = [x for x in check_delta(delta, self.PRIMA, self.DOPO) if x.code == "preservata_consumata"]
        assert [x.subject for x in v] == ["node:a"]

    def test_una_preservata_PUO_essere_uscita_perche_e_li_che_atterra_una_fusione(self):
        """Unione di nodi: `n2` sparisce dentro `n1`, che sopravvive."""
        prima = _ir(_r("R1", "n1", "0", 10), _r("R2", "n2", "0", 20), nodes=("0", "n1", "n2"))
        dopo = _ir(_r("R1", "n1", "0", 10), _r("R2", "n1", "0", 20), nodes=("0", "n1"))
        delta = Delta((StructuralDerivation("parallelo", (N("n2"),), (N("n1"),)),))
        assert check_delta(delta, prima, dopo) == ()
        assert N("n1") in preserve_set(prima, dopo)

    def test_il_nome_riusato_da_una_fusione_non_e_una_falsa_accusa(self):
        """Il caso R2-A, dal lato di `check_delta`.

        `R1 (a,b) 10Ω` e `R2 (a,b) 20Ω` fondono in una equivalente battezzata
        `R1 (a,b) 6⅔Ω`. Con `Pₖ` calcolato per solo identificatore — la seconda
        definizione che viveva in questo modulo — `component:R1` risultava
        «preservata», quindi la derivazione che la consuma davvero veniva segnalata
        `preservata_consumata`: un passo corretto accusato di una violazione. Una
        falsa accusa e' il difetto peggiore di questo prodotto.
        """
        prima = _ir(_r("R1", "a", "b", 10), _r("R2", "a", "b", 20),
                    _r("RL", "b", "0", 5), nodes=("0", "a", "b"))
        dopo = _ir(_r("R1", "a", "b", F(20, 3)), _r("RL", "b", "0", 5),
                   nodes=("0", "a", "b"))
        assert C("R1") not in preserve_set(prima, dopo, operation="parallelo")
        delta = Delta((StructuralDerivation(
            "parallelo", (C("R1"), C("R2")), (C("R1"),)),))
        codici = [v.code for v in check_delta(delta, prima, dopo, operation="parallelo")]
        assert "preservata_consumata" not in codici

    def test_una_definizione_sola_di_pk_in_questo_modulo(self):
        """E-62: due predicati per la stessa cosa divergono dove nessuno guarda."""
        import inspect
        from kirchhoff.domain.transform import check
        corpo = inspect.getsource(check.check_delta)
        assert "preserve_set(" in corpo
        assert "prima & dopo" not in corpo

    def test_le_violazioni_sono_deterministiche(self):
        delta = Delta((StructuralDerivation("serie", (C("R1"),), ()),))
        a = check_delta(delta, self.PRIMA, self.DOPO)
        b = check_delta(delta, self.PRIMA, self.DOPO)
        assert a == b and len(a) > 0
        assert all(isinstance(v, DeltaViolation) for v in a)
