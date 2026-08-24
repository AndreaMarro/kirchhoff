"""Story 2.6 — il contratto di `transform` e i tre Rifiuti di `domain/transform/check`."""

from __future__ import annotations

from fractions import Fraction

import pytest

from kirchhoff.domain.ir import IR, Component
from kirchhoff.domain.refusal import CAUSES, Refusal
from kirchhoff.domain.transform import (
    CATALOG,
    CONTROLLI,
    MUTABLE_ATTRIBUTES,
    Boundary,
    Certificate,
    Equation,
    EntityRef,
    LayoutPatch,
    TransformResult,
    attributes_of,
    check_transform,
    implemented,
    mutable_attributes,
    preserve_set,
    transform,
)
from kirchhoff.domain.validate import validate

F = Fraction
C = lambda i: EntityRef("component", i)      # noqa: E731
N = lambda i: EntityRef("node", i)           # noqa: E731


def _r(cid: str, a: str, b: str, ohm) -> Component:
    return Component.of(cid, "resistor", (a, b), F(ohm), cid)


def _ir(*comps: Component, nodes: tuple[str, ...]) -> IR:
    return IR("1.0.0", "dc_resistive", "netlist", nodes, comps, ())


#: `R1 (a,b) 10Ω` in serie con `R2 (b,0) 20Ω`. Il nodo `b` ha grado 2.
SERIE = _ir(_r("R1", "a", "b", 10), _r("R2", "b", "0", 20), nodes=("0", "a", "b"))

#: `R1` e `R2` fra gli stessi due nodi, piu' un carico che tiene occupato `b`.
PARALLELO = _ir(_r("R1", "a", "b", 10), _r("R2", "a", "b", 20), _r("RL", "b", "0", 5),
                nodes=("0", "a", "b"))


class TestDiscriminanteDiIdentita:
    """AD-22 em. v2.1 — il Catalogo dichiara cosa puo' cambiare, non la Transform."""

    def test_ogni_voce_del_catalogo_dichiara_i_propri_attributi_mutabili(self):
        assert set(MUTABLE_ATTRIBUTES) == CATALOG

    def test_l_insieme_predefinito_e_vuoto(self):
        """«Chi non dichiara nulla non muta nulla.»"""
        assert all(v == frozenset() for v in MUTABLE_ATTRIBUTES.values())
        assert mutable_attributes("serie") == frozenset()

    def test_operazione_fuori_catalogo_non_ha_discriminante(self):
        with pytest.raises(ValueError, match="fuori dal catalogo chiuso"):
            mutable_attributes("REMOVE_LOAD")

    def test_attributi_sostanziali_non_includono_la_provenienza(self):
        """Da dove un componente e' stato letto non e' cio' che il componente e'."""
        assert "provenance" not in attributes_of(_r("R1", "a", "b", 10))

    def test_il_caso_r2a_il_nome_riusato_non_basta_a_restare_preservati(self):
        """Il difetto dell'istruttoria R2-A, eseguito: `R1` da 10Ω che diventa 6⅔Ω."""
        prima = _ir(_r("R1", "a", "b", 10), _r("R2", "a", "b", 20), _r("RL", "b", "0", 5),
                    nodes=("0", "a", "b"))
        dopo = _ir(_r("R1", "a", "b", F(20, 3)), _r("RL", "b", "0", 5),
                   nodes=("0", "a", "b"))
        assert C("R1") not in preserve_set(prima, dopo, operation="parallelo")
        assert C("RL") in preserve_set(prima, dopo, operation="parallelo")

    def test_senza_operazione_la_lettura_e_la_piu_stretta(self):
        """Chi non dice quale operazione sta misurando non ottiene indulgenza."""
        prima = _ir(_r("R1", "a", "0", 10), nodes=("0", "a"))
        dopo = _ir(_r("R1", "a", "0", 99), nodes=("0", "a"))
        assert C("R1") not in preserve_set(prima, dopo)

    def test_un_attributo_dichiarato_mutabile_lascia_l_entita_preservata(self, monkeypatch):
        """CV3: preservato non significa immutato — ma solo per chi lo dichiara."""
        monkeypatch.setitem(MUTABLE_ATTRIBUTES, "serie", frozenset({"value"}))
        prima = _ir(_r("R1", "a", "0", 10), nodes=("0", "a"))
        dopo = _ir(_r("R1", "a", "0", 99), nodes=("0", "a"))
        assert C("R1") in preserve_set(prima, dopo, operation="serie")
        assert C("R1") not in preserve_set(prima, dopo, operation="parallelo")


