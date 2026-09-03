"""Legame autorevole CircuitIR <-> StateRef, al confine applicativo.

Un ``proof_node`` nomina un'esecuzione, non uno stato: ``CertifiedDidacticRun``
consuma un ``ir_`` per esecuzione e non distingue il prima dal dopo di una
trasformazione. Questo modulo introduce il legame esplicito e validato che
mancava, senza toccare il dominio.

Decisioni documentate:

- I ref riusano il genere ``ir_``: il vocabolario di ``domain/identity`` e'
  chiuso e lo stato circuitale e' gia' un ``ir_`` per ``ProofNode``. Nessun
  nuovo genere, nessuna seconda maniera di coniare.
- I ref nominano occorrenze, non contenuti — come ``patch_`` nomina un passo.
  Un ref duplicato fallisce sempre, anche sullo stesso identico IR: e' la
  stessa regola append-only di ``LayoutStore`` e ``ProofGraph``, e nasconderebbe
  un conio doppio. La ripetizione non e' mai idempotente silenziosa.
- Valori canonici distinti non condividono mai un ref. Il ``TransformExecution``
  distingue ``after`` letterale (senza Request rilegate) dallo stato operativo
  dopo ``_bind_successor_request``: questo registro li lega entrambi, ciascuno
  col proprio ref, cosi' lo stato omesso dal passo resta identificabile.
- Il registro e' immutabile e senza orologio: i ref li fornisce il chiamante
  (coniati con ``conia`` a entropia/istante iniettati), la costruzione congela
  gli ingressi mutabili, la risoluzione e' una scansione — non una seconda
  mappa da tenere allineata, come ``ProofGraph.nodo_di``.
- Le violazioni di invariante sollevano (``ValueError``/``KeyError``/
  ``TypeError``) e non diventano mai ``Refusal``: un legame corrotto e' un
  difetto applicativo, e sara' il compositore a mapparlo su ``Failure``.
  ``Refusal`` resta per la semantica utente, non per i legami interni.
"""

from __future__ import annotations

from dataclasses import dataclass

from kirchhoff.domain.identity import verifica
from kirchhoff.domain.ir import IR

__all__ = ["CircuitStateRegistry", "StateBinding", "StateRef"]


@dataclass(frozen=True, slots=True)
class StateRef:
    """Riferimento tipizzato a uno stato circuitale. Genere ``ir_`` verificato."""

    identifier: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "identifier", verifica(self.identifier, "ir"))


@dataclass(frozen=True, slots=True)
class StateBinding:
    """Un ref legato esplicitamente al suo CircuitIR. Immutabile."""

    ref: StateRef
    state: IR

    def __post_init__(self) -> None:
        if not isinstance(self.ref, StateRef):
            raise TypeError(
                f"legame con {type(self.ref).__name__} invece di StateRef")
        if not isinstance(self.state, IR):
            raise TypeError(
                f"legame con {type(self.state).__name__} invece di IR")


@dataclass(frozen=True, slots=True)
class CircuitStateRegistry:
    """I legami di una traccia di prova. Immutabile, append-only per costruzione.

    Un ref risolve esattamente un CircuitIR; due valori distinti non
    condividono mai un ref; un ref duplicato fallisce esplicitamente.
    """

    bindings: tuple[StateBinding, ...] = ()

    def __post_init__(self) -> None:
        # Congela gli ingressi: una lista del chiamante non deve poter mutare
        # il registro dopo che le guardie sono passate.
        object.__setattr__(self, "bindings", tuple(self.bindings))
        visti: set[StateRef] = set()
        for binding in self.bindings:
            if not isinstance(binding, StateBinding):
                raise TypeError(
                    f"{type(binding).__name__} fra i legami invece di StateBinding")
            if binding.ref in visti:
                raise ValueError(
                    f"{binding.ref.identifier} e' gia' legato in questo registro: "
                    "un ref nomina un'occorrenza, non un contenuto, e non si rilega.")
            visti.add(binding.ref)

    def resolve(self, ref: StateRef) -> IR:
        """Il CircuitIR legato a quel ref, o ``KeyError`` esplicito."""
        if not isinstance(ref, StateRef):
            raise TypeError(
                f"risoluzione di {type(ref).__name__} invece di StateRef: "
                "solo un ref tipizzato e verificato risolve uno stato.")
        for binding in self.bindings:
            if binding.ref == ref:
                return binding.state
        raise KeyError(
            f"{ref.identifier!r} non e' legato in questo registro. "
            f"Legati: {', '.join(b.ref.identifier for b in self.bindings) or 'nessuno'}."
        )

    def con_binding(self, binding: StateBinding) -> CircuitStateRegistry:
        """Il registro esteso di un legame. Restituisce, non modifica."""
        if not isinstance(binding, StateBinding):
            raise TypeError(
                f"estensione con {type(binding).__name__} invece di StateBinding")
        if binding.ref in self:
            raise ValueError(
                f"{binding.ref.identifier} e' gia' legato in questo registro: "
                "un ref nomina un'occorrenza, non un contenuto, e non si rilega.")
        return CircuitStateRegistry((*self.bindings, binding))

    def refs(self) -> tuple[StateRef, ...]:
        """I ref legati, in ordine di legame."""
        return tuple(binding.ref for binding in self.bindings)

    def __contains__(self, ref: object) -> bool:
        return any(binding.ref == ref for binding in self.bindings)

    def __len__(self) -> int:
        return len(self.bindings)
