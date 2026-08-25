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
    check_boundary,
    check_patch,
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
            LayoutPatch((C("R1"),), (), (12,), ())  # type: ignore[arg-type]

    def test_entita_ripetuta_rifiutata(self):
        with pytest.raises(ValueError, match="preserve: entita' ripetuta"):
            LayoutPatch((C("R1"), C("R1")), (), (), ())

    def test_l_ordine_e_canonico_e_non_d_inserimento(self):
        uno = LayoutPatch((C("R2"), C("R1")), (), (), ())
        due = LayoutPatch((C("R1"), C("R2")), (), (), ())
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
        layout_patch=LayoutPatch((N("0"),), (C("R1"),), (C("Req"),), (C("Req"),)),
        equation=Equation("Req", "R1 + R2"),
        certificate=Certificate("serie", CONTROLLI),
    )
    return TransformResult(**{**campi, **sovrascritti})


class TestLeCauseDiAd19:
    """Le cause che AD-19 assegna a `domain/transform/check`, viste sollevare.

    Erano tre. Dalla v2.2 `identity_violation` **resta dichiarata e senza
    produttori**: senza `node_mapping`, `id_{k+1}(x) = id_k(x)` su `Pₖ` e' vero per
    costruzione. La causa non e' stata tolta da `Cause` perche' la tabella vive in
    AD-19, che e' spine: rimuoverne una e' un'altra decisione di proprieta'.
    """

    def test_le_tre_cause_sono_nell_enumerazione_chiusa(self):
        assert {"identity_violation", "preserve_nonmaximal", "empty_boundary"} <= CAUSES

    def test_boundary_assente_produce_empty_boundary(self):
        dopo, _ = _serie_riuscita()
        patch = LayoutPatch(tuple(sorted(preserve_set(SERIE, dopo, operation="serie"))),
                            (), (), (N("a"),))
        r = check_transform(SERIE, dopo, "serie", patch, None)
        assert isinstance(r, Refusal) and r.cause == "empty_boundary"

    def test_preserve_diverso_da_pk_in_difetto(self):
        dopo, _ = _serie_riuscita()
        patch = LayoutPatch((N("a"),), (), (), (N("a"),))
        r = check_transform(SERIE, dopo, "serie", patch, Boundary((N("a"), N("0"))))
        assert isinstance(r, Refusal) and r.cause == "preserve_nonmaximal"
        assert "node:0" in r.diagnosis

    def test_preserve_diverso_da_pk_in_eccesso(self):
        """«Diverso da», non «piu' piccolo di»: la causa copre entrambi i versi."""
        dopo, _ = _serie_riuscita()
        preservate = preserve_set(SERIE, dopo, operation="serie")
        patch = LayoutPatch((*sorted(preservate), C("R1")), (), (), (N("a"),))
        r = check_transform(SERIE, dopo, "serie", patch, Boundary((N("a"), N("0"))))
        assert isinstance(r, Refusal) and r.cause == "preserve_nonmaximal"
        assert "component:R1" in r.diagnosis

    def test_una_sopravvissuta_dichiarata_creata(self):
        """Il verso chiuso il 15 agosto: restringere `Pₖ` per far tornare il riferimento."""
        dopo, _ = _serie_riuscita()
        preservate = preserve_set(SERIE, dopo, operation="serie")
        patch = LayoutPatch(tuple(sorted(preservate)), (), (N("a"),), (N("a"),))
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
        from types import MappingProxyType

        from kirchhoff.domain.transform import engine

        # Si sostituisce il LEGAME, non si muta la mappa: il registro e' chiuso
        # (P1-5) e il test non deve essere la ragione per cui resta apribile.
        monkeypatch.setattr(engine, "_REGISTRO", MappingProxyType(
            {**engine._REGISTRO, "stella_triangolo": engine._serie}))
        with pytest.raises(ValueError, match="non applicabile"):
            transform(SERIE, "stella_triangolo", "R1", "R2")


