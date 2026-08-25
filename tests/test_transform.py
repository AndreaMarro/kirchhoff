"""Story 2.6 — il contratto di `transform` e i tre Rifiuti di `domain/transform/check`."""

from __future__ import annotations

from fractions import Fraction

import pytest

from kirchhoff.domain.ir import IR, Component, Provenance, Request
from kirchhoff.domain.refusal import (
    CAUSES,
    SUBJECT_KINDS,
    Cause,
    Refusal,
    SubjectKind,
)
from kirchhoff.domain.transform import (
    CATALOG,
    CONTROLLI,
    MUTABLE_ATTRIBUTES,
    SUPPORTED,
    Boundary,
    CatalogOpening,
    Certificate,
    Equation,
    EntityRef,
    LayoutPatch,
    TransformResult,
    attributes_of,
    check_delta,
    check_transform,
    implemented,
    mutable_attributes,
    preserve_set,
    transform,
    transformations_supported,
)
from kirchhoff.domain.validate import validate

F = Fraction
C = lambda i: EntityRef("component", i)      # noqa: E731
N = lambda i: EntityRef("node", i)           # noqa: E731


def _r(cid: str, a: str, b: str, ohm) -> Component:
    return Component.of(cid, "resistor", (a, b), F(ohm), cid)


def _v(cid: str, a: str, b: str, volt) -> Component:
    return Component.of(cid, "voltage_source_dc", (a, b), F(volt), cid)


def _ir(*comps: Component, nodes: tuple[str, ...], requests=()) -> IR:
    return IR("1.0.0", "dc_resistive", "netlist", nodes, comps, requests)


def _eq(ir: IR, *noti: str) -> Component:
    """L'equivalente: l'unico componente che non c'era prima."""
    return next(c for c in ir.components if c.id not in noti)


#: `R1 (a,b) 10Ω` in serie con `R2 (b,0) 20Ω`. Il nodo `b` ha grado 2.
#:
#: Il generatore non e' decorativo: un criterio della storia dice che «il `CircuitIR`
#: risultante supera la validazione elettrica», e su una fixture senza sorgente quel
#: criterio non e' verificabile — `validate` la rifiuta *prima* per rami aperti, e il
#: test misurerebbe la fixture invece del passo.
SERIE = _ir(_v("V1", "a", "0", 12), _r("R1", "a", "b", 10), _r("R2", "b", "0", 20),
            nodes=("0", "a", "b"))

