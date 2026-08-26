"""Contratto di `Delta`. Ogni invariante ha un test che l'ha visto sollevare."""

from __future__ import annotations

from fractions import Fraction

import pytest

from kirchhoff.domain.ir import IR, Component
from kirchhoff.domain.transform import (
    CATALOG, FORME, PRIMITIVES, Delta, DeltaViolation, EntityRef, Forma,
    StructuralDerivation, StructuralPrimitive, check_delta, entities_of, preserve_set,
)
from kirchhoff.domain.transform.delta import ENTITY_KINDS
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

    def test_i_due_vocabolari_non_condividono_alcun_nome(self):
        """Story 1.2 — «distinto dal catalogo pedagogico», come proprieta' verificata.

        Un nome in entrambi sarebbe accettato sia da `StructuralDerivation` sia da
        `Certificate`, e i due livelli tornerebbero indistinguibili senza che nulla
        protesti: ogni guardia, presa da sola, resterebbe soddisfatta.
        """
        assert CATALOG & PRIMITIVES == frozenset()

    @pytest.mark.parametrize("estranea", [
        # il nome parlato di un passo pedagogico: fuori perche' e' il livello sbagliato
        "COLLAPSE_SERIES",
        # la soppressione di un generatore: fuori per decisione, non per omissione
        "ZERO_VOLTAGE_SOURCE",
        # un nome che non nomina nulla
        "riscrittura_inventata",
    ])
    def test_una_riscrittura_fuori_vocabolario_e_rifiutata(self, estranea):
        """AC1 — «un test che rifiuta ogni operazione fuori insieme».

        `REMOVE_LOAD` non e' un buon esemplare qui e sta altrove: il vocabolario
        **copre** quel concetto, sotto il nome `rimozione_di_componente`, e usarlo per
        illustrare «fuori insieme» confonde il nome col concetto. La distinzione ha un
        test suo, `test_remove_load_e_coperto_sotto_un_altro_nome`.
        """
        with pytest.raises(ValueError, match="fuori dal vocabolario strutturale"):
            StructuralDerivation(estranea, (C("RL"),), ())  # type: ignore[arg-type]

    @pytest.mark.parametrize("passo", sorted(CATALOG))
    def test_nessun_passo_pedagogico_e_una_riscrittura(self, passo):
        """Il difetto che la Story chiude: `operation` puntava a QUESTI nomi.

        Non basta che i due insiemi siano disgiunti — quello e' il test sopra. Qui si
        chiede che la derivazione **rifiuti** ciascuno dei sedici, uno per uno: e' il
        livello sbagliato, e il livello sbagliato dev'essere irrappresentabile.
        """
        with pytest.raises(ValueError, match="fuori dal vocabolario strutturale"):
            StructuralDerivation(passo, (C("RL"),), ())  # type: ignore[arg-type]