class TestLayoutPatch:
    """AD-18 em. — nomina entita', non coordinate: il dominio non sa cosa sia una posizione."""

    def test_una_coordinata_al_posto_di_un_entita_e_rifiutata(self):
        with pytest.raises(TypeError, match="nomina entita', non coordinate"):
            LayoutPatch((C("R1"),), (), (12,), (), ())  # type: ignore[arg-type]

    def test_entita_ripetuta_rifiutata(self):
        with pytest.raises(ValueError, match="preserve: entita' ripetuta"):
            LayoutPatch((C("R1"), C("R1")), (), (), (), ())

    def test_identificatore_vuoto_nella_mappa(self):
        with pytest.raises(ValueError, match="non identifica nulla"):
            LayoutPatch((C("R1"),), (), (), (("a", ""),), ())

    def test_mappa_non_funzionale(self):
        with pytest.raises(ValueError, match="mappato due volte"):
            LayoutPatch((C("R1"),), (), (), (("a", "b"), ("a", "c")), ())

    def test_mappa_non_iniettiva(self):
        """Senza iniettivita' due entita' collassano in una, e `Pₖ` si restringe."""
        with pytest.raises(ValueError, match="non e' iniettiva"):
            LayoutPatch((C("R1"),), (), (), (("a", "z"), ("b", "z")), ())

    def test_chi_non_compare_nella_mappa_conserva_il_proprio_nome(self):
        patch = LayoutPatch((C("R1"),), (), (), (("a", "z"),), ())
        assert patch.image_of("a") == "z"
        assert patch.image_of("b") == "b"

    def test_l_ordine_e_canonico_e_non_d_inserimento(self):
        uno = LayoutPatch((C("R2"), C("R1")), (), (), (("b", "y"), ("a", "z")), ())
        due = LayoutPatch((C("R1"), C("R2")), (), (), (("a", "z"), ("b", "y")), ())
        assert uno == due


class TestMembriDelRisultato:
    def test_boundary_vuoto_non_si_costruisce(self):
        with pytest.raises(ValueError, match="non e' un passo"):
            Boundary(())

    def test_equazione_senza_soggetto(self):
        with pytest.raises(ValueError, match="non si sa cosa definisce"):
            Equation("", "R1 + R2")

    def test_equazione_senza_espressione(self):
        with pytest.raises(ValueError, match="senza espressione"):
            Equation("Req", "")

    def test_equazione_leggibile(self):
        assert str(Equation("Req", "R1 + R2")) == "Req = R1 + R2"

    def test_certificato_di_un_operazione_inesistente(self):
        with pytest.raises(ValueError, match="fuori dal\n?\\s*catalogo chiuso|fuori dal "):
            Certificate("REMOVE_LOAD", ("boundary",))  # type: ignore[arg-type]

    def test_certificato_vuoto_si_legge_come_tutto_a_posto(self):
        with pytest.raises(ValueError, match="senza alcun controllo eseguito"):
            Certificate("serie", ())

    def test_certificato_con_un_controllo_elencato_due_volte(self):
        with pytest.raises(ValueError, match="elencato due volte"):
            Certificate("serie", ("boundary", "boundary"))

    def test_preserve_vuoto_autocertifica_il_kill_criterion(self):
        with pytest.raises(ValueError, match="conservare zero"):
            _risultato(preserve=frozenset())

    def test_delta_vuoto_non_e_un_passo(self):
        from kirchhoff.domain.transform import Delta
        with pytest.raises(ValueError, match="non e' un passo"):
            _risultato(delta=Delta(()))


def _risultato(**sovrascritti):
    from kirchhoff.domain.transform import Delta, StructuralDerivation
    campi = dict(
        preserve=frozenset({N("0")}),
        delta=Delta((StructuralDerivation("serie", (C("R1"), C("R2")), (C("Req"),)),)),
        boundary=Boundary((N("0"),)),
        layout_patch=LayoutPatch((N("0"),), (C("R1"),), (C("Req"),), (), (C("Req"),)),
        equation=Equation("Req", "R1 + R2"),
        certificate=Certificate("serie", CONTROLLI),
    )
    return TransformResult(**{**campi, **sovrascritti})