#: `R1` e `R2` fra gli stessi due nodi, piu' un carico che tiene occupato `b`.
PARALLELO = _ir(_v("V1", "a", "0", 12), _r("R1", "a", "b", 10), _r("R2", "a", "b", 20),
                _r("RL", "b", "0", 5), nodes=("0", "a", "b"))


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
        """CV3: preservato non significa immutato — ma solo per chi lo dichiara.

        La dichiarazione si raggiunge dal `dict` privato, non dalla vista pubblica:
        e' il test a scavalcare il recinto, esplicitamente, e non il recinto a non
        esserci.
        """
        from kirchhoff.domain.transform import catalog
        monkeypatch.setitem(catalog._MUTABILI, "serie", frozenset({"value"}))
        prima = _ir(_r("R1", "a", "0", 10), nodes=("0", "a"))
        dopo = _ir(_r("R1", "a", "0", 99), nodes=("0", "a"))
        assert C("R1") in preserve_set(prima, dopo, operation="serie")
        assert C("R1") not in preserve_set(prima, dopo, operation="parallelo")

    def test_la_dichiarazione_non_si_riscrive_con_un_assegnazione(self):
        """`CATALOG` e `SUPPORTED` sono frozenset; il discriminante non era protetto.

        Cambiare `MUTABLE_ATTRIBUTES["serie"]` a runtime avrebbe spostato **senza
        alcuna decisione** il riferimento rispetto a cui `Pₖ` e' misurato, nel modulo
        che dichiara il vocabolario chiuso per sempre.
        """
        with pytest.raises(TypeError):
            MUTABLE_ATTRIBUTES["serie"] = frozenset({"value"})  # type: ignore[index]
        assert mutable_attributes("serie") == frozenset()


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
        eq = _eq(dopo, "V1")
        assert eq.value.amount == F(30)
        assert "b" not in dopo.nodes
        assert eq.terminals == ("a", "0")

    def test_parallelo_in_aritmetica_esatta(self):
        esito = transform(PARALLELO, "parallelo", "R1", "R2")
        assert not isinstance(esito, Refusal)
        dopo, res = esito
        eq = _eq(dopo, "V1", "RL")
        assert eq.value.amount == F(20, 3)
        # L'aspettativa precedente pinnava la forma tautologica: il primo membro
        # portava l'espressione invece dell'identificatore, e l'uguaglianza leggeva
        # «(R1·R2 / (R1 + R2)) = R1·R2 / (R1 + R2)». Ora nomina cio' che definisce.
        assert res.equation.subject == eq.id
        assert str(res.equation) == f"{eq.id} = R1·R2 / (R1 + R2)"

    def test_l_equivalente_ha_identita_nuova_e_lineage_nelle_due_direzioni(self):
        dopo, res = _serie_riuscita()
        nuova = C(_eq(dopo, "V1").id)
        assert nuova not in res.preserve
        # Il nodo assorbito entra fra le origini: l'equivalente esiste perche' i due
        # resistori **e** il nodo comune sono stati consumati. L'aspettativa
        # precedente — solo i due componenti — pinnava una lineage incompleta, e la
        # stessa incompletezza faceva fallire `check_delta` con
        # `sparizione_non_spiegata su node:b`.
        assert res.delta.derived_from(nuova) == (C("R1"), C("R2"), N("b"))
        assert res.delta.what_happened_to(C("R1")).outputs == (nuova,)

    def test_il_circuito_risultante_supera_la_validazione_elettrica(self):
        esito = transform(SERIE, "serie", "R1", "R2")
        assert not isinstance(esito, Refusal)
        assert not isinstance(validate(esito[0]), Refusal)

    def test_un_prodotto_che_non_supera_la_validazione_non_esce_certificato(self):
        """Il criterio non e' una proprieta' dei tre controlli strutturali.

        `R1` e `R2` stanno davvero fra gli stessi due nodi, quindi il parallelo e'
        legittimo e boundary, identita' e massimalita' passano tutti e tre. Fondendole
        resta pero' `a` con un solo terminale — un ramo aperto — e prima di questa
        riga il prodotto usciva con un `Certificate` completo e un circuito che
        `validate` rifiuta.
        """
        prima = _ir(_v("V1", "b", "0", 12), _r("R4", "b", "0", 40),
                    _r("R1", "a", "b", 10), _r("R2", "a", "b", 20),
                    nodes=("0", "a", "b"))
        assert not isinstance(validate(prima), Refusal)     # l'ingresso e' sano
        esito = transform(prima, "parallelo", "R1", "R2")
        assert isinstance(esito, Refusal)
        assert esito.cause == "topology" and esito.subject == "a"

    def test_un_ingresso_gia_rotto_non_diventa_una_colpa_del_passo(self, monkeypatch):
        """Il verso simmetrico: senza di esso `transform` valuta il passo su un
        circuito che nessuno avrebbe potuto risolvere, e la diagnosi esce dalla
        validazione del **prodotto** — cioe' accusa la Trasformazione di un difetto
        che c'era prima di lei.

        Il difetto non si vede confrontando le due diagnosi: su questo circuito
        nominano lo stesso nodo. Si vede da **quando** arriva il Rifiuto — se
        l'ingresso e' gia' rotto, il passo non viene nemmeno valutato.
        """
        from kirchhoff.domain.transform import engine
        rotto = _ir(_r("R1", "a", "b", 10), _r("R2", "b", "0", 20),
                    nodes=("0", "a", "b"))
        atteso = validate(rotto)
        assert isinstance(atteso, Refusal)

        def _mai_valutato(*a, **k):
            raise AssertionError(
                "il passo e' stato valutato su un circuito gia' elettricamente rotto")

        monkeypatch.setattr(engine, "check_transform", _mai_valutato)
        esito = transform(rotto, "serie", "R1", "R2")
        assert isinstance(esito, Refusal)
        assert (esito.cause, esito.subject) == (atteso.cause, atteso.subject)

    def test_il_certificato_elenca_anche_le_due_validazioni(self):
        """E-65: un controllo che ha girato compare, e i due estremi sono distinti."""
        _, res = _serie_riuscita()
        assert "validazione elettrica di Cₖ" in res.certificate.checks
        assert "validazione elettrica di Cₖ₊₁" in res.certificate.checks

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