class TestRinominaNonEPreservazione:
    """AD-22 v2.2: `Pₖ` e' l'intersezione per identificatore, senza mappature.

    Questa classe verificava il verso opposto — che una rinomina, *attraverso*
    `node_mapping`, entrasse in `Pₖ` per potervi essere colta. Il campo e' ritirato
    e il verso si e' invertito: una rinomina non entra affatto, e non deve.

    Il test superstite non e' cambiato di una riga; e' cambiato cio' che dimostra.
    Prima documentava un difetto — «senza la mappa il confronto non vede nulla» —
    ed era la ragione per cui la mappa esisteva. Ora documenta il contratto.
    """

    PRIMA = _ir(_v("V1", "a", "0", 12), _r("R1", "a", "b", 10), _r("R2", "b", "0", 20),
                nodes=("0", "a", "b"))
    #: lo stesso circuito, col nodo `a` rinominato in `a2`.
    RINOMINATO = _ir(_v("V1", "a2", "0", 12), _r("R1", "a2", "b", 10),
                     _r("R2", "b", "0", 20), nodes=("0", "a2", "b"))

    def test_un_nodo_rinominato_non_sopravvive_sotto_nessuno_dei_due_nomi(self):
        """`rinomina != preservazione`: e' una consumata piu' una creata."""
        p = preserve_set(self.PRIMA, self.RINOMINATO, operation="serie")
        assert N("a") not in p
        assert N("a2") not in p

    def test_un_componente_i_cui_terminali_cambiano_non_e_preservato(self):
        """Conseguenza dichiarata del ritiro, registrata invece che scoperta dopo.

        `R1 (a,b)` diventa `R1 (a2,b)` perche' il nodo che tocca e' stato rinominato.
        Sotto la v2 il confronto passava per la mappa e `R1` restava preservata; sotto
        la v2.2 i terminali si confrontano letteralmente, quindi `R1` **non** e'
        preservata: attributi diversi, identita' diversa.

        Nel catalogo corrente lo scenario non si presenta — i componenti che toccano
        un nodo assorbito sono esattamente quelli consumati — e una rinomina di nodo
        non e' un'operazione del contratto. Se una trasformazione futura ne avesse
        bisogno, AD-22 v2.2 dice gia' che serve una nuova decisione architetturale.
        """
        p = preserve_set(self.PRIMA, self.RINOMINATO, operation="serie")
        assert C("R1") not in p
        assert C("V1") not in p

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


# ---------------------------------------------------------------------------
# P0-C — storicizzato. `node_mapping` e' stata ritirata dalla v2.2, e con essa i
# quattro controlli che la sorvegliavano. L'iniettivita' non e' piu' un invariante
# da verificare: e' una proprieta' che nessuno puo' violare, perche' `Pₖ` e' un
# insieme e un identificatore vi compare al piu' una volta.
#
# Il rilievo resta valido come storia: sotto la v2 (AD-22 v2).
#
# L'iniettivita' era promessa dal docstring di `LayoutPatch` e verificata solo
# fra le coppie esplicite: la collisione fra una coppia dichiarata `n2 -> n1` e
# l'identita' implicita `n1 -> n1` non era colta ne' dalla patch ne' da
# `preserve_set`, e `Pₖ` si gonfiava — due entita' di `Cₖ` contate come
# sopravvissute sulla stessa entita' di `Cₖ₊₁`.
#
# Gonfiare `Pₖ` e' il verso opposto di quello che AD-22 v2 chiude, e ha lo stesso
# effetto: il riferimento del kill criterion si sposta sotto la misura.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# AD-22 v2.2 — `node_mapping` e' DIFFERITA. Questi test sono cio' che deve reggere
# **dopo** il ritiro, e sono stati scritti prima di rimuovere il campo: servono a
# dimostrare che togliere lo strato di mappatura non indebolisce il contratto.
#
# Nel contratto corrente la preservazione richiede identita' semantica stabile E
# identificatore semantico stabile. `rinomina != preservazione`: una entita' che
# cambia nome e' una consumata piu' una creata, con lineage nel `Delta`.
# ---------------------------------------------------------------------------


RINOMINATO = _ir(_v("V1", "a", "0", 12), _r("R1", "a", "z", 10), _r("R2", "z", "0", 20),
                 nodes=("0", "a", "z"))


def test_una_rinomina_non_e_una_preservazione():
    """`b` diventa `z`: nessuno dei due nomi sopravvive come preservato.

    Senza strato di mappatura `Pₖ` e' un'intersezione per identificatore: `b` non
    e' in `Cₖ₊₁`, `z` non e' in `Cₖ`, e nessuno dei due entra. E' esattamente cio'
    che il contratto vuole — una rinomina e' una consumata piu' una creata.
    """
    p = preserve_set(SERIE, RINOMINATO, operation="serie")
    assert N("b") not in p, "il nome vecchio non sopravvive"
    assert N("z") not in p, "il nome nuovo non e' una preservazione"


def test_un_preserve_che_rivendica_il_nome_vecchio_e_rifiutato():
    """Il verso che conta: nessuno puo' DICHIARARE preservato cio' che e' rinominato."""
    patch = LayoutPatch(
        preserve=(N("0"), N("a"), N("b")),   # rivendica b, che in Cₖ₊₁ non c'e'
        remove=(), create=(),
        reroute_scope=(N("a"),),
    )
    rifiuto = check_transform(SERIE, RINOMINATO, "serie", patch, Boundary((N("a"),)))
    assert rifiuto is not None
    assert rifiuto.cause == "preserve_nonmaximal"


def test_due_entita_non_possono_collassare_in_una_sola_preservata():
    """Many-to-one non e' piu' esprimibile: `Pₖ` e' un'intersezione di insiemi.

    Con lo strato di mappatura, `b -> a` faceva contare `a` e `b` entrambi come
    sopravvissuti sullo stesso posto di `Cₖ₊₁` e gonfiava `Pₖ`. Senza, la
    collisione non ha un canale attraverso cui esprimersi: ogni identificatore
    compare al piu' una volta in un insieme.
    """
    p = preserve_set(SERIE, SERIE, operation="serie")
    identificatori = [e.id for e in p if e.kind == "node"]
    assert len(identificatori) == len(set(identificatori))