class TestLeTreCauseDiAd19:
    """Le tre cause che AD-19 assegna a `domain/transform/check`, viste sollevare."""

    def test_le_tre_cause_sono_nell_enumerazione_chiusa(self):
        assert {"identity_violation", "preserve_nonmaximal", "empty_boundary"} <= CAUSES

    def test_boundary_assente_produce_empty_boundary(self):
        dopo, _ = _serie_riuscita()
        patch = LayoutPatch(tuple(sorted(preserve_set(SERIE, dopo, operation="serie"))),
                            (), (), (), (N("a"),))
        r = check_transform(SERIE, dopo, "serie", patch, None)
        assert isinstance(r, Refusal) and r.cause == "empty_boundary"

    def test_una_preservata_rinominata_produce_identity_violation(self):
        dopo, _ = _serie_riuscita()
        preservate = preserve_set(SERIE, dopo, operation="serie")
        patch = LayoutPatch(tuple(sorted(preservate)), (), (), (("a", "a2"),), (N("a"),))
        r = check_transform(SERIE, dopo, "serie", patch, Boundary((N("a"), N("0"))))
        assert isinstance(r, Refusal)
        assert r.cause == "identity_violation" and r.subject == "a"

    def test_preserve_diverso_da_pk_in_difetto(self):
        dopo, _ = _serie_riuscita()
        patch = LayoutPatch((N("a"),), (), (), (), (N("a"),))
        r = check_transform(SERIE, dopo, "serie", patch, Boundary((N("a"), N("0"))))
        assert isinstance(r, Refusal) and r.cause == "preserve_nonmaximal"
        assert "node:0" in r.diagnosis

    def test_preserve_diverso_da_pk_in_eccesso(self):
        """«Diverso da», non «piu' piccolo di»: la causa copre entrambi i versi."""
        dopo, _ = _serie_riuscita()
        preservate = preserve_set(SERIE, dopo, operation="serie")
        patch = LayoutPatch((*sorted(preservate), C("R1")), (), (), (), (N("a"),))
        r = check_transform(SERIE, dopo, "serie", patch, Boundary((N("a"), N("0"))))
        assert isinstance(r, Refusal) and r.cause == "preserve_nonmaximal"
        assert "component:R1" in r.diagnosis

    def test_una_sopravvissuta_dichiarata_creata(self):
        """Il verso chiuso il 15 agosto: restringere `Pₖ` per far tornare il riferimento."""
        dopo, _ = _serie_riuscita()
        preservate = preserve_set(SERIE, dopo, operation="serie")
        patch = LayoutPatch(tuple(sorted(preservate)), (), (N("a"),), (), (N("a"),))
        r = check_transform(SERIE, dopo, "serie", patch, Boundary((N("a"), N("0"))))
        assert isinstance(r, Refusal) and r.cause == "preserve_nonmaximal"
        assert r.subject == "a" and r.subject_kind == "node"


def _serie_riuscita() -> tuple[IR, TransformResult]:
    esito = transform(SERIE, "serie", "R1", "R2")
    assert not isinstance(esito, Refusal)
    return esito