class TestCioCheCkPiuUnoDeveEssere:
    """`Cₖ₊₁` e' **derivato**, non una copia di `Cₖ` con meno componenti.

    Tre campi non si copiano invariati, e prima di questa storia copiarli produceva
    un `ValueError` dal costruttore dell'IR su circuiti che `validate` promuove —
    cioe' un esito che AD-2 em. non ammette, ne' prodotto ne' Rifiuto.
    """

    CON_RICHIESTE = _ir(
        _v("V1", "a", "0", 12), _r("R1", "a", "b", 10), _r("R2", "b", "0", 20),
        nodes=("0", "a", "b"),
        requests=(Request("q1", "voltage", "R1"), Request("q2", "current", "V1")))

    def test_l_ingresso_con_richieste_e_un_circuito_promosso(self):
        assert not isinstance(validate(self.CON_RICHIESTE), Refusal)

    def test_una_richiesta_sul_componente_consumato_non_fa_esplodere_il_passo(self):
        """E' il flusso che la storia descrive: la riduzione consuma proprio cio' che
        la richiesta nomina."""
        esito = transform(self.CON_RICHIESTE, "serie", "R1", "R2")
        assert not isinstance(esito, Refusal)
        dopo, res = esito
        assert [r.id for r in dopo.requests] == ["q2"]

    def test_la_richiesta_consumata_non_e_persa_ma_derivata(self):
        """Non si perde e non viene ridiretta: la si ritrova dal `Delta`.

        Ridirigerla sull'equivalente sarebbe peggio dell'eccezione che c'era prima —
        la tensione ai capi di `R1` non e' quella ai capi di `R1+R2`, e la domanda
        dell'utente cambierebbe di nascosto.
        """
        _, res = transform(self.CON_RICHIESTE, "serie", "R1", "R2")
        derivazione = res.delta.what_happened_to(C("R1"))
        assert derivazione is not None and derivazione.operation == "serie"

    def test_una_richiesta_sul_superstite_viaggia_col_circuito(self):
        dopo, _ = transform(self.CON_RICHIESTE, "serie", "R1", "R2")
        assert [r.target for r in dopo.requests] == ["V1"]

    def test_la_sorgente_di_ck_piu_uno_e_generated(self):
        """Dice da dove l'IR e' stato *letto*, e questo non e' stato letto: e' stato
        calcolato qui."""
        dopo, _ = _serie_riuscita()
        assert dopo.source_kind == "generated"