# ---------------------------------------------------------------------------
# P1-1 — `create` e `remove` contro i due circuiti.
#
# L'invariante generale, e la ragione per cui viene prima del boundary:
#
#     cio' che appare e sparisce nel CircuitIR
#       <-> cio' che dice il Delta
#       <-> cio' che dice la LayoutPatch
#
# Il Delta ha gia' il suo controllore (P0-A). La patch no: `create` e `remove`
# non erano confrontati con nulla. Misurato: una patch con
# `create=(component:MaiEsistita,)` — oppure `remove` — attraversava
# `check_transform` pulita, e un renderer che la seguisse riceverebbe istruzioni
# su entita' che nessuno dei due circuiti possiede.
# ---------------------------------------------------------------------------


def _patch_della_serie(**override):
    """La patch che la serie produce davvero, con un campo sostituito."""
    dopo, res = _serie_riuscita()
    campi = dict(preserve=res.layout_patch.preserve,
                 remove=res.layout_patch.remove,
                 create=res.layout_patch.create,
                 reroute_scope=res.layout_patch.reroute_scope)
    return dopo, LayoutPatch(**{**campi, **override})


@pytest.mark.parametrize("campo", ["create", "remove"])
def test_una_patch_che_nomina_un_entita_mai_esistita_e_un_guasto(campo):
    from kirchhoff.domain.transform.engine import PatchIncoerente, _prodotto
    dopo, patch = _patch_della_serie(**{campo: (C("MaiEsistita"),)})
    violazioni = check_patch(patch, SERIE, dopo)
    assert violazioni, (
        f"una patch con {campo}=(component:MaiEsistita,) non e' stata contestata")
    assert any("MaiEsistita" in v.subject for v in violazioni)


def test_una_patch_che_tace_su_cio_che_e_sparito_e_contestata():
    """Il verso omissivo: `remove` incompleto e' bugiardo quanto `remove` gonfiato."""
    dopo, patch = _patch_della_serie(remove=(C("R1"),))   # tace su R2 e node:b
    violazioni = check_patch(patch, SERIE, dopo)
    soggetti = {v.subject for v in violazioni}
    assert "component:R2" in soggetti and "node:b" in soggetti


def test_la_patch_che_le_riduzioni_producono_regge_il_controllore():
    """Discriminazione positiva: il controllore non deve accusare il caso sano."""
    for circuito, operazione in [(SERIE, "serie"), (PARALLELO, "parallelo")]:
        dopo, res = transform(circuito, operazione, "R1", "R2")
        assert check_patch(res.layout_patch, circuito, dopo) == ()


def test_una_patch_che_mente_e_un_guasto_non_un_rifiuto():
    """Discriminazione negativa attraverso il motore, non solo sul controllore.

    Speculare a `test_un_delta_che_mente_e_un_guasto_non_un_rifiuto`. Dopo la
    correzione non esiste una via pubblica per produrre una patch incoerente: le
    due riduzioni dichiarano correttamente cio' che tolgono e cio' che creano.
    Si chiama quindi l'assemblatore interno, con `rimossi` che nomina un'entita'
    che nessuno dei due circuiti possiede.
    """
    from kirchhoff.domain.transform.engine import PatchIncoerente, _prodotto, _senza

    eq = Component.of("R1R2eq", "resistor", ("a", "0"), F(30), "(R1 + R2)")
    dopo = _senza(SERIE, ("R1", "R2"), ("b",), eq)

    with pytest.raises(PatchIncoerente) as scoppio:
        _prodotto(
            SERIE, dopo, "serie",
            consumati=(C("R1"), C("R2"), N("b")),
            prodotto=C("R1R2eq"),
            # dichiara rimossa un'entita' mai esistita, e tace su R2 e node:b
            rimossi=(C("MaiEsistita"),),
            boundary=Boundary((N("a"), N("0"))),
            equazione=Equation("R1R2eq", "R1 + R2"),
        )
    messaggio = str(scoppio.value)
    assert "remove_non_sparita" in messaggio and "MaiEsistita" in messaggio
    assert "sparita_non_dichiarata" in messaggio


# ---------------------------------------------------------------------------
# P1-2 — il `Boundary` verificato nel CONTENUTO.
#
# `∂Tₖ` dice «dove guardare per sapere che la trasformazione e' locale». Era
# verificato solo come vuoto/non vuoto: `Boundary((N("fantasma"),))` — entita'
# inesistente in entrambi i circuiti — attraversava `check_transform` pulito.
#
# Due condizioni necessarie, misurate vere su entrambe le riduzioni del catalogo
# prima di essere imposte:
#   1. ogni entita' del boundary sopravvive — sta in `Pₖ`. Cio' che non sopravvive
#      non e' un punto di contatto col resto della rete: e' dentro il sottografo.
#   2. ogni entita' del boundary e' adiacente al cambiamento — e' terminale di
#      qualcosa che e' stato tolto o creato. Un nodo lontano che sopravvive non
#      confina con niente di trasformato.
# ---------------------------------------------------------------------------