class TestContrattoDiTransform:
    """AD-2 em.: `(CircuitIR, TransformResult) | Refusal`, e nient'altro."""

    def test_serie_produce_i_sei_membri_tutti_non_vuoti(self):
        dopo, res = _serie_riuscita()
        assert res.preserve and res.delta.derivations and res.boundary.entities
        assert res.layout_patch.preserve and res.equation and res.certificate.checks

    def test_serie_somma_le_resistenze_e_fa_sparire_il_nodo_interno(self):
        dopo, res = _serie_riuscita()
        assert [c.value.amount for c in dopo.components] == [F(30)]
        assert "b" not in dopo.nodes
        assert dopo.components[0].terminals == ("a", "0")

    def test_parallelo_in_aritmetica_esatta(self):
        esito = transform(PARALLELO, "parallelo", "R1", "R2")
        assert not isinstance(esito, Refusal)
        dopo, res = esito
        eq = next(c for c in dopo.components if c.id != "RL")
        assert eq.value.amount == F(20, 3)
        assert str(res.equation).startswith("(R1·R2 / (R1 + R2))")

    def test_l_equivalente_ha_identita_nuova_e_lineage_nelle_due_direzioni(self):
        dopo, res = _serie_riuscita()
        nuova = C(dopo.components[0].id)
        assert nuova not in res.preserve
        assert res.delta.derived_from(nuova) == (C("R1"), C("R2"))
        assert res.delta.what_happened_to(C("R1")).outputs == (nuova,)

    def test_il_circuito_risultante_supera_la_validazione_elettrica(self):
        prima = _ir(_r("R1", "a", "b", 10), _r("R2", "b", "0", 20),
                    Component.of("V1", "voltage_source_dc", ("a", "0"), F(12), "V1"),
                    nodes=("0", "a", "b"))
        esito = transform(prima, "serie", "R1", "R2")
        assert not isinstance(esito, Refusal)
        assert not isinstance(validate(esito[0]), Refusal)

    def test_stesso_ingresso_stessa_uscita(self):
        """Nessuna I/O, nessun orologio, nessuna casualita' (AD-2)."""
        assert _serie_riuscita()[1] == _serie_riuscita()[1]

    def test_il_certificato_elenca_i_controlli_eseguiti(self):
        assert _serie_riuscita()[1].certificate.checks == tuple(sorted(CONTROLLI))

    def test_operazione_fuori_catalogo_fallisce_prima_di_qualunque_calcolo(self):
        with pytest.raises(ValueError, match="non\\s*si estende a runtime"):
            transform(SERIE, "REMOVE_LOAD", "R1", "R2")  # type: ignore[arg-type]

    def test_il_registro_e_un_sottoinsieme_del_catalogo(self):
        assert implemented() <= CATALOG
        assert implemented() == {"serie", "parallelo"}

    def test_il_catalogo_non_si_estende_a_runtime(self):
        from kirchhoff.domain.transform import engine
        assert not hasattr(engine, "register")
        assert isinstance(CATALOG, frozenset)


class TestPrecondizioniDelleRiduzioni:
    def test_la_riduzione_vale_fra_resistori(self):
        ir = _ir(_r("R1", "a", "b", 10), nodes=("0", "a", "b"))
        ir = IR("1.0.0", "dc_resistive", "netlist", ("0", "a", "b"),
                (*ir.components,
                 Component.of("C1", "capacitor", ("b", "0"), F(1), "C1")), ())
        with pytest.raises(ValueError, match="vale fra resistori"):
            transform(ir, "serie", "R1", "C1")

    def test_due_resistori_senza_nodo_in_comune_non_sono_in_serie(self):
        ir = _ir(_r("R1", "a", "b", 10), _r("R2", "c", "0", 20),
                 nodes=("0", "a", "b", "c"))
        with pytest.raises(ValueError, match="condividono 0 nodi"):
            transform(ir, "serie", "R1", "R2")

    def test_un_nodo_di_grado_tre_non_e_una_serie(self):
        """Se la corrente si divide, la somma delle resistenze non e' l'equivalente."""
        ir = _ir(_r("R1", "a", "b", 10), _r("R2", "b", "0", 20), _r("R3", "b", "0", 30),
                 nodes=("0", "a", "b"))
        with pytest.raises(ValueError, match="ha grado 3"):
            transform(ir, "serie", "R1", "R2")

    def test_due_resistori_su_nodi_diversi_non_sono_in_parallelo(self):
        with pytest.raises(ValueError, match="non stanno fra gli stessi due nodi"):
            transform(SERIE, "parallelo", "R1", "R2")

    def test_l_identita_nuova_non_collide_con_una_esistente(self):
        ir = _ir(_r("R1", "a", "b", 10), _r("R2", "b", "0", 20),
                 _r("R1R2eq", "a", "0", 7), nodes=("0", "a", "b"))
        esito = transform(ir, "serie", "R1", "R2")
        assert not isinstance(esito, Refusal)
        assert {c.id for c in esito[0].components} == {"R1R2eq", "R1R2eq_"}

    def test_un_rifiuto_del_controllore_arriva_a_chi_chiama(self, monkeypatch):
        """Il Rifiuto si restituisce, non si solleva, e non diventa un prodotto (AD-13)."""
        from kirchhoff.domain.transform import engine
        atteso = Refusal("empty_boundary", "serie", "request", "rifiuto simulato")
        monkeypatch.setattr(engine, "check_transform", lambda *a: atteso)
        assert transform(SERIE, "serie", "R1", "R2") is atteso
