"""Gli identificatori delle entita' esposte: un vocabolario chiuso di prefissi.

`Consistency Conventions` dello spine: *«ULID con prefisso per tipo (`ir_`, `sol_`,
`var_`, `evt_`; dalla v2.1 anche `lay_` per il `LayoutIR` e `patch_` per il
`LayoutPatch`, che senza identita' non sono citabili da evidenza, replay ed eval).
Mai interi auto-incrementali su entita' esposte.»*

CV6 conta quella riga fra le tre cose che rendono VCER incalcolabile: *«i due
operandi non hanno entita' ne' identificatore»*. Questo modulo e' la meta'
«identificatore»; la ritenzione vive in `render/layout` e la relazione in
`domain/proof`.

## Una fonte sola per i sei prefissi

I generi sono **derivati** da `IdentityKind` con `get_args`, come `refusal.CAUSES` da
`Cause` e `transform.PRIMITIVES` da `StructuralPrimitive`. Non c'e' un secondo
insieme da tenere allineato: E-62 dice che un vocabolario scritto due volte diverge
nel posto dove nessuno guarda, e questo decide se un'evidenza sa di che cosa parla.

## Un modo solo di nascere, ed e' il ULID delle convenzioni

`conia` e' l'unica funzione che conia: 48 bit di istante piu' 80 di casualita', 26
cifre Crockford base32. **Prende l'istante e la casualita' come argomenti**, non li
chiede a nessuno: e' la stessa disciplina di `ClockPort` (AD-17, *«il tempo si
inietta»*), e senza di essa questo modulo non potrebbe stare sotto `domain/`.

Non esiste una seconda maniera. Una versione precedente di questo modulo ne offriva
una — un identificatore derivato da un'impronta del contenuto, per il produttore
puro del `LayoutPatch` — ed e' stata ritirata: le convenzioni dicono «ULID», e un
identificatore che *sembra* un ULID senza esserlo ordina per impronta invece che per
tempo, quindi produce una successione plausibile e falsa. Chi produce senza orologio
non conia: **conia chi ritiene**, con l'istante iniettato. E' cio' che
`render/layout` fa per il `LayoutIR` e per il `LayoutPatch`.

## Chi fornisce la casualita', e perche' dev'essere fresca

Il chiamante, dalla stessa firma da cui passa l'istante — non c'e' un `EntropyPort`
nell'elenco dei port dello spine, e questo modulo non ne inventa uno. Il requisito
che ne discende va detto qui perche' nessun altro puo' imporlo: **dieci byte nuovi a
ogni conio**. A entropia costante due entita' coniate nello stesso millisecondo
ricevono lo stesso identificatore, e il registro che le ritiene solleva «gia'
depositato» — un errore che accusa chi deposita di un difetto di chi ha scelto
l'entropia. Un test che ferma l'orologio puo' fissare anche l'entropia, perche' li'
gli istanti sono distinti per costruzione.

Puro: nessuna I/O, nessun orologio, nessuna casualita'.
"""

from __future__ import annotations

from typing import Literal, get_args

#: I generi di entita' esposta che hanno un prefisso. Chiuso: aggiungerne uno e'
#: una modifica delle `Consistency Conventions` dello spine, non di questo modulo.
IdentityKind = Literal["ir", "sol", "var", "evt", "lay", "patch"]

#: Derivato, non riscritto. Vedi il docstring: una fonte sola per i sei prefissi.
GENERI: frozenset[str] = frozenset(get_args(IdentityKind))

#: Crockford base32 — senza `I`, `L`, `O` e `U`, cosi' che un identificatore letto
#: ad alta voce o trascritto a mano non possa diventarne un altro.
ALFABETO = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

#: 26 cifre da 5 bit coprono i 128 bit di un ULID (130 ≥ 128).
LUNGHEZZA = 26

#: I due campi del ULID, in bit.
BIT_ISTANTE = 48
BIT_CASUALITA = 80

#: Il primo valore che 128 bit **non** rappresentano. Le 26 cifre ne reggerebbero
#: 130, quindi esistono stringhe di forma giusta e valore impossibile: `verifica` le
#: rifiuta, o accetterebbe identificatori che nessun `conia` puo' produrre.
OLTRE_IL_MASSIMO = 1 << (BIT_ISTANTE + BIT_CASUALITA)

_CIFRE = frozenset(ALFABETO)
_VALORE_DI = {cifra: valore for valore, cifra in enumerate(ALFABETO)}


def _codifica(valore: int) -> str:
    """I 128 bit in 26 cifre Crockford, la piu' significativa per prima."""
    cifre: list[str] = []
    for _ in range(LUNGHEZZA):
        valore, resto = divmod(valore, len(ALFABETO))
        cifre.append(ALFABETO[resto])
    return "".join(reversed(cifre))


def _decodifica(cifre: str) -> int:
    """Il valore delle 26 cifre. L'inversa di `_codifica` sui valori validi."""
    valore = 0
    for cifra in cifre:
        valore = valore * len(ALFABETO) + _VALORE_DI[cifra]
    return valore


def _verifica_genere(genere: str) -> None:
    if genere not in GENERI:
        raise ValueError(
            f"genere di identificatore {genere!r} fuori dal vocabolario chiuso: "
            f"{', '.join(sorted(GENERI))}. Aggiungerne uno e' una modifica delle "
            "Consistency Conventions dello spine.")