#: serie di R1,R2 dentro una rete piu' grande: `0` sopravvive e NON confina col passo.
CATENA = _ir(_v("V1", "a", "0", 12), _r("R1", "a", "b", 10),
             _r("R2", "b", "c", 20), _r("R3", "c", "0", 30),
             nodes=("0", "a", "b", "c"))


def test_un_boundary_fantasma_e_contestato():
    dopo, res = transform(CATENA, "serie", "R1", "R2")
    violazioni = check_boundary(Boundary((N("fantasma"),)), res.layout_patch,
                                CATENA, dopo)
    assert violazioni, "un boundary su un'entita' inesistente non e' stato contestato"
    assert any(v.code == "fuori_da_pk" for v in violazioni)


def test_un_boundary_lontano_dal_cambiamento_e_contestato():
    """`node:0` sopravvive, ma tocca V1 e R3: non confina col passo."""
    dopo, res = transform(CATENA, "serie", "R1", "R2")
    violazioni = check_boundary(Boundary((N("0"),)), res.layout_patch, CATENA, dopo)
    assert any(v.code == "non_adiacente" for v in violazioni), violazioni


def test_il_boundary_che_le_riduzioni_producono_regge():
    """Discriminazione positiva: il controllore non accusa il caso sano."""
    for circuito, operazione in [(SERIE, "serie"), (PARALLELO, "parallelo"),
                                 (CATENA, "serie")]:
        dopo, res = transform(circuito, operazione, "R1", "R2")
        assert check_boundary(res.boundary, res.layout_patch, circuito, dopo) == ()


def test_un_boundary_che_mente_e_un_guasto_non_un_rifiuto():
    """Terza discriminazione attraverso il motore, sorella delle altre due.

    `node:0` sopravvive alla serie di `R1,R2` dentro `CATENA`, ma tocca `V1` e
    `R3`: non confina con niente di trasformato. Dichiararlo allargherebbe la zona
    che il renderer annota senza che nulla lo giustifichi.
    """
    from kirchhoff.domain.transform.engine import (
        AttestazioneIncoerente, BoundaryIncoerente, _prodotto, _senza,
    )

    eq = Component.of("R1R2eq", "resistor", ("a", "c"), F(30), "(R1 + R2)")
    dopo = _senza(CATENA, ("R1", "R2"), ("b",), eq)

    with pytest.raises(BoundaryIncoerente) as scoppio:
        _prodotto(
            CATENA, dopo, "serie",
            consumati=(C("R1"), C("R2"), N("b")),
            prodotto=C("R1R2eq"),
            rimossi=(C("R1"), C("R2"), N("b")),
            boundary=Boundary((N("0"),)),      # sopravvive, ma non confina
            equazione=Equation("R1R2eq", "R1 + R2"),
        )
    assert "non_adiacente" in str(scoppio.value)
    # un solo invariante, tre canali: le tre eccezioni condividono la base
    assert isinstance(scoppio.value, AttestazioneIncoerente)


# ---------------------------------------------------------------------------
# P1-3 — gli argomenti entrano dalle porte tipizzate.
#
# Il contratto di `transform` documenta con cura tre porte — `ValueError` per cio'
# che non si potra' fare, `NotImplementedError` per cio' che non si e' ancora
# fatto, `Refusal` per il dominio — e il primo errore che un chiamante reale
# commette le attraversava tutte:
#
#     transform(SERIE, "serie", "R1", "RX")  -> KeyError('RX')
#     transform(SERIE, "serie", "R1")        -> TypeError: _serie() missing 1 ...
#
# Un quarto tipo, senza operazione ne' diagnosi, e nessun test lo copriva. Il nome
# della funzione privata finiva nel messaggio: una fuga di implementazione che
# racconta al chiamante come e' fatto dentro invece di che cosa ha sbagliato.
# ---------------------------------------------------------------------------


def test_un_identificatore_inesistente_passa_dalla_porta_tipizzata():
    with pytest.raises(ValueError) as scoppio:
        transform(SERIE, "serie", "R1", "RX")
    messaggio = str(scoppio.value)
    assert "RX" in messaggio, "la diagnosi non nomina l'argomento sbagliato"
    assert "serie" in messaggio, "la diagnosi non nomina l'operazione"
    assert "_serie" not in messaggio, "il nome della funzione privata non deve uscire"


@pytest.mark.parametrize("argomenti", [("R1",), ("R1", "R2", "R3"), ()])
def test_un_arita_sbagliata_passa_dalla_porta_tipizzata(argomenti):
    with pytest.raises(ValueError) as scoppio:
        transform(SERIE, "serie", *argomenti)
    messaggio = str(scoppio.value)
    assert "serie" in messaggio
    assert "_serie" not in messaggio, "il nome della funzione privata non deve uscire"


def test_gli_argomenti_giusti_non_sono_disturbati():
    """Discriminazione positiva: la porta nuova non deve accusare il caso sano."""
    esito = transform(SERIE, "serie", "R1", "R2")
    assert not isinstance(esito, Refusal)


