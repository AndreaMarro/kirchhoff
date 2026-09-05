"""Story 1.3 — il vocabolario chiuso dei prefissi, e la maniera di coniare.

CV6: *«i due operandi non hanno entita' ne' identificatore»*. Questo file copre la
meta' «identificatore»; la ritenzione sta in `test_layout.py` e la relazione in
`test_proof.py`.
"""

from __future__ import annotations

from typing import get_args

import pytest

from kirchhoff.domain.identity import (
    ALFABETO,
    BIT_CASUALITA,
    BIT_ISTANTE,
    GENERI,
    LUNGHEZZA,
    OLTRE_IL_MASSIMO,
    IdentityKind,
    conia,
    genere_di,
    verifica,
)

ENTROPIA = bytes(range(10))


# --- il vocabolario ----------------------------------------------------------

def test_i_generi_sono_i_sette_delle_convenzioni():
    """`Consistency Conventions`: `ir_`, `sol_`, `var_`, `evt_`, e dalla v2.1
    `lay_` e `patch_`; dalla Proof Demo 0.1 (D-H1.5-1) `sess_` per l'occurrence
    della `ProofSession` pubblicata. Estensione deliberata, non deriva."""
    assert GENERI == {"ir", "sol", "var", "evt", "lay", "patch", "sess"}


def test_sess_conia_e_verifica_un_ulid_di_occurrence():
    valore = conia("sess", 1_700_000_000_000, ENTROPIA)
    assert valore.startswith("sess_")
    assert verifica(valore, "sess") == valore
    with pytest.raises(ValueError, match="sess"):
        verifica(valore, "ir")


def test_i_generi_sono_derivati_dal_literal_e_non_riscritti():
    """La stessa disciplina di `refusal.CAUSES` e di `transform.PRIMITIVES`: una
    fonte sola, quindi nessun secondo insieme che possa divergere (E-62)."""
    assert GENERI == frozenset(get_args(IdentityKind))


def test_l_alfabeto_e_crockford_senza_le_quattro_lettere_ambigue():
    assert len(ALFABETO) == 32
    assert not ({"I", "L", "O", "U"} & set(ALFABETO))


def test_le_26_cifre_coprono_i_128_bit_del_ulid():
    assert LUNGHEZZA * 5 >= BIT_ISTANTE + BIT_CASUALITA == 128


# --- conia: il ULID vero -----------------------------------------------------

def test_conia_produce_prefisso_e_ventisei_cifre():
    valore = conia("lay", 1_700_000_000_000, ENTROPIA)
    assert valore.startswith("lay_")
    assert len(valore) == len("lay_") + LUNGHEZZA
    assert set(valore[4:]) <= set(ALFABETO)


def test_conia_e_deterministico_sugli_stessi_ingressi():
    """E' cio' che rende un replay riproducibile invece che verificabile a occhio."""
    assert conia("ir", 42, ENTROPIA) == conia("ir", 42, ENTROPIA)


def test_conia_ordina_lessicograficamente_per_istante():
    """La proprieta' che distingue un ULID da un'impronta: due layout dello stesso
    stato visuale restano due, e si ordinano per quando sono nati."""
    prima = conia("lay", 1_000, ENTROPIA)
    dopo = conia("lay", 2_000, ENTROPIA)
    assert prima < dopo


#: Vettori a risposta nota. Senza di essi ogni test di questo file e' **relativo**
#: — uguale, diverso, ordinato — e un alfabeto permutato o i due campi invertiti
#: (`casualita << 48 | istante`) li passerebbero tutti. Un identificatore dev'essere
#: stabile fra versioni del codice, o «citabile da evidenza, replay ed eval» non
#: significa niente: il primo vettore e' l'istante del vettore di specifica del ULID
#: (1469918176385 ms), gli altri due isolano i due campi.
VETTORI = [
    (1469918176385, bytes(10), "ir_01ARYZ6S410000000000000000"),
    (0, bytes(9) + b"\x01", "ir_00000000000000000000000001"),
    (1, bytes(10), "ir_00000000010000000000000000"),
]