class TestSorgenteFotografica:
    """FR-5: da un'immagine ogni componente porta la propria area di provenienza.

    L'equivalente non ne ha una — non compare in nessuna fotografia, perche' non c'e'
    mai stato — e prima di questa storia ogni Trasformazione su un IR fotografico
    moriva nel costruttore dell'IR. La fotografia e' la sorgente primaria del
    prodotto: era il caso piu' importante e il meno coperto.
    """

    AREA = Provenance(F(0), F(0), F(1, 4), F(1, 4))

    @classmethod
    def _foto(cls) -> IR:
        return IR("1.0.0", "dc_resistive", "image", ("0", "a", "b"), (
            Component.of("V1", "voltage_source_dc", ("a", "0"), F(12), "V1",
                         provenance=cls.AREA),
            Component.of("R1", "resistor", ("a", "b"), F(10), "R1", provenance=cls.AREA),
            Component.of("R2", "resistor", ("b", "0"), F(20), "R2", provenance=cls.AREA),
        ), ())

    def test_l_ingresso_fotografico_e_un_circuito_promosso(self):
        assert not isinstance(validate(self._foto()), Refusal)

    def test_una_riduzione_su_una_foto_produce_un_circuito_e_non_un_eccezione(self):
        esito = transform(self._foto(), "serie", "R1", "R2")
        assert not isinstance(esito, Refusal)
        dopo, _ = esito
        assert dopo.source_kind == "generated"
        assert all(c.provenance is None for c in dopo.components)

    def test_la_provenienza_persa_non_toglie_nessuno_da_pk(self):
        """`provenance` non e' fra gli `IDENTITY_ATTRIBUTES`: dice da dove il
        componente e' stato letto, non che cosa e'."""
        _, res = transform(self._foto(), "serie", "R1", "R2")
        assert C("V1") in res.preserve


class TestSerieAttraversoIlRiferimento:
    """Il nodo `0` non si elimina: e' il potenziale rispetto a cui tutto e' definito."""

    ATTRAVERSO_ZERO = _ir(_v("V1", "a", "c", 12), _r("R1", "a", "0", 10),
                          _r("R2", "0", "c", 20), nodes=("0", "a", "c"))

    def test_l_ingresso_e_un_circuito_promosso_e_la_coppia_e_una_serie(self):
        assert not isinstance(validate(self.ATTRAVERSO_ZERO), Refusal)
        tocca = [c.id for c in self.ATTRAVERSO_ZERO.components if "0" in c.terminals]
        assert sorted(tocca) == ["R1", "R2"]          # grado 2: e' una serie vera

    def test_la_diagnosi_nomina_l_operazione_e_la_coppia(self):
        """Prima moriva due strati piu' in basso con «manca il nodo di riferimento»:
        vero, e senza dire ne' quale operazione ne' quali componenti."""
        with pytest.raises(ValueError, match="nodo di riferimento 0"):
            transform(self.ATTRAVERSO_ZERO, "serie", "R1", "R2")


class TestFR43AlMotore:
    """Le applicabili non sono un'etichetta: sono una porta che `transform` attraversa."""

    def test_una_non_applicabile_e_rifiutata_invece_che_improvvisata(self):
        assert "stella_triangolo" in CATALOG and "stella_triangolo" not in SUPPORTED
        with pytest.raises(ValueError, match="non applicabile"):
            transform(SERIE, "stella_triangolo", "R1", "R2")

    def test_non_applicabile_e_non_ancora_scritta_sono_risposte_diverse(self):
        """Le due che il docstring del Catalogo dice di non confondere. Prima erano lo
        stesso `NotImplementedError`, con la diagnosi sbagliata delle due."""
        with pytest.raises(NotImplementedError, match="applicabile ma senza"):
            transform(SERIE, "partitore_di_tensione", "R1", "R2")
        with pytest.raises(ValueError, match="non applicabile"):
            transform(SERIE, "partitore_di_corrente", "R1", "R2")

    def test_il_vocabolario_viene_prima_di_tutto(self):
        with pytest.raises(ValueError, match="non\\s*si estende a runtime"):
            transform(SERIE, "REMOVE_LOAD", "R1", "R2")  # type: ignore[arg-type]

    def test_una_decisione_registrata_apre_la_porta(self):
        """Esibita a ogni chiamata: non c'e' uno stato globale che ricordi l'apertura."""
        decisione = CatalogOpening(
            F(97, 100), F(1, 2), F(9, 10), F(2, 5), "reference-set/dev",
            "proprietario", "2026-08-24", frozenset({"stella_triangolo"}))
        assert "stella_triangolo" in transformations_supported(decisione)
        # La porta si apre: l'esito non e' piu' «non applicabile» ma «non scritta».
        with pytest.raises(NotImplementedError, match="applicabile ma senza"):
            transform(SERIE, "stella_triangolo", "R1", "R2", opening=decisione)
        with pytest.raises(ValueError, match="non applicabile"):
            transform(SERIE, "stella_triangolo", "R1", "R2")

    def test_una_implementata_ma_non_applicabile_non_verrebbe_eseguita(self, monkeypatch):
        """Il recinto era un test sugli insiemi; adesso e' una porta a runtime.

        Con il solo recinto statico, una voce che entrasse nel registro senza essere
        applicabile sarebbe stata eseguita senza che nulla protestasse.
        """
        from kirchhoff.domain.transform import engine
        monkeypatch.setitem(engine._REGISTRO, "stella_triangolo", engine._serie)
        with pytest.raises(ValueError, match="non applicabile"):
            transform(SERIE, "stella_triangolo", "R1", "R2")


