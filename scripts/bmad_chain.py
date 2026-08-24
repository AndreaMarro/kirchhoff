"""Lo stato della catena BMAD, derivato dal disco invece che ricordato.

Il 14 agosto il passo 2 era stato eseguito alle 07:41 — `brief.md` a `version: 3`,
`addendum.md` con la sezione «H. Delta v3» — ma la tabella FASE 1 di `.claude/loop.md`
mostrava ancora `⬜`. Una ripartenza avrebbe rifatto il lavoro da capo. La causa non è
distrazione: lo stato viveva in una tabella Markdown che il loop doveva editare da sé, e
un passo che dipende dalla memoria di un agente con contesto fresco è un passo che prima
o poi salta.

`sprint-status.yaml` non ha questo problema perché ha uno script che lo scrive e un
validatore che lo controlla. Questo modulo fa la stessa cosa per la catena di §25.1, con
una differenza che chiude anche il caso opposto: lo stato **dichiarato** viene confrontato
con le **prove sul disco**, e la divergenza è un errore in entrambe le direzioni.

    dichiarato=done  prove assenti    → «dichiarato senza prova»
    dichiarato≠done  prove presenti   → «fatto e non tracciato»   ← il difetto del 14 ago

La prima direzione impedisce di spuntare un passo non fatto. La seconda fa emergere il
lavoro perso anche quando il comando di chiusura non è stato eseguito affatto — che è
l'unico modo perché il meccanismo sopravviva a un loop che dimentica.

La definizione della catena (i passi, le prove) sta qui, nel codice, versionata e
rivedibile. Lo stato sta in JSON, che è di proprietà della macchina: la tabella leggibile
in `loop.md` viene rigenerata da `rendi`, e non va scritta a mano.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
FILE_STATO = RADICE / "_bmad-output" / "planning-artifacts" / "bmad-chain-status.json"
FILE_LOOP = RADICE / ".claude" / "loop.md"

APERTURA = "<!-- BMAD-CHAIN:START -->"
CHIUSURA = "<!-- BMAD-CHAIN:END -->"

SCHEMA = "kirchhoff/bmad-chain@1"
STATI = ("backlog", "in-progress", "done")

PIANIFICATI = "_bmad-output/planning-artifacts"


@dataclass(frozen=True)
class Prova:
    """Un fatto verificabile su disco: un file che contiene una stringa letterale.

    Niente regex e niente giudizio di merito. Una prova dice «l'artefatto esiste e porta
    il timbro del passo», non «l'artefatto è buono» — quello è il lavoro della review.
    """

    percorso: str
    contiene: str
    min_byte: int = 0

    def soddisfatta(self, radice: Path) -> bool:
        f = radice / self.percorso
        if not f.is_file():
            return False
        if f.stat().st_size < self.min_byte:
            return False
        try:
            testo = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            return False
        return self.contiene in testo

    def descrivi(self) -> str:
        taglia = f" ≥{self.min_byte} B" if self.min_byte else ""
        return f"{self.percorso} contiene «{self.contiene}»{taglia}"


@dataclass(frozen=True)
class Passo:
    numero: int
    chiave: str
    titolo: str
    skill: str
    prove: tuple[Prova, ...] = ()
    segnali: tuple[Prova, ...] = field(default=())

    def prove_soddisfatte(self, radice: Path) -> bool:
        return all(p.soddisfatta(radice) for p in self.prove)

    def prove_mancanti(self, radice: Path) -> list[Prova]:
        return [p for p in self.prove if not p.soddisfatta(radice)]

    def segnali_mancanti(self, radice: Path) -> list[Prova]:
        return [s for s in self.segnali if not s.soddisfatta(radice)]


# La convenzione di timbro è quella che `brief.md` usa già sul disco: `version: 3` nel
# frontmatter YAML più un marcatore strutturale del passo. Gli artefatti v2 non la
# portano, quindi i passi 3-7 risultano non soddisfatti finché non vengono davvero
# riscritti. I `segnali` vengono dalla sezione «Cosa deve entrare nei documenti» di
# loop.md: non bloccano, si segnalano.
CATENA: tuple[Passo, ...] = (
    Passo(
        1, "01-costituzione", "Costituzione K-0…K-5", "—",
        prove=(
            Prova("docs/02-costituzione-kirchhoff.md", "K-5"),
            Prova("docs/02-costituzione-kirchhoff.md", "owner-locked"),
        ),
    ),
    Passo(
        2, "02-brief", "Brief update", "bmad-product-brief (update)",
        prove=(
            Prova(f"{PIANIFICATI}/briefs/brief-Kirchhoff-2026-08-13/brief.md",
                  "version: 3", min_byte=10_000),
            Prova(f"{PIANIFICATI}/briefs/brief-Kirchhoff-2026-08-13/addendum.md",
                  "H. Delta v3"),
        ),
    ),
    Passo(
        3, "03-prd", "PRD v3", "bmad-prd (update)",
        prove=(
            Prova(f"{PIANIFICATI}/prds/prd-Kirchhoff-2026-08-13/prd.md", "version: 3"),
        ),
        segnali=(
            Prova(f"{PIANIFICATI}/prds/prd-Kirchhoff-2026-08-13/prd.md", "CircuitIR"),
            Prova(f"{PIANIFICATI}/prds/prd-Kirchhoff-2026-08-13/prd.md", "LayoutIR"),
            Prova(f"{PIANIFICATI}/prds/prd-Kirchhoff-2026-08-13/prd.md", "ProofGraph"),
            Prova(f"{PIANIFICATI}/prds/prd-Kirchhoff-2026-08-13/prd.md", "VVDR"),
        ),
    ),
    Passo(
        4, "04-ux", "UX Pro update", "bmad-ux + ui-ux-pro-max:design-system",
        prove=(
            Prova(f"{PIANIFICATI}/ux-designs/ux-Kirchhoff-2026-08-13/DESIGN.md",
                  "version: 3"),
            Prova(f"{PIANIFICATI}/ux-designs/ux-Kirchhoff-2026-08-13/EXPERIENCE.md",
                  "version: 3"),
        ),
        segnali=(
            Prova(f"{PIANIFICATI}/ux-designs/ux-Kirchhoff-2026-08-13/EXPERIENCE.md",
                  "alternativa testuale"),
        ),
    ),
    Passo(
        5, "05-spine", "Architecture Spine v2", "bmad-architecture (update)",
        prove=(
            Prova(f"{PIANIFICATI}/architecture/architecture-Kirchhoff-2026-08-13/"
                  "ARCHITECTURE-SPINE.md", "version: 2"),
            Prova(f"{PIANIFICATI}/architecture/architecture-Kirchhoff-2026-08-13/"
                  "ARCHITECTURE-SPINE.md", "LayoutPatch"),
        ),
        segnali=(
            Prova(f"{PIANIFICATI}/architecture/architecture-Kirchhoff-2026-08-13/"
                  "ARCHITECTURE-SPINE.md", "reroute_scope"),
            Prova(f"{PIANIFICATI}/architecture/architecture-Kirchhoff-2026-08-13/"
                  "ARCHITECTURE-SPINE.md", "ProofGraph"),
        ),
    ),
    Passo(
        6, "06-epiche", "Ribilanciamento epiche → Gate A–G",
        "bmad-create-epics-and-stories",
        prove=(
            Prova(f"{PIANIFICATI}/epics.md", "Gate A"),
            Prova(f"{PIANIFICATI}/epics.md", "Gate G"),
        ),
        segnali=(
            Prova(f"{PIANIFICATI}/epics.md", "Visual Proof Kernel"),
        ),
    ),
    Passo(
        7, "07-readiness", "Readiness gate", "bmad-sprint-planning (readiness)",
        prove=(
            Prova(f"{PIANIFICATI}/implementation-readiness.md", "version: 3"),
        ),
    ),
    # Le prove del passo 8 usano le sottostringhe nude, non i marcatori interi: la
    # colonna «Prova» stampa il testo cercato, e un marcatore stampato dentro la tabella
    # generata verrebbe riletto come fine del blocco al render successivo. Il difetto si
    # manifesta solo alla seconda esecuzione — `sostituisci_in_loop` lo blocca comunque.
    Passo(
        8, "08-ship-loop", "Ship loop", ".claude/loop.md",
        prove=(
            Prova(".claude/loop.md", "BMAD-CHAIN:START"),
            Prova(".claude/loop.md", "BMAD-CHAIN:END"),
        ),
    ),
)


def passo_per_riferimento(riferimento: str) -> Passo:
    """Accetta il numero (`3`) o la chiave (`03-prd`). Un riferimento sbagliato è un errore."""
    for p in CATENA:
        if riferimento == p.chiave or riferimento == str(p.numero):
            return p
    chiavi = ", ".join(f"{p.numero}={p.chiave}" for p in CATENA)
    raise KeyError(f"passo sconosciuto: {riferimento!r}. Passi: {chiavi}")


# ── stato su disco ──────────────────────────────────────────────────────────────


def _adesso() -> str:
    return datetime.now().strftime("%m-%d-%Y %H:%M")


def stato_vuoto(data: str | None = None) -> dict:
    quando = data or _adesso()
    return {
        "schema": SCHEMA,
        "project": "Kirchhoff",
        "chain": "correct-course chain-top v3",
        "source": "docs/inbox/kirchhoff_01_piano_master_v3.md §25.1",
        "generated": quando,
        "last_updated": quando,
        "steps": {
            p.chiave: {"status": "backlog", "at": None, "note": None} for p in CATENA
        },
    }


def carica_stato(percorso: Path = FILE_STATO, data: str | None = None) -> dict:
    """Legge lo stato, e ricostruisce le voci mancanti invece di esplodere.

    Un passo aggiunto a `CATENA` dopo la creazione del file deve comparire come
    `backlog`, non far fallire ogni comando successivo.
    """
    if not percorso.exists():
        return stato_vuoto(data)
    dati = json.loads(percorso.read_text(encoding="utf-8"))
    if dati.get("schema") != SCHEMA:
        raise ValueError(
            f"{percorso}: schema {dati.get('schema')!r}, atteso {SCHEMA!r}")
    voci = dati.setdefault("steps", {})
    for p in CATENA:
        voci.setdefault(p.chiave, {"status": "backlog", "at": None, "note": None})
    return dati


def salva_stato(dati: dict, percorso: Path = FILE_STATO, data: str | None = None) -> None:
    """Scrittura atomica: un'interruzione non lascia un file di stato mezzo scritto."""
    dati["last_updated"] = data or _adesso()
    percorso.parent.mkdir(parents=True, exist_ok=True)
    testo = json.dumps(dati, indent=2, ensure_ascii=False) + "\n"
    fd, tmp = tempfile.mkstemp(dir=percorso.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(testo)
        os.replace(tmp, percorso)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


# ── confronto fra dichiarato e provato ──────────────────────────────────────────


@dataclass(frozen=True)
class Deriva:
    passo: Passo
    genere: str  # "fatto-non-tracciato" | "dichiarato-senza-prova"
    dichiarato: str
    mancanti: tuple[str, ...] = ()

    def descrivi(self) -> str:
        testa = f"passo {self.passo.numero} ({self.passo.chiave}) — {self.passo.titolo}"
        if self.genere == "fatto-non-tracciato":
            return (f"{testa}: le prove sono sul disco ma lo stato dichiarato è "
                    f"'{self.dichiarato}'. Il lavoro è fatto e non tracciato — "
                    f"registralo, non rifarlo.")
        elenco = "; ".join(self.mancanti)
        return (f"{testa}: dichiarato '{self.dichiarato}' senza prova. Manca: {elenco}")


def derive(stato: dict, radice: Path = RADICE) -> list[Deriva]:
    """Le divergenze fra ciò che il file dichiara e ciò che il disco dimostra."""
    fuori = []
    for p in CATENA:
        voce = stato["steps"][p.chiave]
        dichiarato = voce.get("status", "backlog")
        provato = p.prove_soddisfatte(radice)
        forzato = bool(voce.get("forced"))
        if dichiarato == "done" and not provato and not forzato:
            fuori.append(Deriva(
                p, "dichiarato-senza-prova", dichiarato,
                tuple(pr.descrivi() for pr in p.prove_mancanti(radice))))
        elif dichiarato != "done" and provato:
            fuori.append(Deriva(p, "fatto-non-tracciato", dichiarato))
    return fuori


def prossimo(stato: dict, radice: Path = RADICE) -> Passo | None:
    """Il primo passo non chiuso. `None` quando la catena è completa."""
    for p in CATENA:
        if stato["steps"][p.chiave].get("status") != "done":
            return p
    return None


# ── rappresentazione ────────────────────────────────────────────────────────────


def _simbolo(voce: dict, provato: bool) -> str:
    stato = voce.get("status", "backlog")
    if stato == "done":
        return "⚠️" if not provato and voce.get("forced") else "✅"
    if stato == "in-progress":
        return "🔄"
    return "⬜"


def rendi_tabella(stato: dict, radice: Path = RADICE) -> str:
    """La tabella FASE 1, derivata. Il testo fra i marcatori di `loop.md`."""
    righe = [
        APERTURA,
        "<!-- generato da scripts/bmad_chain.py — non modificare a mano:"
        " `uv run python scripts/bmad_chain.py rendi` -->",
        "",
        "| # | Passo | Skill | Stato | Prova |",
        "|---|---|---|---|---|",
    ]
    for p in CATENA:
        voce = stato["steps"][p.chiave]
        provato = p.prove_soddisfatte(radice)
        quando = voce.get("at") or ""
        nota = voce.get("note") or ""
        etichetta = " · ".join(x for x in (quando, nota) if x)
        prova = "; ".join(pr.percorso.rsplit("/", 1)[-1] + f" «{pr.contiene}»"
                          for pr in p.prove)
        righe.append(
            f"| {p.numero} | {p.titolo} | `{p.skill}` | "
            f"{_simbolo(voce, provato)} {etichetta} | {'✓' if provato else '—'} "
            f"{prova} |")
    righe += ["", f"<!-- aggiornata: {stato.get('last_updated', '?')} -->", CHIUSURA]
    return "\n".join(righe)


def sostituisci_in_loop(testo: str, tabella: str) -> str:
    """Sostituisce il blocco fra i marcatori. Marcatori assenti = errore, non append.

    Appendere in fondo produrrebbe due tabelle e nessun avviso: esattamente il modo in
    cui uno stato torna a divergere.

    La tabella generata non può contenere i marcatori: se li contenesse, il render
    successivo li leggerebbe come confine del blocco e troncherebbe il file. È già
    successo — il passo 8 ha per prova l'esistenza dei marcatori, e la colonna «Prova»
    stampa il testo cercato. Un difetto che si vede solo alla seconda esecuzione, quindi
    va bloccato qui e non solo evitato a monte.
    """
    for marcatore, atteso in ((APERTURA, 1), (CHIUSURA, 1)):
        if tabella.count(marcatore) != atteso:
            raise ValueError(
                f"la tabella generata contiene {tabella.count(marcatore)} volte "
                f"{marcatore}, attese {atteso}: riscriverebbe il file storto")
    inizio = testo.find(APERTURA)
    fine = testo.find(CHIUSURA)
    if inizio == -1 or fine == -1 or fine < inizio:
        raise ValueError(
            f"marcatori {APERTURA} / {CHIUSURA} assenti o invertiti in loop.md")
    return testo[:inizio] + tabella + testo[fine + len(CHIUSURA):]


def rendi_file_loop(stato: dict, percorso: Path = FILE_LOOP,
                    radice: Path = RADICE) -> bool:
    """Riscrive la tabella nel file. `True` se il contenuto è cambiato."""
    testo = percorso.read_text(encoding="utf-8")
    nuovo = sostituisci_in_loop(testo, rendi_tabella(stato, radice))
    if nuovo == testo:
        return False
    percorso.write_text(nuovo, encoding="utf-8")
    return True


# ── comandi ─────────────────────────────────────────────────────────────────────


def _stampa_riepilogo(stato: dict, radice: Path) -> None:
    print(f"Catena BMAD v3 — {stato['source']}")
    print(f"aggiornata: {stato.get('last_updated', '?')}\n")
    for p in CATENA:
        voce = stato["steps"][p.chiave]
        provato = p.prove_soddisfatte(radice)
        n = len(p.prove)
        ok = n - len(p.prove_mancanti(radice))
        print(f"  {_simbolo(voce, provato)} {p.numero} {p.chiave:<16} "
              f"{voce.get('status', 'backlog'):<12} prove {ok}/{n}")
        for s in p.segnali_mancanti(radice):
            if voce.get("status") == "done":
                print(f"      · segnale assente: {s.descrivi()}")


def comando_verifica(args) -> int:
    radice = Path(args.radice).resolve()
    stato = carica_stato(Path(args.file_stato))
    _stampa_riepilogo(stato, radice)
    fuori = derive(stato, radice)
    codice = 0
    if fuori:
        print("\nDIVERGENZE:")
        for d in fuori:
            print(f"  ✗ {d.descrivi()}")
        codice = 1
    if args.con_loop:
        testo = Path(args.file_loop).read_text(encoding="utf-8")
        atteso = sostituisci_in_loop(testo, rendi_tabella(stato, radice))
        if atteso != testo:
            print(f"\n  ✗ {args.file_loop}: la tabella FASE 1 non corrisponde allo "
                  f"stato. Esegui `rendi`.")
            codice = 1
    if codice == 0:
        p = prossimo(stato, radice)
        print("\n  catena coerente. " +
              (f"prossimo: passo {p.numero} — {p.titolo} ({p.skill})"
               if p else "catena chiusa: si passa a FASE 2, Gate A."))
    return codice


def comando_segna(args) -> int:
    radice = Path(args.radice).resolve()
    passo = passo_per_riferimento(args.passo)
    if args.stato not in STATI:
        print(f"stato sconosciuto: {args.stato!r}. Ammessi: {', '.join(STATI)}",
              file=sys.stderr)
        return 2
    stato = carica_stato(Path(args.file_stato))
    mancanti = passo.prove_mancanti(radice)
    if args.stato == "done" and mancanti and not args.forza:
        print(f"rifiuto: passo {passo.numero} ({passo.chiave}) non ha le prove.",
              file=sys.stderr)
        for m in mancanti:
            print(f"  manca: {m.descrivi()}", file=sys.stderr)
        print("  produci l'artefatto, oppure `--forza --motivo \"...\"` e resta a "
              "vista nella tabella.", file=sys.stderr)
        return 1
    if args.forza and args.stato == "done" and mancanti and not args.motivo:
        print("`--forza` richiede `--motivo`.", file=sys.stderr)
        return 2

    voce = stato["steps"][passo.chiave]
    voce["status"] = args.stato
    voce["at"] = args.data or _adesso()
    if args.nota is not None:
        voce["note"] = args.nota
    if args.stato == "done" and mancanti and args.forza:
        voce["forced"] = True
        voce["reason"] = args.motivo
    else:
        voce.pop("forced", None)
        voce.pop("reason", None)
    salva_stato(stato, Path(args.file_stato), args.data)
    print(f"passo {passo.numero} ({passo.chiave}) → {args.stato}")

    if not args.senza_rendi:
        cambiato = rendi_file_loop(stato, Path(args.file_loop), radice)
        print(f"  loop.md: {'tabella riscritta' if cambiato else 'già allineata'}")
    return 0


def comando_rendi(args) -> int:
    radice = Path(args.radice).resolve()
    stato = carica_stato(Path(args.file_stato))
    percorso = Path(args.file_loop)
    if args.controlla:
        testo = percorso.read_text(encoding="utf-8")
        if sostituisci_in_loop(testo, rendi_tabella(stato, radice)) != testo:
            print(f"{percorso}: tabella FASE 1 non allineata allo stato.",
                  file=sys.stderr)
            return 1
        print(f"{percorso}: allineata.")
        return 0
    cambiato = rendi_file_loop(stato, percorso, radice)
    print(f"{percorso}: {'riscritta' if cambiato else 'già allineata'}")
    return 0


def comando_stato(args) -> int:
    radice = Path(args.radice).resolve()
    stato = carica_stato(Path(args.file_stato))
    if args.json:
        print(json.dumps(stato, indent=2, ensure_ascii=False))
        return 0
    _stampa_riepilogo(stato, radice)
    return 0


def comando_inizializza(args) -> int:
    """Crea il file di stato deducendo lo stato iniziale dalle prove sul disco."""
    radice = Path(args.radice).resolve()
    percorso = Path(args.file_stato)
    if percorso.exists() and not args.forza:
        print(f"{percorso} esiste già. `--forza` per riscriverlo.", file=sys.stderr)
        return 1
    stato = stato_vuoto(args.data)
    for p in CATENA:
        if p.prove_soddisfatte(radice):
            stato["steps"][p.chiave].update(
                {"status": "done", "at": args.data or _adesso(),
                 "note": "dedotto dalle prove su disco"})
    salva_stato(stato, percorso, args.data)
    print(f"{percorso}: creato.")
    _stampa_riepilogo(stato, radice)
    return 0


def costruisci_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="bmad_chain.py",
        description="Stato della catena BMAD v3, derivato dalle prove su disco.")
    p.add_argument("--radice", default=str(RADICE))
    p.add_argument("--file-stato", default=str(FILE_STATO))
    p.add_argument("--file-loop", default=str(FILE_LOOP))
    p.add_argument("--data", default=None, help="MM-DD-YYYY HH:MM; default adesso")
    sub = p.add_subparsers(dest="comando", required=True)

    v = sub.add_parser("verifica", help="dichiarato vs provato; esce 1 se divergono")
    v.add_argument("--con-loop", action="store_true",
                   help="controlla anche che la tabella di loop.md sia allineata")
    v.set_defaults(fn=comando_verifica)

    s = sub.add_parser("segna", help="cambia lo stato di un passo e rigenera la tabella")
    s.add_argument("--passo", required=True, help="numero o chiave")
    s.add_argument("--stato", required=True, choices=STATI)
    s.add_argument("--nota", default=None)
    s.add_argument("--forza", action="store_true")
    s.add_argument("--motivo", default=None)
    s.add_argument("--senza-rendi", action="store_true")
    s.set_defaults(fn=comando_segna)

    r = sub.add_parser("rendi", help="riscrive la tabella FASE 1 in loop.md")
    r.add_argument("--controlla", action="store_true",
                   help="non scrive: esce 1 se la tabella è disallineata")
    r.set_defaults(fn=comando_rendi)

    t = sub.add_parser("stato", help="riepilogo leggibile")
    t.add_argument("--json", action="store_true")
    t.set_defaults(fn=comando_stato)

    i = sub.add_parser("inizializza", help="crea il file di stato dalle prove su disco")
    i.add_argument("--forza", action="store_true")
    i.set_defaults(fn=comando_inizializza)
    return p


def main(argv: list[str] | None = None) -> int:
    args = costruisci_parser().parse_args(argv)
    try:
        return args.fn(args)
    except (KeyError, ValueError, FileNotFoundError) as e:
        print(f"errore: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