class TestIlVocabolarioEScrittoUnaVoltaSola:
    """E-62 sul modulo che cita E-62. `refusal.CAUSES` e' il precedente riusato."""

    def test_primitives_coincide_col_literal(self):
        from typing import get_args
        assert set(get_args(StructuralPrimitive)) == PRIMITIVES

    def test_remove_load_e_coperto_sotto_un_altro_nome(self):
        """Il sotto-passo che la Story cita esiste: si chiama `rimozione_di_componente`.

        Il nome parlato non e' una riscrittura — nomina il carico, cioe' un ruolo, non
        una modifica del grafo — ma il concetto e' nel vocabolario, e questo test
        distingue le due affermazioni invece di confonderle.
        """
        with pytest.raises(ValueError, match="fuori dal vocabolario strutturale"):
            StructuralDerivation("REMOVE_LOAD", (C("RL"),), ())  # type: ignore[arg-type]
        assert FORME["rimozione_di_componente"] == Forma("component", 1, 0)
        assert StructuralDerivation("rimozione_di_componente", (C("RL"),), ())

    def test_la_soppressione_di_un_generatore_non_e_nel_vocabolario(self):
        """L'altro sotto-passo citato dalla Story, e la decisione che lo tiene fuori.

        `ZERO_VOLTAGE_SOURCE` **non** ha un corrispondente qui, e l'assenza e'
        deliberata: lo spine lascia aperto se disattivare un generatore sia «stessa
        entita', stato cambiato» oppure una sostituzione strutturale, e la questione e'
        una decisione del proprietario registrata in `deferred-work.md`. Dare qui un
        nome alla soppressione sceglierebbe la seconda lettura in un modulo.

        L'insieme e' pinnato per intero, non per sottrazione: il giorno in cui la
        decisione sara' presa, questo test diventa rosso, ed e' il posto dove
        dichiarare il caso nuovo.
        """
        assert PRIMITIVES == {
            "fusione_di_componenti",
            "fusione_di_nodi",
            "eliminazione_di_nodo",
            "sostituzione_di_componente",
            "rimozione_di_componente",
        }
        with pytest.raises(ValueError, match="fuori dal vocabolario strutturale"):
            StructuralDerivation("ZERO_VOLTAGE_SOURCE", (C("V1"),), ())  # type: ignore[arg-type]


class TestLaFormaDiUnaRiscrittura:
    """I cinque nomi non sono intercambiabili, e qui si misura che non lo sono.

    Prima di questa tabella `check_delta` verificava gli aggregati contro i due
    circuiti e non guardava mai `d.operation`: le quattro derivazioni qui sotto si
    costruivano tutte, e con esse ogni lineage falsa che rispettasse gli aggregati.
    """

    def test_le_cinque_forme_sono_distinte_a_due_a_due(self):
        """La traduzione eseguibile di «non intercambiabili»: se due riscritture
        ammettessero le stesse derivazioni, sceglierne una non affermerebbe nulla."""
        assert len({(f.genere, f.ingressi_minimi, f.uscite) for f in FORME.values()}) \
            == len(PRIMITIVES)

    def test_una_riscrittura_non_trasforma_un_nodo_in_un_componente(self):
        with pytest.raises(ValueError, match="genere component"):
            StructuralDerivation("eliminazione_di_nodo", (N("b"),), (C("Req"),))

    def test_una_fusione_di_componenti_su_nodi_e_rifiutata(self):
        with pytest.raises(ValueError, match="genere node"):
            StructuralDerivation("fusione_di_componenti", (N("a"), N("b")), (N("z"),))

    def test_una_fusione_di_un_componente_solo_non_e_una_fusione(self):
        with pytest.raises(ValueError, match="ne vuole almeno 2"):
            StructuralDerivation("fusione_di_componenti", (C("R1"),), (C("Req"),))

    def test_una_rimozione_che_produce_qualcosa_e_rifiutata(self):
        with pytest.raises(ValueError, match="esattamente 0"):
            StructuralDerivation("rimozione_di_componente", (C("R1"),), (C("R9"),))

    def test_una_fusione_di_nodi_senza_superstite_e_rifiutata(self):
        """E' il capo su cui `fusione_di_nodi` ed `eliminazione_di_nodo` si separano:
        la prima lascia un erede, la seconda no."""
        with pytest.raises(ValueError, match="esattamente 1"):
            StructuralDerivation("fusione_di_nodi", (N("b"),), ())
        assert StructuralDerivation("eliminazione_di_nodo", (N("b"),), ())