# ---------------------------------------------------------------------------
# P1-4 — il genere del soggetto non deve mentire.
#
# `empty_boundary` e il primo ramo di `preserve_nonmaximal` costruivano
# `Refusal(causa, operation, "request", ...)`: soggetto «serie», genere `request`.
# Nessuna richiesta chiamata «serie» esiste nel circuito.
#
# Non e' cosmesi. FR-4 e K-3 vogliono la diagnosi riusabile come Domanda mirata
# **sull'elemento coinvolto**: chi risale per `subject_kind` per costruirla trova
# un genere che mente, e cerchera' fra le richieste un'entita' che non c'e'. Il
# ripiego — nessun `SubjectKind` copriva «operazione» — non era dichiarato da
# nessuna parte, quindi era indistinguibile da una svista.
# ---------------------------------------------------------------------------


def _refusal_empty_boundary():
    dopo, res = _serie_riuscita()
    return check_transform(SERIE, dopo, "serie", res.layout_patch, None)


def _refusal_preserve_nonmaximal():
    dopo, res = _serie_riuscita()
    guasta = LayoutPatch(preserve=(), remove=res.layout_patch.remove,
                         create=res.layout_patch.create,
                         reroute_scope=res.layout_patch.reroute_scope)
    return check_transform(SERIE, dopo, "serie", guasta, res.boundary)


@pytest.mark.parametrize("costruisci", [
    _refusal_empty_boundary,
    _refusal_preserve_nonmaximal,
])
def test_un_rifiuto_che_nomina_l_operazione_ne_dichiara_il_genere(costruisci):
    r = costruisci()
    assert isinstance(r, Refusal)
    assert r.subject == "serie"
    assert r.subject_kind == "operation", (
        f"soggetto «{r.subject}» dichiarato di genere «{r.subject_kind}»: "
        "nessuna richiesta con quel nome esiste nel circuito")


# **Osservazione, non correzione.** `domain/validate` costruisce
# `Refusal("unsolvable", r.target, "request", ...)`: il soggetto e' il TARGET della
# richiesta — un componente che non esiste — mentre il genere dice `request`. E' la
# stessa imprecisione dei due rifiuti corretti qui sopra, in un terzo posto che
# nessuno dei quattordici rilievi nomina. Non toccata: allargare la Story mentre la
# si ripara e' il modo di renderla non verificabile.


# ---------------------------------------------------------------------------
# P1-5 — il registro e' chiuso anche a runtime, non solo a parole.
#
# Il docstring del modulo dichiara «registro chiuso caricato all'avvio: non espone
# alcuna funzione per aggiungervi una voce a runtime». Vero, e insufficiente: un
# `dict` non ha bisogno che gliela si esponga. `_REGISTRO["serie"] = altra` sostituiva
# l'implementazione della serie senza attraversare nessuna delle quattro porte.
#
# `MUTABLE_ATTRIBUTES` era gia' blindato con `MappingProxyType` nello stesso
# pacchetto: il registro che decide QUALE CODICE viene eseguito no. Stessa classe di
# difetto, chiusa in un modulo e lasciata aperta in quello accanto.
# ---------------------------------------------------------------------------


def test_il_registro_non_si_puo_riscrivere_a_runtime():
    from kirchhoff.domain.transform import engine
    with pytest.raises(TypeError):
        engine._REGISTRO["serie"] = engine._parallelo


def test_il_registro_non_accetta_voci_nuove_a_runtime():
    from kirchhoff.domain.transform import engine
    with pytest.raises(TypeError):
        engine._REGISTRO["stella_triangolo"] = engine._serie


# ---------------------------------------------------------------------------
# HIGH-1 — un cambiamento di attributi a identificatore stabile.
#
# Il caso fondativo dell'istruttoria R2-A, quello che AD-22 v2.1 cita per
# introdurre il discriminante: `R1 (a,b) 10Ω` e `R2 (a,b) 20Ω` fondono in una
# equivalente battezzata `R1 (a,b) 6⅔Ω`. `R1` esce da `Pₖ` — corretto — ma per
# `check_patch` non e' ne' apparsa ne' sparita, perche' quei due insiemi erano
# calcolati per SOLO IDENTIFICATORE.
#
# AD-22 v2.1 lo dice gia': «Un'entita' che fallisce la seconda condizione non e'
# preservata: e' una rimozione piu' una creazione, e come tale deve comparire nel
# Delta». I controllori misuravano «appare e sparisce» per id e `Pₖ` per
# attributi: la fessura fra le due nozioni e' esattamente l'entita' mutata in luogo.
# ---------------------------------------------------------------------------


#: `Cₖ`: R1 e R2 in parallelo fra gli stessi nodi, piu' un carico che tiene il grado.
R2A_PRIMA = _ir(_v("V1", "a", "0", 12), _r("RL", "a", "0", 100),
                _r("R1", "a", "0", 10), _r("R2", "a", "0", 20), nodes=("0", "a"))
#: `Cₖ₊₁`: l'equivalente riusa il nome `R1`. Tipo e terminali coincidono, cambia il valore.
R2A_DOPO = _ir(_v("V1", "a", "0", 12), _r("RL", "a", "0", 100),
               _r("R1", "a", "0", F(20, 3)), nodes=("0", "a"))