@pytest.mark.parametrize(("istante", "casualita", "atteso"), VETTORI)
def test_conia_da_la_risposta_nota_su_ogni_vettore(istante, casualita, atteso):
    assert conia("ir", istante, casualita) == atteso


def test_l_istante_occupa_le_cifre_alte_e_la_casualita_quelle_basse():
    """La proprieta' che i vettori fissano, detta una volta: invertire i due campi
    darebbe identificatori validi che ordinano per entropia invece che per tempo."""
    solo_istante = conia("ir", (1 << BIT_ISTANTE) - 1, bytes(10))
    solo_casualita = conia("ir", 0, b"\xff" * 10)
    assert solo_istante[3:] > solo_casualita[3:]
    assert solo_istante.endswith("0" * 16)
    assert solo_casualita[3:3 + 10] == "0" * 10


def test_l_alfabeto_e_nell_ordine_dei_valori_crescenti():
    """Una permutazione dell'alfabeto passerebbe ogni test relativo: qui l'ordine
    delle cifre e' l'ordine dei valori che rappresentano."""
    assert ALFABETO == "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
    coniati = [conia("ir", 0, bytes(9) + bytes([v])) for v in range(len(ALFABETO))]
    assert [c[-1] for c in coniati] == list(ALFABETO)


def test_conia_rifiuta_un_genere_fuori_dal_vocabolario():
    with pytest.raises(ValueError, match="fuori dal vocabolario chiuso"):
        conia("layout", 1, ENTROPIA)  # type: ignore[arg-type]


@pytest.mark.parametrize("istante", ["1700000000000", 1.5, True])
def test_conia_rifiuta_un_istante_che_non_e_un_intero(istante):
    """`True` compreso: `bool` e' `int` in Python, e un istante booleano
    passerebbe ogni controllo di intervallo scrivendo l'epoca."""
    with pytest.raises(TypeError, match="millisecondi dall'epoca"):
        conia("evt", istante, ENTROPIA)  # type: ignore[arg-type]


@pytest.mark.parametrize("istante", [-1, 1 << BIT_ISTANTE])
def test_conia_rifiuta_un_istante_fuori_dai_quarantotto_bit(istante):
    with pytest.raises(ValueError, match=f"fuori dai {BIT_ISTANTE} bit"):
        conia("evt", istante, ENTROPIA)


@pytest.mark.parametrize("quanti", [0, 9, 11])
def test_conia_rifiuta_un_entropia_di_lunghezza_sbagliata(quanti):
    with pytest.raises(ValueError, match="il ULID ne vuole 10"):
        conia("sol", 1, bytes(quanti))


@pytest.mark.parametrize("casualita", ["0123456789", [0] * 10, None])
def test_conia_rifiuta_una_casualita_che_non_e_di_byte(casualita):
    """Una `str` di dieci caratteri supera il controllo di lunghezza e muore dentro
    `int.from_bytes` con un messaggio che parla di conversione, non di entropia."""
    with pytest.raises(TypeError, match="invece di bytes"):
        conia("sol", 1, casualita)  # type: ignore[arg-type]


def test_conia_accetta_un_bytearray():
    """Chi legge da un generatore di entropia riceve spesso un buffer mutabile: e'
    dieci byte, e rifiutarlo sarebbe una guardia sul contenitore invece che sul dato."""
    assert conia("sol", 1, bytearray(ENTROPIA)) == conia("sol", 1, ENTROPIA)


def test_conia_riempie_le_ventisei_cifre_anche_al_massimo():
    """Il valore piu' grande rappresentabile non trabocca oltre le 26 cifre."""
    massimo = conia("var", (1 << BIT_ISTANTE) - 1, b"\xff" * 10)
    assert len(massimo) == len("var_") + LUNGHEZZA
    assert verifica(massimo, "var") == massimo


# --- una maniera sola di coniare ---------------------------------------------