class TestLaTabellaDelleForme:
    """CV5: ogni condizione imposta alla tabella ha un test che l'ha vista sollevare."""

    def test_una_riscrittura_senza_forma_e_rifiutata(self):
        from kirchhoff.domain.transform.primitives import _verifica_forme
        with pytest.raises(RuntimeError, match="divergenti"):
            _verifica_forme({"fusione_di_nodi": Forma("node", 1, 1)})

    def test_due_riscritture_con_la_stessa_forma_sono_rifiutate(self):
        from kirchhoff.domain.transform.primitives import _verifica_forme
        gemelle = dict(FORME)
        gemelle["fusione_di_nodi"] = gemelle["eliminazione_di_nodo"]
        with pytest.raises(RuntimeError, match="hanno la stessa forma"):
            _verifica_forme(gemelle)

    def test_nessuna_riscrittura_crea_senza_ascendenza(self):
        """Se una comparira', questa e' la condizione da cambiare."""
        from kirchhoff.domain.transform.primitives import _verifica_forme
        assert all(f.ingressi_minimi >= 1 for f in FORME.values())
        senza = dict(FORME)
        senza["fusione_di_nodi"] = Forma("node", 0, 1)
        with pytest.raises(RuntimeError, match="zero ingressi"):
            _verifica_forme(senza)

    def test_la_tabella_reale_regge_al_proprio_controllo(self):
        from kirchhoff.domain.transform.primitives import _verifica_forme
        assert _verifica_forme(FORME) is None

    def test_un_genere_che_non_e_un_genere_di_entita_e_rifiutato(self):
        """La riconciliazione fra i due moduli, che un ciclo di import vieta di fare
        con un tipo condiviso."""
        from kirchhoff.domain.transform.delta import _verifica_generi_delle_forme
        with pytest.raises(RuntimeError, match="generi di entita' che non esistono"):
            _verifica_generi_delle_forme({"x": Forma("ramo", 1, 1)}, ENTITY_KINDS)

    def test_i_generi_reali_sono_tutti_noti(self):
        from kirchhoff.domain.transform.delta import _verifica_generi_delle_forme
        assert _verifica_generi_delle_forme(FORME, ENTITY_KINDS) is None


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
        d = StructuralDerivation("rimozione_di_componente", (C("RL"),), ())
        assert d.outputs == ()

    def test_una_derivazione_senza_ingressi_e_rifiutata(self):
        """Decisione esplicita, non omissione: nel vocabolario strutturale chiuso non
        esiste oggi una riscrittura che crei senza ascendenza — `_verifica_forme` lo
        impone alla tabella, e nessuna forma ammette zero ingressi. Se comparira',
        questo test cambia."""
        with pytest.raises(ValueError, match="0 entita' in ingresso"):
            StructuralDerivation("fusione_di_componenti", (), (C("Req"),))

    def test_ingresso_ripetuto(self):
        with pytest.raises(ValueError, match="ingresso ripetuto"):
            StructuralDerivation("fusione_di_componenti", (C("R1"), C("R1")), (C("Req"),))

    def test_uscita_ripetuta(self):
        with pytest.raises(ValueError, match="uscita ripetuta"):
            StructuralDerivation("fusione_di_componenti", (C("R1"),), (C("Req"), C("Req")))

    def test_gli_insiemi_sono_ordinati_canonicamente_alla_costruzione(self):
        a = StructuralDerivation("fusione_di_componenti", (C("R2"), C("R1")), (C("Req"),))
        b = StructuralDerivation("fusione_di_componenti", (C("R1"), C("R2")), (C("Req"),))
        assert a == b
        assert a.inputs == (C("R1"), C("R2"))