def test_una_mutata_in_luogo_e_sparita_e_apparsa():
    """`R1` cambia valore a nome fermo: per AD-22 v2.1 e' rimozione piu' creazione."""
    p = preserve_set(R2A_PRIMA, R2A_DOPO, operation="parallelo")
    assert C("R1") not in p, "il discriminante v2.1 deve tenerla fuori da Pₖ"

    patch_verace = LayoutPatch(preserve=tuple(sorted(p)), remove=(C("R1"), C("R2")),
                               create=(C("R1"),), reroute_scope=(N("a"),))
    assert check_patch(patch_verace, R2A_PRIMA, R2A_DOPO) == (), (
        "la patch che dice la verita' della dottrina viene rifiutata")


def test_una_patch_che_tace_su_una_mutata_in_luogo_e_contestata():
    """Il verso che conta: il silenzio non deve passare."""
    p = preserve_set(R2A_PRIMA, R2A_DOPO, operation="parallelo")
    muta = LayoutPatch(preserve=tuple(sorted(p)), remove=(C("R2"),), create=(),
                       reroute_scope=(N("a"),))
    violazioni = check_patch(muta, R2A_PRIMA, R2A_DOPO)
    soggetti = {v.subject for v in violazioni}
    assert "component:R1" in soggetti, (
        "una patch che tace su un componente il cui valore e' cambiato "
        f"non e' stata contestata: {violazioni}")


def test_un_delta_che_tace_su_una_mutata_in_luogo_e_contestato():
    """«e come tale deve comparire nel Delta» — AD-22 v2.1, non sostenuto da nulla."""
    from kirchhoff.domain.transform import Delta, StructuralDerivation
    muto = Delta((StructuralDerivation("parallelo", (C("R2"),), (C("R1"),)),))
    violazioni = check_delta(muto, R2A_PRIMA, R2A_DOPO, operation="parallelo")
    assert any("R1" in v.subject for v in violazioni), (
        f"il Delta non rende conto di R1 e nessuno protesta: {violazioni}")


# ---------------------------------------------------------------------------
# HIGH-2 — il Certificate attesta un controllo che nessuno esegue.
# ---------------------------------------------------------------------------


def test_il_certificato_non_attesta_controlli_rimossi():
    """`identita'` e' stata rimossa da questo stesso ramo. Un attestato che la
    elenca fra i controlli ESEGUITI e' falso, e il docstring di `Certificate`
    fissa lo standard: «un controllo che non ha girato non compare» (E-65).
    """
    assert "identita'" not in CONTROLLI, (
        "CONTROLLI elenca «identita'», ma nessuna riga del pacchetto la verifica: "
        "i controlli d'identita' sono usciti con node_mapping (AD-22 v2.2)")


# ---------------------------------------------------------------------------
# Ri-revisione — due rilievi, uno dei quali introdotto dalla correzione precedente.
# ---------------------------------------------------------------------------


def test_una_comparsa_non_spiegata_produce_una_sola_violazione():
    """La chiusura del vecchio HIGH aveva aggiunto un ciclo accanto a uno esistente.

    `preservate ⊆ prima` per costruzione, quindi `dopo - prima ⊆ dopo - preservate`:
    il ciclo vecchio non poteva mai scattare da solo e, quando scattava, duplicava.
    Due voci di vocabolario per lo stesso difetto sono il gesto E-62 che il ramo
    dichiara di chiudere altrove.
    """
    from kirchhoff.domain.transform import Delta, StructuralDerivation
    dopo, _ = _serie_riuscita()
    muto = Delta((StructuralDerivation("serie", (C("R1"), C("R2"), N("b")), (C("V1"),)),))
    v = check_delta(muto, SERIE, dopo, operation="serie")
    su_eq = [x for x in v if "R1R2eq" in x.subject]
    assert len(su_eq) == 1, f"stesso difetto contestato {len(su_eq)} volte: {su_eq}"


def test_un_risultato_con_patch_vuota_non_e_costruibile():
    """AD-22: «Ogni campo e' non-vuoto o il prodotto non e' costruibile»."""
    dopo, res = _serie_riuscita()
    with pytest.raises(ValueError, match="layout_patch"):
        TransformResult(
            preserve=res.preserve, delta=res.delta, boundary=res.boundary,
            layout_patch=LayoutPatch((), (), (), ()),
            equation=res.equation, certificate=res.certificate)


def test_due_dichiarazioni_di_pk_nello_stesso_prodotto_non_possono_divergere():
    """`preserve` e `layout_patch.preserve` sono la stessa cosa scritta due volte."""
    dopo, res = _serie_riuscita()
    with pytest.raises(ValueError, match="preserve"):
        TransformResult(
            preserve=frozenset({N("0")}), delta=res.delta, boundary=res.boundary,
            layout_patch=res.layout_patch,
            equation=res.equation, certificate=res.certificate)