def conia(genere: IdentityKind, istante: int, casualita: bytes) -> str:
    """Il ULID delle convenzioni: `<genere>_<26 cifre>`, ordinabile nel tempo.

    `istante` sono i millisecondi dall'epoca — 48 bit, come il ULID prescrive — e
    arriva da un `ClockPort`, mai da questo modulo. `casualita` sono i 10 byte di
    entropia, **nuovi a ogni conio**, e arrivano da chi ce l'ha: vedi il docstring
    del modulo per la ragione. Iniettandoli, la funzione resta pura e due esecuzioni
    con gli stessi ingressi danno lo stesso identificatore: e' cio' che rende
    riproducibile un replay, che senza sarebbe verificabile solo a occhio.
    """
    _verifica_genere(genere)
    if not isinstance(istante, int) or isinstance(istante, bool):
        raise TypeError(
            f"istante {type(istante).__name__}: servono i millisecondi dall'epoca "
            "come intero. L'orologio si inietta (AD-17), non si converte qui.")
    if not 0 <= istante < 1 << BIT_ISTANTE:
        raise ValueError(
            f"istante {istante} fuori dai {BIT_ISTANTE} bit che il ULID gli "
            f"riserva: ammessi 0…{(1 << BIT_ISTANTE) - 1} millisecondi.")
    # Il controllo di tipo precede quello di lunghezza: una `str` di dieci caratteri
    # supererebbe il secondo e morirebbe dentro `int.from_bytes` con un messaggio
    # che parla di conversione, non di entropia — cioe' un difetto che si diagnostica
    # leggendo l'implementazione invece dell'errore.
    if not isinstance(casualita, bytes | bytearray):
        raise TypeError(
            f"casualita' {type(casualita).__name__} invece di bytes: i "
            f"{BIT_CASUALITA // 8} byte di entropia sono byte. Una stringa di "
            "lunghezza giusta passerebbe ogni altro controllo e conierebbe "
            "l'identificatore dei suoi punti di codice.")
    if len(casualita) != BIT_CASUALITA // 8:
        raise ValueError(
            f"casualita' di {len(casualita)} byte: il ULID ne vuole "
            f"{BIT_CASUALITA // 8}. Meno entropia di cosi' rende due identificatori "
            "dello stesso millisecondo indistinguibili.")
    return f"{genere}_{_codifica((istante << BIT_CASUALITA) | int.from_bytes(casualita, 'big'))}"


def verifica(valore: str, genere: IdentityKind) -> str:
    """Solleva se `valore` non e' un identificatore di quel genere. Lo restituisce.

    Restituisce cio' che ha accettato perche' il chiamante tipico e' un
    `__post_init__` di dataclass congelata, dove il valore va riassegnato comunque:
    `object.__setattr__(self, "identifier", verifica(...))` si legge in una riga.

    CV5: lo stack e' Python senza type checker, quindi «il vincolo e' nel tipo» qui
    non e' vero. La guardia gira a runtime e un test l'ha vista sollevare.
    """
    _verifica_genere(genere)
    if not isinstance(valore, str):
        raise TypeError(
            f"identificatore {type(valore).__name__} invece di str. Le convenzioni "
            "vietano gli interi auto-incrementali sulle entita' esposte, e un "
            "intero qui e' esattamente quello.")
    prefisso = f"{genere}_"
    if not valore.startswith(prefisso):
        raise ValueError(
            f"identificatore {valore!r}: atteso il prefisso {prefisso!r}. Il "
            "prefisso e' cio' che permette a un'evidenza di sapere di che genere "
            "di entita' parla senza risolverla.")
    corpo = valore[len(prefisso):]
    if len(corpo) != LUNGHEZZA:
        raise ValueError(
            f"identificatore {valore!r}: {len(corpo)} cifre dopo il prefisso, ne "
            f"servono {LUNGHEZZA}.")
    fuori = sorted(set(corpo) - _CIFRE)
    if fuori:
        raise ValueError(
            f"identificatore {valore!r}: {', '.join(repr(c) for c in fuori)} non "
            f"appartiene all'alfabeto Crockford base32 ({ALFABETO}).")
    # Forma giusta e valore impossibile: 26 cifre reggono 130 bit, il ULID ne usa
    # 128. Senza questo controllo `verifica` accetta identificatori che nessun
    # `conia` puo' produrre, e un'evidenza puo' citarne uno che non e' mai nato.
    if _decodifica(corpo) >= OLTRE_IL_MASSIMO:
        raise ValueError(
            f"identificatore {valore!r}: oltre i {BIT_ISTANTE + BIT_CASUALITA} bit "
            f"del ULID. Il massimo coniabile e' {genere}_{_codifica(OLTRE_IL_MASSIMO - 1)}; "
            "le 26 cifre ne rappresentano 130, e le due in piu' non sono un "
            "identificatore che qualcuno abbia coniato.")
    return valore


def genere_di(valore: str) -> str:
    """Il genere che l'identificatore dichiara, verificandolo.

    Serve dove un registro riceve identificatori di provenienza diversa e deve
    sapere che cosa gli e' arrivato prima di indicizzarlo: leggere il prefisso senza
    verificare il resto accetterebbe `lay_` seguito da qualunque cosa.
    """
    if not isinstance(valore, str):
        raise TypeError(f"identificatore {type(valore).__name__} invece di str")
    genere, separatore, _ = valore.partition("_")
    if not separatore or genere not in GENERI:
        raise ValueError(
            f"identificatore {valore!r}: nessuno dei generi noti "
            f"({', '.join(sorted(GENERI))}) lo prefissa.")
    verifica(valore, genere)  # type: ignore[arg-type]
    return genere