class TestDelta:
    FUSIONE = StructuralDerivation("fusione_di_componenti", (C("R1"), C("R2")), (C("Req"),))
    ALTRA = StructuralDerivation("fusione_di_componenti", (C("R3"), C("R4")), (C("Rp"),))

    def test_ordine_canonico_indipendente_dall_inserimento(self):
        """Invariante 6: stesso contenuto, ordine diverso, stesso oggetto e stessa
        serializzazione. Senza questo, replay e certificate divergono per rumore."""
        uno = Delta((self.FUSIONE, self.ALTRA))
        due = Delta((self.ALTRA, self.FUSIONE))
        assert uno == due
        assert [str(d) for d in uno.derivations] == [str(d) for d in due.derivations]

    def test_derivazione_ripetuta_identica(self):
        with pytest.raises(ValueError, match="ripetuta identica"):
            Delta((self.FUSIONE, self.FUSIONE))

    def test_entita_consumata_due_volte(self):
        altra = StructuralDerivation("fusione_di_componenti", (C("R1"), C("R9")), (C("Rp"),))
        with pytest.raises(ValueError, match="consumata due volte"):
            Delta((self.FUSIONE, altra))

    def test_entita_prodotta_da_due_derivazioni(self):
        altra = StructuralDerivation("fusione_di_componenti", (C("R3"), C("R4")), (C("Req"),))
        with pytest.raises(ValueError, match="prodotta da due derivazioni"):
            Delta((self.FUSIONE, altra))

    def test_la_lineage_non_puo_chiudersi_in_cerchio(self):
        """Condizione che con una derivazione sola non poteva darsi.

        Le riscritture di un passo descrivono lo stesso salto `Cₖ → Cₖ₊₁` da piu'
        punti, non una pipeline: non c'e' un «prima» e un «dopo» fra due di esse.
        Misurato prima della guardia: le due derivazioni qui sotto si costruivano, e
        `derived_from` rispondeva in cerchio.
        """
        with pytest.raises(ValueError, match="consumata da un'altra"):
            Delta((
                StructuralDerivation("sostituzione_di_componente", (C("R1"),), (C("R2"),)),
                StructuralDerivation("sostituzione_di_componente", (C("R2"),), (C("R1"),)),
            ))

    def test_dentro_una_sola_derivazione_ingresso_e_uscita_possono_coincidere(self):
        """Il caso che la guardia sopra non deve prendere: e' la forma con cui AD-22
        v2.1 vuole scritta l'entita' mutata in luogo."""
        d = Delta((StructuralDerivation(
            "sostituzione_di_componente", (C("R2"),), (C("R2"),)),))
        assert d.consumed == d.produced == frozenset({C("R2")})

    def test_delta_vuoto_e_legittimo(self):
        assert Delta().derivations == ()