def test_non_esiste_una_seconda_maniera_di_coniare():
    """Una versione precedente offriva `conia_da_contenuto`, un identificatore
    derivato da un'impronta: stessa forma di un ULID e nessun istante dentro, quindi
    ordinabile in una successione plausibile e falsa. Le convenzioni dicono «ULID»,
    e chi produce senza orologio non conia — conia chi ritiene."""
    import kirchhoff.domain.identity as identita
    assert not hasattr(identita, "conia_da_contenuto")


def test_il_prefisso_dice_il_genere_senza_risolvere_l_entita():
    assert genere_di(conia("lay", 7, ENTROPIA)) == "lay"
    assert genere_di(conia("patch", 7, ENTROPIA)) == "patch"


# --- verifica ----------------------------------------------------------------

def test_verifica_restituisce_cio_che_accetta():
    valore = conia("ir", 5, ENTROPIA)
    assert verifica(valore, "ir") is valore


def test_verifica_rifiuta_un_genere_fuori_dal_vocabolario():
    with pytest.raises(ValueError, match="fuori dal vocabolario chiuso"):
        verifica(conia("ir", 5, ENTROPIA), "nodo")  # type: ignore[arg-type]


def test_verifica_rifiuta_un_intero():
    """«Mai interi auto-incrementali su entita' esposte» — e un intero qui e'
    esattamente quello."""
    with pytest.raises(TypeError, match="interi auto-incrementali"):
        verifica(17, "ir")  # type: ignore[arg-type]


def test_verifica_rifiuta_il_prefisso_di_un_altro_genere():
    """Il difetto che questa guardia chiude: un `lay_` accettato dove ci si aspetta
    un `patch_` congiunge due entita' che non hanno nulla a che vedere."""
    with pytest.raises(ValueError, match="atteso il prefisso 'patch_'"):
        verifica(conia("lay", 1, ENTROPIA), "patch")


@pytest.mark.parametrize("corpo", ["", "0" * 25, "0" * 27])
def test_verifica_rifiuta_una_lunghezza_diversa_da_ventisei(corpo):
    with pytest.raises(ValueError, match=f"ne servono {LUNGHEZZA}"):
        verifica(f"lay_{corpo}", "lay")


@pytest.mark.parametrize("cifra", ["I", "L", "O", "U", "-"])
def test_verifica_rifiuta_una_cifra_fuori_dall_alfabeto(cifra):
    with pytest.raises(ValueError, match="Crockford base32"):
        verifica(f"lay_{cifra}{'0' * 25}", "lay")


@pytest.mark.parametrize("corpo", ["Z" * 26, "8" + "0" * 25])
def test_verifica_rifiuta_un_valore_che_nessun_conio_puo_produrre(corpo):
    """26 cifre reggono 130 bit, il ULID ne usa 128: esistono stringhe di forma
    giusta e valore impossibile. Accettarle lascia citare in un'evidenza un
    identificatore che nessuno ha mai coniato."""
    with pytest.raises(ValueError, match="oltre i 128 bit"):
        verifica(f"lay_{corpo}", "lay")


def test_verifica_accetta_l_ultimo_valore_coniabile():
    """Il confine e' esattamente dove `conia` arriva, non uno prima."""
    massimo = conia("lay", (1 << BIT_ISTANTE) - 1, b"\xff" * 10)
    assert verifica(massimo, "lay") == massimo
    assert OLTRE_IL_MASSIMO == 1 << 128


# --- genere_di ---------------------------------------------------------------

def test_genere_di_rifiuta_cio_che_non_e_una_stringa():
    with pytest.raises(TypeError, match="invece di str"):
        genere_di(None)  # type: ignore[arg-type]


@pytest.mark.parametrize("valore", ["0" * 26, "proof_" + "0" * 26])
def test_genere_di_rifiuta_cio_che_nessun_genere_prefissa(valore):
    with pytest.raises(ValueError, match="nessuno dei generi noti"):
        genere_di(valore)


def test_genere_di_verifica_anche_il_corpo_e_non_solo_il_prefisso():
    """Leggere il prefisso senza verificare il resto accetterebbe `lay_` seguito
    da qualunque cosa."""
    with pytest.raises(ValueError, match="ne servono 26"):
        genere_di("lay_TROPPOCORTO")