class TestIdentitaAttraversoLaMappa:
    """AD-22 em.: `Pₖ` e' l'intersezione **dopo** `node_mapping`."""

    PRIMA = _ir(_v("V1", "a", "0", 12), _r("R1", "a", "b", 10), _r("R2", "b", "0", 20),
                nodes=("0", "a", "b"))
    #: lo stesso circuito, col nodo `a` davvero rinominato in `a2`.
    RINOMINATO = _ir(_v("V1", "a2", "0", 12), _r("R1", "a2", "b", 10),
                     _r("R2", "b", "0", 20), nodes=("0", "a2", "b"))
    MAPPA = (("a", "a2"),)

    def _patch(self, prima: IR, dopo: IR, mappa, **extra) -> LayoutPatch:
        preservate = preserve_set(prima, dopo, operation="serie", node_mapping=mappa)
        campi = dict(preserve=tuple(sorted(preservate)), remove=(), create=(),
                     node_mapping=mappa, reroute_scope=(N("b"),))
        return LayoutPatch(**{**campi, **extra})

    def test_una_rinomina_reale_entra_in_pk_e_viene_colta(self):
        """Prima era invisibile: `node:a` usciva da `Pₖ` per il solo fatto di non
        chiamarsi piu' come prima, e il ciclo d'identita' scorre `Pₖ`."""
        preservate = preserve_set(self.PRIMA, self.RINOMINATO, operation="serie",
                                  node_mapping=self.MAPPA)
        assert N("a") in preservate
        patch = self._patch(self.PRIMA, self.RINOMINATO, self.MAPPA)
        r = check_transform(self.PRIMA, self.RINOMINATO, "serie", patch,
                            Boundary((N("b"),)))
        assert isinstance(r, Refusal)
        assert r.cause == "identity_violation" and r.subject == "a"

    def test_senza_la_mappa_lo_stesso_confronto_non_vede_nulla(self):
        """La prova che il difetto era strutturale e non una svista di soglia."""
        senza = preserve_set(self.PRIMA, self.RINOMINATO, operation="serie")
        assert N("a") not in senza

    def test_un_componente_segue_il_nodo_assorbito_e_resta_preservato(self):
        """`R1 (a,b)` diventa `R1 (a2,b)` **solo** perche' `a` e' stato rinominato:
        non ha cambiato identita', e restringere `Pₖ` qui la restringerebbe proprio
        dove una fusione di nodi la mette alla prova."""
        preservate = preserve_set(self.PRIMA, self.RINOMINATO, operation="serie",
                                  node_mapping=self.MAPPA)
        assert C("R1") in preservate and C("V1") in preservate

    def test_una_mappa_verso_un_nome_inesistente_non_fa_uscire_da_pk(self):
        """L'uscita di sicurezza che restava aperta: mappare un sopravvissuto su un
        nome che `Cₖ₊₁` non ha lo toglieva da `Pₖ`, e un `preserve` che lo omette
        risultava conforme perche' il riferimento si era ristretto con lui."""
        dopo, _ = _serie_riuscita()
        patch = LayoutPatch(preserve=(C("V1"), N("0")), remove=(), create=(),
                            node_mapping=(("a", "zzz"),), reroute_scope=(N("0"),))
        r = check_transform(SERIE, dopo, "serie", patch, Boundary((N("0"),)))
        assert isinstance(r, Refusal)
        assert r.cause == "identity_violation" and r.subject == "a"

    def test_la_mappa_dei_nodi_non_tocca_i_componenti(self):
        """Un componente di id `a` e un nodo di id `a` sono due entita' distinte:
        `EntityRef` le distingue, e la mappa deve rispettare la distinzione.

        La rinomina qui e' **reale** — `z` esiste in `Cₖ₊₁` — di proposito: su una
        rinomina soltanto dichiarata il primo verso del controllo scatterebbe per
        conto proprio e coprirebbe il difetto. Entrambe le letture producono un
        `identity_violation` di soggetto `a`; cambia il **genere**, e con esso quale
        entita' viene accusata.
        """
        prima = _ir(_v("a", "a", "0", 12), _r("R1", "a", "b", 10),
                    _r("R2", "b", "0", 20), nodes=("0", "a", "b"))
        dopo = _ir(_v("a", "z", "0", 12), _r("R1", "z", "b", 10),
                   _r("R2", "b", "0", 20), nodes=("0", "b", "z"))
        mappa = (("a", "z"),)
        preservate = preserve_set(prima, dopo, operation="serie", node_mapping=mappa)
        assert {C("a"), N("a")} <= preservate      # omonimi, e tutti e due in `Pₖ`
        patch = LayoutPatch(preserve=tuple(sorted(preservate)), remove=(), create=(),
                            node_mapping=mappa, reroute_scope=(N("b"),))
        r = check_transform(prima, dopo, "serie", patch, Boundary((N("b"),)))
        assert isinstance(r, Refusal) and r.cause == "identity_violation"
        assert r.subject == "a" and r.subject_kind == "node"