class TestInterrogabilita:
    """Invariante 8: entrambe le direzioni cadono dal modello, senza indice parallelo."""

    D = Delta((StructuralDerivation("fusione_di_componenti", (C("R1"), C("R2")), (C("Req"),)),))

    def test_che_fine_ha_fatto_R1(self):
        d = self.D.what_happened_to(C("R1"))
        assert d is not None
        assert d.operation == "fusione_di_componenti"
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
            StructuralDerivation("fusione_di_componenti", (C("R1"), C("R2")), (C("Req"),)),
            StructuralDerivation("eliminazione_di_nodo", (N("b"),), ()),
        ))
        assert check_delta(delta, self.PRIMA, self.DOPO) == ()

    def test_preserve_set_si_calcola_dai_circuiti_non_dal_delta(self):
        """CV1: nessuno dei due insiemi si deduce dall'altro."""
        assert preserve_set(self.PRIMA, self.DOPO) == frozenset({N("0"), N("a")})

    def test_sparizione_non_spiegata(self):
        delta = Delta((StructuralDerivation(
            "fusione_di_componenti", (C("R1"), C("R2")), (C("Req"),)),))
        codici = [v.code for v in check_delta(delta, self.PRIMA, self.DOPO)]
        assert "sparizione_non_spiegata" in codici

    def test_comparsa_non_spiegata(self):
        # Tutto cio' che sparisce e' consumato e nulla e' prodotto: l'equivalente
        # esiste in `DOPO` e nessuna derivazione lo genera.
        delta = Delta((StructuralDerivation(
                           "rimozione_di_componente", (C("R1"), C("R2")), ()),
                       StructuralDerivation("eliminazione_di_nodo", (N("b"),), ())))
        codici = [v.code for v in check_delta(delta, self.PRIMA, self.DOPO)]
        assert "comparsa_non_spiegata" in codici

    def test_input_inesistente(self):
        delta = Delta((
            StructuralDerivation(
                "fusione_di_componenti", (C("R1"), C("R2"), C("R9")), (C("Req"),)),
            StructuralDerivation("eliminazione_di_nodo", (N("b"),), ()),
        ))
        v = [x for x in check_delta(delta, self.PRIMA, self.DOPO) if x.code == "input_inesistente"]
        assert [x.subject for x in v] == ["component:R9"]

    def test_output_inesistente(self):
        delta = Delta((
            StructuralDerivation(
                "fusione_di_componenti", (C("R1"), C("R2")), (C("Rz"),)),
            StructuralDerivation("eliminazione_di_nodo", (N("b"),), ()),
        ))
        v = [x for x in check_delta(delta, self.PRIMA, self.DOPO) if x.code == "output_inesistente"]
        assert [x.subject for x in v] == ["component:Rz"]

    def test_una_preservata_non_puo_essere_consumata(self):
        delta = Delta((
            StructuralDerivation("fusione_di_componenti", (C("R1"), C("R2")), (C("Req"),)),
            StructuralDerivation("eliminazione_di_nodo", (N("b"), N("a")), ()),
        ))
        v = [x for x in check_delta(delta, self.PRIMA, self.DOPO) if x.code == "preservata_consumata"]
        assert [x.subject for x in v] == ["node:a"]

    def test_una_preservata_PUO_essere_uscita_perche_e_li_che_atterra_una_fusione(self):
        """Unione di nodi: `n2` sparisce dentro `n1`, che sopravvive."""
        prima = _ir(_r("R1", "n1", "0", 10), _r("R2", "n2", "0", 20), nodes=("0", "n1", "n2"))
        dopo = _ir(_r("R1", "n1", "0", 10), _r("R2", "n1", "0", 20), nodes=("0", "n1"))
        # `R2` passa da `(n2,0)` a `(n1,0)`: i terminali cambiano perche' il nodo che
        # tocca viene assorbito. Sotto AD-22 **v2.2** non e' piu' preservata — e' la
        # conseguenza dichiarata del ritiro di `node_mapping`, gia' fissata da
        # `test_un_componente_i_cui_terminali_cambiano_non_e_preservato`. Il `Delta`
        # deve quindi renderne conto: «una rimozione piu' una creazione, e come tale
        # deve comparire nel Delta» (AD-22 v2.1).
        #
        # **Cio' che `check_delta` esige non basta piu' a far passare il passo.**
        # Misurato dopo la Story 1.1: su questa stessa coppia di circuiti,
        # `check_transform` restituisce `Refusal(identity_violation, R2)`, perche'
        # `R2` compare in entrambi senza nominare la stessa entita'. Il `Delta` qui
        # sotto e' corretto per il proprio controllore e resta la risposta giusta alla
        # domanda che questo test pone; una fusione di nodi che sposti i terminali di
        # un componente sopravvissuto e' pero' oggi un passo **rifiutato**, e nessuna
        # delle due riduzioni del catalogo la produce. Registrato in
        # `deferred-work.md`.
        #
        # Prima della correzione degli insiemi, `prima - dopo` era calcolato per solo
        # identificatore e `R2` non compariva: il `Delta` che la ignorava passava.
        delta = Delta((
            StructuralDerivation("fusione_di_nodi", (N("n2"),), (N("n1"),)),
            StructuralDerivation("sostituzione_di_componente", (C("R2"),), (C("R2"),)),
        ))
        assert check_delta(delta, prima, dopo) == ()
        assert N("n1") in preserve_set(prima, dopo)
        assert C("R2") not in preserve_set(prima, dopo)

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
            "fusione_di_componenti", (C("R1"), C("R2")), (C("R1"),)),))
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
        delta = Delta((StructuralDerivation("rimozione_di_componente", (C("R1"),), ()),))
        a = check_delta(delta, self.PRIMA, self.DOPO)
        b = check_delta(delta, self.PRIMA, self.DOPO)
        assert a == b and len(a) > 0
        assert all(isinstance(v, DeltaViolation) for v in a)