def test_il_certificato_e_il_delta_non_possono_nominare_operazioni_diverse():
    dopo, res = _serie_riuscita()
    with pytest.raises(ValueError, match="operazione"):
        TransformResult(
            preserve=res.preserve, delta=res.delta, boundary=res.boundary,
            layout_patch=res.layout_patch, equation=res.equation,
            certificate=Certificate("parallelo", CONTROLLI))


# ---------------------------------------------------------------------------
# Terza tornata — la coerenza interna del prodotto, tutte le coppie di canali.
#
# La chiusura precedente confrontava `preserve` con `layout_patch.preserve` e
# l'operazione del `Certificate` con quella del `Delta`, e si fermava li'. Il
# revisore ha costruito quattro risultati che passavano puliti, e il suo argomento
# e' il mio: «cio' che sparisce» e' scritto due volte — `delta.consumed` e
# `patch.remove` — e non lo confrontava nessuno.
#
# Gli invarianti mancanti sono tutti verificabili **senza i circuiti**, cioe' al
# livello a cui la difesa e' stata messa.
# ---------------------------------------------------------------------------


def _risultato(**override):
    dopo, res = _serie_riuscita()
    campi = dict(preserve=res.preserve, delta=res.delta, boundary=res.boundary,
                 layout_patch=res.layout_patch, equation=res.equation,
                 certificate=res.certificate)
    return TransformResult(**{**campi, **override})


def test_una_preservata_non_puo_essere_anche_consumata_nel_prodotto():
    """(a) due canali che affermano l'opposto sulla stessa entita'."""
    from kirchhoff.domain.transform import Delta, StructuralDerivation
    _, res = _serie_riuscita()
    with pytest.raises(ValueError, match="consuma"):
        _risultato(delta=Delta((StructuralDerivation(
            "serie", (C("V1"), C("R1"), C("R2"), N("b")), (C(_eq_id(res)),)),)))


def test_cio_che_sparisce_e_scritto_una_volta_sola():
    """(b) il Delta tace su R2, la patch no."""
    from kirchhoff.domain.transform import Delta, StructuralDerivation
    _, res = _serie_riuscita()
    with pytest.raises(ValueError, match="consumed.*remove|remove.*consumed"):
        _risultato(delta=Delta((StructuralDerivation(
            "serie", (C("R1"), N("b")), (C(_eq_id(res)),)),)))


def test_il_boundary_del_prodotto_sta_dentro_preserve():
    """(c) un boundary che nomina cio' che il prodotto non conserva."""
    with pytest.raises(ValueError, match="boundary"):
        _risultato(boundary=Boundary((N("mai_esistito"),)))


def test_l_equazione_definisce_qualcosa_che_il_passo_produce():
    """(d) l'equazione definisce un simbolo che nessuna derivazione produce."""
    with pytest.raises(ValueError, match="equazione|equation"):
        _risultato(equation=Equation("Zeq_inventata", "R1 + R2"))


def test_cio_che_nasce_e_scritto_una_volta_sola():
    """Il verso simmetrico di (b): `produced - preserve` deve essere `create`."""
    _, res = _serie_riuscita()
    patch = LayoutPatch(preserve=res.layout_patch.preserve,
                        remove=res.layout_patch.remove,
                        create=(C("AltroNome"),),
                        reroute_scope=res.layout_patch.reroute_scope)
    with pytest.raises(ValueError, match="produce.*crea|crea.*produce"):
        _risultato(layout_patch=patch)


def _eq_id(res):
    return res.delta.derivations[0].outputs[0].id


# ---------------------------------------------------------------------------
# Quarta tornata — `reroute_scope`, il quarto canale che nessuno leggeva.
#
# FR-38 lo usa come limite normativo del renderer: «il numero di elementi con
# coordinate cambiate e' limitato allo `reroute_scope` dichiarato». Un renderer che
# lo rispetta riceveva istruzioni su entita' che nessuno dei due circuiti possiede
# — parola per parola l'argomento con cui e' nato `check_patch`, un campo piu' in la'.
# ---------------------------------------------------------------------------


def test_un_reroute_scope_fantasma_e_contestato():
    dopo, res = _serie_riuscita()
    patch = LayoutPatch(preserve=res.layout_patch.preserve,
                        remove=res.layout_patch.remove,
                        create=res.layout_patch.create,
                        reroute_scope=(C("MaiEsistita"), N("nodo_fantasma")))
    violazioni = check_patch(patch, SERIE, dopo, operation="serie")
    soggetti = {v.subject for v in violazioni}
    assert "component:MaiEsistita" in soggetti and "node:nodo_fantasma" in soggetti, violazioni


def test_un_reroute_scope_vuoto_e_contestato():
    """Un passo che non libera nessuna instradatura non ha nulla da ridisegnare."""
    dopo, res = _serie_riuscita()
    patch = LayoutPatch(preserve=res.layout_patch.preserve,
                        remove=res.layout_patch.remove,
                        create=res.layout_patch.create,
                        reroute_scope=())
    violazioni = check_patch(patch, SERIE, dopo, operation="serie")
    assert any(v.code == "reroute_scope_vuoto" for v in violazioni), violazioni