# ---------------------------------------------------------------------------
# P0-A — il Delta emesso deve attraversare il proprio controllore.
#
# Il pacchetto possiede `check_delta` e la produzione non lo eseguiva mai: i sei
# membri di un `TransformResult` potevano raccontare storie incompatibili sulla
# stessa entita' senza che nulla lo impedisse. E-65 — un componente non certifica
# se stesso asserendolo — vale anche quando il verificatore esiste ma non e'
# cablato: un controllore non chiamato e' un controllo che non c'e'.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("circuito, operazione", [
    (SERIE, "serie"),
    (PARALLELO, "parallelo"),
])
def test_il_delta_emesso_supera_il_proprio_controllore(circuito, operazione):
    esito = transform(circuito, operazione, "R1", "R2")
    assert not isinstance(esito, Refusal), esito
    dopo, res = esito
    violazioni = check_delta(res.delta, circuito, dopo, operation=operazione)
    assert violazioni == (), (
        f"il Delta emesso da «{operazione}» viola il proprio controllore: "
        + "; ".join(f"{v.code} su {v.subject}" for v in violazioni))


# ---------------------------------------------------------------------------
# P1 — il vocabolario degli errori ha UNA fonte autoritativa.
#
# `Cause` e `CAUSES` erano scritti due volte e tenuti allineati a mano; questa
# storia ha esteso entrambe le copie nello stesso commit, che e' precisamente il
# gesto che E-62 descrive: un vocabolario scritto due volte prima o poi diverge,
# e diverge nel posto dove nessuno guarda. Per `CATALOG` la riconciliazione e'
# gia' dottrina; qui mancava.
#
# `CAUSES` ora si DERIVA da `Cause`: la divergenza non e' piu' evitata per
# disciplina, e' impossibile per costruzione. Questi test pinnano l'invariante.
# ---------------------------------------------------------------------------


def test_causes_coincide_con_il_literal():
    from typing import get_args
    assert set(get_args(Cause)) == CAUSES


def test_subject_kinds_coincide_con_il_literal():
    from typing import get_args
    assert set(get_args(SubjectKind)) == SUBJECT_KINDS


