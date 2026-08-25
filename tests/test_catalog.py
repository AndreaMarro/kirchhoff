"""FR-43 — il Catalogo e' chiuso, e la sua apertura e' una decisione registrata.

Il vocabolario e il discriminante d'identita' sono verificati altrove:
`test_delta.py::TestCatalogo` confronta `CATALOG` con `REFERENCE_TRANSFORMATIONS`,
`test_transform.py::TestDiscriminanteDiIdentita` copre AD-22 v2.1. Qui c'e' l'altra
meta' del Catalogo: **chi e' applicabile oggi**, e a quali condizioni quell'insieme
puo' crescere.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from kirchhoff.domain.transform import (
    CATALOG, SUPPORTED, CatalogOpening, implemented, transformations_supported,
)
from kirchhoff.domain.transform.catalog import _dentro_il_vocabolario

F = Fraction


def _decisione(**cambi) -> CatalogOpening:
    """Una registrazione completa. Ogni test ne deforma un campo solo."""
    campi = dict(
        vcer_arm_a=F(97, 100), vcer_arm_b=F(61, 100),
        sm18_arm_a=F(9, 10), sm18_arm_b=F(1, 2),
        corpus="reference-set/dev",
        decided_by="proprietario",
        decided_on="2026-08-24",
        opens=frozenset({"stella_triangolo"}),
    )
    campi.update(cambi)
    return CatalogOpening(**campi)


class TestVocabolarioEApplicabili:
    """Esistere, essere applicabile ed essere implementata sono tre cose."""

    def test_le_applicabili_sono_le_tre_di_FR_43(self):
        assert SUPPORTED == frozenset({"serie", "parallelo", "partitore_di_tensione"})

    def test_SM_C5_vale_tre(self):
        """*«Deve restare a tre»* finche' il kill criterion di Gate A non e' superato.
        Il conteggio si legge dall'insieme che lo definisce, non da un riepilogo."""
        assert len(transformations_supported()) == 3

    def test_un_nome_del_vocabolario_non_e_per_questo_applicabile(self):
        assert "resistenza_equivalente_di_thevenin" in CATALOG
        assert "resistenza_equivalente_di_thevenin" not in SUPPORTED

    def test_i_tre_insiemi_sono_annidati(self):
        """Implementare cio' che non e' applicabile aggirerebbe FR-43 dal basso."""
        assert implemented() <= SUPPORTED <= CATALOG

    def test_un_insieme_di_applicabili_fuori_dal_vocabolario_e_rifiutato(self):
        with pytest.raises(ValueError, match="fuori dal vocabolario chiuso"):
            _dentro_il_vocabolario(frozenset({"REMOVE_LOAD"}), "prova")


class TestDecisioneDiApertura:
    """*«Una registrazione priva di uno di questi campi non apre il Catalogo.»*"""

    def test_un_campo_assente_non_costruisce_la_registrazione(self):
        with pytest.raises(TypeError):
            CatalogOpening(  # type: ignore[call-arg]
                vcer_arm_a=F(1), vcer_arm_b=F(1), sm18_arm_a=F(1), sm18_arm_b=F(1),
                corpus="reference-set/dev", decided_by="proprietario",
                opens=frozenset({"stella_triangolo"}))

    @pytest.mark.parametrize(
        "campo", ["vcer_arm_a", "vcer_arm_b", "sm18_arm_a", "sm18_arm_b"])
    def test_misura_in_virgola_mobile_respinta(self, campo):
        """Nessun `float` nel dominio, nemmeno nel numero che decide l'apertura."""
        with pytest.raises(TypeError, match="serve una Fraction"):
            _decisione(**{campo: 0.61})

    @pytest.mark.parametrize("campo", ["corpus", "decided_by"])
    def test_campo_presente_ma_vuoto(self, campo):
        """L'incompletezza che passa inosservata non e' il campo assente: e' questa."""
        with pytest.raises(ValueError, match=f"senza {campo}"):
            _decisione(**{campo: ""})

    def test_data_fuori_forma(self):
        with pytest.raises(ValueError, match="AAAA-MM-GG"):
            _decisione(decided_on="24 agosto 2026")

    @pytest.mark.parametrize("giorno", ["2026-13-99", "2026-02-30", "2026-00-10"])
    def test_una_data_che_rispetta_la_forma_ma_non_e_un_giorno(self, giorno):
        """La forma da sola non basta: `2026-13-99` la rispetta e non e' mai esistito.

        Una decisione datata in un mese che non esiste non e' stata presa in alcun
        momento, e archiviarla come valida rende inverificabile *quando* il kill
        criterion sarebbe passato.
        """
        with pytest.raises(ValueError, match="non e' un giorno del calendario"):
            _decisione(decided_on=giorno)

    def test_la_verifica_della_data_non_legge_un_orologio(self):
        """AD-2: il dominio non ha orologi. Una data di ieri e una del 2199 valgono
        uguale — e' la decisione a datarsi, non il codice."""
        assert _decisione(decided_on="1999-01-01").decided_on == "1999-01-01"
        assert _decisione(decided_on="2199-12-31").decided_on == "2199-12-31"

    def test_una_decisione_che_non_apre_nulla(self):
        with pytest.raises(ValueError, match="non apre nulla"):
            _decisione(opens=frozenset())

    @pytest.mark.parametrize(
        "gia_applicabili",
        [frozenset({"serie"}), frozenset({"serie", "parallelo"}), SUPPORTED])
    def test_una_decisione_che_apre_solo_cio_che_e_gia_applicabile(self, gia_applicabili):
        """«Che non apre nulla» non e' la stessa cosa di «vuota».

        Una registrazione che nomina solo Trasformazioni gia' applicabili lascia
        l'insieme identico: accettarla archivierebbe una decisione come se avesse
        avuto un effetto che non ha avuto, e SM-C5 resterebbe tre mentre il registro
        delle decisioni dice il contrario.
        """
        with pytest.raises(ValueError, match="non apre nulla"):
            _decisione(opens=gia_applicabili)

    def test_una_decisione_mista_apre_per_la_parte_nuova(self):
        aperte = _decisione(opens=frozenset({"serie", "stella_triangolo"}))
        assert transformations_supported(aperte) == SUPPORTED | {"stella_triangolo"}

    def test_una_decisione_apre_il_catalogo_ma_non_lo_estende(self):
        with pytest.raises(ValueError, match="fuori dal vocabolario chiuso"):
            _decisione(opens=frozenset({"REMOVE_LOAD"}))

    def test_una_registrazione_completa_apre(self):
        aperte = transformations_supported(_decisione())
        assert aperte == SUPPORTED | {"stella_triangolo"}
        assert aperte <= CATALOG

    def test_senza_decisione_restano_le_tre(self):
        assert transformations_supported(None) == SUPPORTED

    def test_la_registrazione_non_e_uno_stato_globale(self):
        """Chi vuole il Catalogo aperto esibisce la decisione a ogni chiamata: una
        apertura che restasse appiccicata al modulo renderebbe SM-C5 dipendente
        dall'ordine delle chiamate invece che dalla decisione."""
        transformations_supported(_decisione())
        assert transformations_supported() == SUPPORTED