def test_il_reroute_scope_che_le_riduzioni_producono_regge():
    for circuito, operazione in [(SERIE, "serie"), (PARALLELO, "parallelo")]:
        dopo, res = transform(circuito, operazione, "R1", "R2")
        assert check_patch(res.layout_patch, circuito, dopo, operation=operazione) == ()


# ---------------------------------------------------------------------------
# Decisione owner del 25/08/2026 — uscita B.
#
# `CONTROLLI` smette di attestare la massimalita' di `preserve` sul percorso
# interno di `transform()`. Il motore riempie `patch.preserve` con
# `preserve_set(prima, dopo, op)` e `check_transform` la riconfronta con
# `preserve_set(before, after, op)`: funzione pura, stessi argomenti, quindi
# `f(x) != f(x)` non e' mai vero. La non-massimalita' e' **impossibile per
# costruzione**, non verificata.
#
# `check_transform` conserva la capacita' di verificarla quando riceve un prodotto
# dichiarativo esterno. E' il `Certificate` che smette di affermare di aver
# verificato indipendentemente cio' che il motore ha costruito da `Pₖ`.
#
# Coerente con E-65 e con la scelta gia' fatta per il controllo d'identita'.
# ---------------------------------------------------------------------------


def test_il_certificato_non_attesta_la_massimalita_sul_percorso_interno():
    assert "massimalita' di preserve" not in CONTROLLI, (
        "il motore costruisce patch.preserve da Pₖ e check_transform lo riconfronta "
        "con lo stesso Pₖ: riferimento e misurato sono la stessa variabile, quindi "
        "il Certificate attesterebbe una verifica indipendente che non e' avvenuta")


def test_check_transform_sa_ancora_rifiutare_un_preserve_non_massimale():
    """La capacita' resta: e' l'attestazione che se ne va, non il controllo.

    Il giorno in cui esistera' un produttore che DICHIARA `preserve` invece di
    farselo derivare, questa porta lo verifichera'. Oggi nessuno la attraversa dal
    motore, ed e' precisamente per questo che il `Certificate` tace.
    """
    dopo, res = _serie_riuscita()
    guasta = LayoutPatch(preserve=(N("0"),), remove=res.layout_patch.remove,
                         create=res.layout_patch.create,
                         reroute_scope=res.layout_patch.reroute_scope)
    r = check_transform(SERIE, dopo, "serie", guasta, res.boundary)
    assert isinstance(r, Refusal) and r.cause == "preserve_nonmaximal"


# ---------------------------------------------------------------------------
# Quinta tornata — il discriminante contraddiceva la simmetria dei bipoli.
#
# `ir/canonical.py` dichiara `resistor`, `capacitor`, `inductor` in `SYMMETRIC`:
# «nessuna di queste differenze dice qualcosa del circuito». L'ordine dei terminali
# di un GENERATORE invece e' la polarita', e riordinarlo produrrebbe un circuito
# diverso che si dichiara uguale.
#
# `preserve_set` confrontava `terminals` per uguaglianza sintattica di tupla.
# Misurato: due IR che `canonicalize` dichiara IDENTICI davano `Pₖ` diversi, e un
# passo che non tocca nulla riceveva quattro violazioni. Falsa accusa — «il difetto
# peggiore di questo prodotto» — sulla superficie che la decisione owner conserva
# proprio per il produttore dichiarativo esterno.
# ---------------------------------------------------------------------------


def test_un_bipolo_riorientato_resta_preservato():
    from kirchhoff.domain.ir import canonicalize
    prima = _ir(_v("V1", "a", "0", 12), _r("R1", "a", "0", 10), nodes=("0", "a"))
    dopo = canonicalize(prima)
    assert canonicalize(prima) == canonicalize(dopo), "fixture: non sono lo stesso circuito"
    p = preserve_set(prima, dopo)
    assert C("R1") in p, (
        "un resistore riorientato e' lo stesso resistore: `SYMMETRIC` lo dice, "
        "e `Pₖ` non puo' dipendere da una proprieta' che il dominio dichiara "
        "non semantica")


def test_un_passo_che_non_tocca_nulla_non_e_accusato():
    from kirchhoff.domain.ir import canonicalize
    from kirchhoff.domain.transform import Delta
    prima = _ir(_v("V1", "a", "0", 12), _r("R1", "a", "0", 10), nodes=("0", "a"))
    dopo = canonicalize(prima)
    assert check_delta(Delta(()), prima, dopo) == ()


def test_la_polarita_di_un_generatore_non_e_simmetrica():
    """Il verso opposto: riordinare un generatore NON e' lo stesso circuito.

    Se la correzione fosse «confronta i terminali come insiemi», questo test
    diventerebbe rosso — ed e' precisamente l'errore silenzioso che
    `canonical.py` esiste per prevenire.
    """
    prima = _ir(_v("V1", "a", "0", 12), _r("R1", "a", "0", 10), nodes=("0", "a"))
    invertito = _ir(_v("V1", "0", "a", 12), _r("R1", "a", "0", 10), nodes=("0", "a"))
    assert C("V1") not in preserve_set(prima, invertito)