def test_la_lineage_risponde_anche_per_il_nodo_assorbito():
    """`delta.py` promette che la lineage sia interrogabile per costruzione.

    Era vera per i componenti e muta per il nodo che la fusione inghiotte:
    `what_happened_to(node:b)` rispondeva `None` su un'entita' sparita. Una
    promessa che vale per alcune entita' e non per altre non e' un contratto.
    """
    esito = transform(SERIE, "serie", "R1", "R2")
    assert not isinstance(esito, Refusal), esito
    _, res = esito
    derivazione = res.delta.what_happened_to(N("b"))
    assert derivazione is not None, "il nodo assorbito non ha lineage"
    assert derivazione.operation == "serie"
    assert N("b") in derivazione.inputs


# ---------------------------------------------------------------------------
# P0-B — l'equazione deve nominare l'entita' che definisce.
#
# La forma emessa era `(R1 + R2) = R1 + R2`: il primo membro portava
# l'ESPRESSIONE dell'equivalente invece del suo identificatore, quindi
# l'uguaglianza non legava il simbolo nuovo alla formula che lo definisce e non
# giustificava nulla. Il contratto lo diceva gia': il campo si chiama `subject` e
# rifiutarsi di esistere vuoto porta il messaggio «non si sa cosa definisce».
#
# Un test pinnava la forma difettosa come comportamento atteso. E-xx: un test mai
# visto fallire e' un test possibilmente vacuo — e questo certificava il bug.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("circuito, operazione", [
    (SERIE, "serie"),
    (PARALLELO, "parallelo"),
])
def test_l_equazione_nomina_l_entita_che_definisce(circuito, operazione):
    esito = transform(circuito, operazione, "R1", "R2")
    assert not isinstance(esito, Refusal), esito
    _, res = esito
    prodotta = res.delta.derivations[0].outputs[0]
    assert res.equation.subject == prodotta.id, (
        f"l'equazione definisce «{res.equation.subject}», ma il passo produce "
        f"«{prodotta.id}»: il simbolo nuovo non compare nell'uguaglianza")


@pytest.mark.parametrize("circuito, operazione", [
    (SERIE, "serie"),
    (PARALLELO, "parallelo"),
])
def test_l_equazione_non_e_tautologica(circuito, operazione):
    """Discriminazione negativa: `X = X` non giustifica un passo."""
    esito = transform(circuito, operazione, "R1", "R2")
    assert not isinstance(esito, Refusal), esito
    _, res = esito
    assert res.equation.subject != res.equation.expression, (
        f"equazione tautologica: {res.equation}")


def test_un_delta_che_mente_e_un_guasto_non_un_rifiuto():
    """Discriminazione negativa: la guardia deve mordere, non decorare.

    Si chiama l'assemblatore interno perche' dopo la correzione **non esiste piu'
    una via pubblica** per produrre un Delta incoerente: le due riduzioni ora
    dichiarano correttamente cio' che consumano. Un guard senza un test che lo
    veda scattare e' un guard di cui nessuno sa se funziona — ed e' proprio la
    classe di difetto che questa storia sta chiudendo.

    L'esito e' un'eccezione e non un `Refusal`: la richiesta era soddisfacibile e
    il motore ha prodotto un attestato incoerente con cio' che ha fatto. AD-13
    chiama guasto esattamente questo.
    """
    from kirchhoff.domain.transform.engine import DeltaIncoerente, _prodotto, _senza

    eq = Component.of("R1R2eq", "resistor", ("a", "0"), F(30), "(R1 + R2)")
    dopo = _senza(SERIE, ("R1", "R2"), ("b",), eq)

    with pytest.raises(DeltaIncoerente) as scoppio:
        _prodotto(
            SERIE, dopo, "serie",
            # il nodo assorbito NON e' dichiarato: e' esattamente la forma che il
            # difetto aveva prima della correzione
            consumati=(C("R1"), C("R2")),
            prodotto=C("R1R2eq"),
            rimossi=(C("R1"), C("R2"), N("b")),
            boundary=Boundary((N("a"), N("0"))),
            equazione=Equation("R1R2eq", "R1 + R2"),
        )
    assert "sparizione_non_spiegata" in str(scoppio.value)
    assert "node:b" in str(scoppio.value)
