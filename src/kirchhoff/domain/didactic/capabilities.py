"""Capacità realmente eseguibili sul circuito corrente.

Quattro concetti distinti, e il planner interroga l'ultimo:

- nome nel catalogo
- tecnica permessa dal profilo (`SUPPORTED`)
- implementazione esistente (`engine.implemented`)
- azione applicabile *a questo* circuito

`partitore_di_tensione` è nel catalogo e in `SUPPORTED` ma non ha corpo: qui
non compare mai fra le riduzioni eseguibili.

Le guardie di serie/parallelo non vivono qui: la sola fonte è
`transform.applicability.enumerate_executable_transforms`.
"""

from __future__ import annotations

from ..ir import IR, REFERENCE_NODE
from ..refusal import Refusal
from ..transform.applicability import (
    ExecutableTransform,
    enumerate_executable_transforms,
)
from .analytical import (
    _generatori_verso_riferimento,
    _precondizioni_kcl_supernodo,
    _sorgenti_tensione_flottanti,
    nodi_dei_supernodi_semplici,
    nodi_kcl_ordinarie,
    supernodi_semplici,
)
from .observation import ObservationContract, ObservationEffect, observation_effect
from ..transform.engine import transform

#: Sottoinsieme per cui lo slice didattico sa davvero scrivere equazioni.
#: I generatori di corrente indipendenti entrano nel termine noto della
#: KCL. I supernodi semplici (una voltage_source_dc flottante a due nodi
#: unknown disgiunti) sono ammessi. Sorgenti controllate e catene no.
DIDACTIC_NODAL_COMPONENT_TYPES: frozenset[str] = frozenset({
    "resistor",
    "voltage_source_dc",
    "current_source_dc",
})

QUANTITA_NODALI: frozenset[str] = frozenset({"voltage", "current"})

RiduzioneEseguibile = ExecutableTransform


def riduzioni_eseguibili(ir: IR) -> tuple[RiduzioneEseguibile, ...]:
    """Le riduzioni con corpo *e* precondizioni soddisfatte su questo IR."""
    return enumerate_executable_transforms(ir)


def effetto_osservazione(
    ir: IR,
    riduzione: RiduzioneEseguibile,
    contract: ObservationContract,
) -> ObservationEffect:
    """Interroga la sola autorita' semantica su una riduzione eseguibile.

    L'esecuzione qui e' pura e serve a leggere il suo risultato certificato; non
    pianifica un percorso e non muta l'IR. Un rifiuto del prodotto non diventa una
    scorciatoia semantica: la riduzione non contribuisce.
    """
    outcome = transform(ir, riduzione.operation, *riduzione.operands)
    if isinstance(outcome, Refusal):
        return ObservationEffect(
            "blocked", None, "la riduzione eseguibile non produce un circuito valido")
    after, result = outcome
    return observation_effect(ir, after, result, riduzione.operation, contract)


def contribuisce(
    ir: IR,
    riduzione: RiduzioneEseguibile,
    contract: ObservationContract,
) -> bool:
    """Compatibilita': delega integralmente alla semantica osservativa P1-J."""
    return effetto_osservazione(ir, riduzione, contract).kind != "blocked"


def riduzioni_che_contribuiscono(
    ir: IR, contract: ObservationContract,
) -> tuple[RiduzioneEseguibile, ...]:
    return tuple(
        r for r in riduzioni_eseguibili(ir)
        if contribuisce(ir, r, contract)
    )


def _nodi_incogniti(ir: IR) -> tuple[str, ...]:
    """Nodi che `define_nodal_unknowns` dichiarerebbe `unknown`.

    Non è una seconda discovery delle KCL: è il complemento di
    riferimento e generatori verso massa, in ordine canonico.
    """
    fissi = _generatori_verso_riferimento(ir)
    return tuple(sorted(
        n for n in ir.nodes
        if n != REFERENCE_NODE and n not in fissi
    ))


def _copertura_nodale(ir: IR) -> bool:
    """Partizione: U = O ∪ S e ogni floating appartiene a un supernodo.

    La copertura vuota e' copertura: quando ogni nodo non di riferimento e'
    fissato da un generatore verso massa non servono equazioni e la
    derivazione prosegue con i soli noti (stato terminale, non irrisolvibile).
    """
    flottanti = {c.id for c in _sorgenti_tensione_flottanti(ir)}
    supernodi = supernodi_semplici(ir)
    if flottanti != {sn.source_id for sn in supernodi}:
        return False
    for sn in supernodi:
        try:
            _precondizioni_kcl_supernodo(ir, sn)
        except ValueError:
            return False
    U = set(_nodi_incogniti(ir))
    O = set(nodi_kcl_ordinarie(ir))
    S = set(nodi_dei_supernodi_semplici(ir))
    if U != O | S:
        return False
    return True


def nodale_disponibile(ir: IR, quantity: str) -> bool:
    """Vero solo se plan → azioni analitiche → equazioni esatte è eseguibile.

    Ogni unknown sta o su una KCL ordinaria o in esattamente un supernodo
    semplice supportato. Ogni voltage_source_dc flottante deve coincidere
    con un supernodo supportato: niente floating ignorate.
    """
    if ir.domain != "dc":
        return False
    if quantity not in QUANTITA_NODALI:
        return False
    if not ir.components:
        return False
    if not all(c.type in DIDACTIC_NODAL_COMPONENT_TYPES for c in ir.components):
        return False
    return _copertura_nodale(ir)
