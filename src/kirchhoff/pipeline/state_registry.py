"""Legame canonico CircuitIR <-> StateRef, al confine applicativo.

Un ``proof_node`` nomina lo stato circuitale consumato da un'esecuzione,
cioe' un nodo del ``ProofGraph``, non un'esecuzione: AD-29 definisce i nodi
come stati circuitali e ``ProofNode.identifier`` e' l'``ir_`` dello stato;
``orchestrate`` assegna un identificatore per stato operativo distinto
(``state_ids``) prima di eseguirlo; il Claim P1-K ancora quello stesso
identificatore come ``state_id``. Questo modulo registra quel legame, senza
toccare il dominio.

Decisioni documentate:

- I ref riusano il genere ``ir_``: il vocabolario di ``domain/identity`` e'
  chiuso e lo stato circuitale e' gia' un ``ir_`` per ``ProofNode``. Nessun
  nuovo genere, nessuna seconda maniera di coniare.
- Il registro e' canonico, non un diario di occorrenze: un valore IR ha un
  solo ref e un ref un solo valore, in un registro. Come ``ProofGraph``
  rifiuta due nodi sullo stesso identificatore, qui un secondo ref sullo
  stesso valore fallisce esplicitamente: nasconderebbe un conio doppio, e
  non sarebbe la relazione autorevole CircuitIR <-> state-id che la
  sessione di prova richiede. La ripetizione non e' mai idempotente
  silenziosa.
- L'identita' di stato e' il valore IR intero, Request incluse: nessun
  ridisegno dell'IR, nessun secondo criterio. Gli stati operativi di una run
  sono comunque a due a due distinti (ogni trasformazione riduce
  strettamente i componenti), quindi la mappa e' biiettiva in pratica oltre
  che per costruzione.
- Il ``TransformExecution.after`` letterale e' il prodotto intermedio
  certificato, non uno stato della timeline: con un retarget differisce
  dallo stato operativo per le Request rilegate. Resta identificabile come
  evidenza esplicita col proprio ref quando il valore differisce; quando
  coincide (effetto identity) condivide il ref dello stato operativo, per
  canonicita'. Nessun arco fittizio per la rilegatura: gli archi sono
  ``Transform`` (AD-29).
- La proiezione ``componi_registro`` deriva solo da dati pubblici immutabili
  della run (``before`` di ogni esecuzione, ``final_ir``, ``state_ids``):
  mai da helper privati del dominio. Per continuita' — validata dal dominio
  stesso — il ``before`` successivo e' lo stato operativo dopo il passo.
- Il registro e' immutabile e senza orologio: i ref li fornisce il chiamante
  (coniati con ``conia`` a entropia/istante iniettati), la costruzione congela
  gli ingressi mutabili, la risoluzione e la ricerca inversa sono scansioni —
  non seconde mappe da tenere allineate, come ``ProofGraph.nodo_di``.
- Le violazioni di invariante sollevano (``ValueError``/``KeyError``/
  ``TypeError``) e non diventano mai ``Refusal``: un legame corrotto e' un
  difetto applicativo, e sara' il compositore a mapparlo su ``Failure``.
  ``Refusal`` resta per la semantica utente, non per i legami interni.
"""

from __future__ import annotations

from dataclasses import dataclass

from kirchhoff.domain.didactic.orchestrate import CertifiedDidacticRun
from kirchhoff.domain.identity import verifica
from kirchhoff.domain.ir import IR

__all__ = [
    "CircuitStateRegistry",
    "StateBinding",
    "StateRef",
    "componi_registro",
    "stati_operativi",
]


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
    """I legami canonici di una traccia di prova. Immutabile.

    Un ref risolve esattamente un CircuitIR; un valore ha un solo ref:
    un secondo legame sullo stesso ref o sullo stesso valore fallisce
    esplicitamente.
    """

    bindings: tuple[StateBinding, ...] = ()

    def __post_init__(self) -> None:
        # Congela gli ingressi: una lista del chiamante non deve poter mutare
        # il registro dopo che le guardie sono passate.
        object.__setattr__(self, "bindings", tuple(self.bindings))
        for index, binding in enumerate(self.bindings):
            if not isinstance(binding, StateBinding):
                raise TypeError(
                    f"{type(binding).__name__} fra i legami invece di StateBinding")
            for precedente in self.bindings[:index]:
                if precedente.ref == binding.ref:
                    raise ValueError(
                        f"{binding.ref.identifier} e' gia' legato in questo "
                        "registro: un ref nomina uno stato canonico e non si "
                        "rilega.")
                if precedente.state == binding.state:
                    raise ValueError(
                        f"{binding.ref.identifier} rilega il valore gia' legato "
                        f"a {precedente.ref.identifier}: un valore canonico ha "
                        "un solo ref in questo registro, come un ProofGraph "
                        "non ha due nodi sullo stesso stato.")

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

    def ref_for(self, state: IR) -> StateRef:
        """Il ref legato a quel valore IR, o ``KeyError`` esplicito.

        La direzione inversa del legame canonico: un valore, un ref.
        """
        if not isinstance(state, IR):
            raise TypeError(
                f"ricerca di {type(state).__name__} invece di IR: il registro "
                "canonico indicizza valori CircuitIR.")
        for binding in self.bindings:
            if binding.state == state:
                return binding.ref
        raise KeyError(
            "nessun ref legato a questo stato in questo registro. "
            f"Legati: {', '.join(b.ref.identifier for b in self.bindings) or 'nessuno'}."
        )

    def con_binding(self, binding: StateBinding) -> CircuitStateRegistry:
        """Il registro esteso di un legame. Restituisce, non modifica."""
        if not isinstance(binding, StateBinding):
            raise TypeError(
                f"estensione con {type(binding).__name__} invece di StateBinding")
        for precedente in self.bindings:
            if precedente.ref == binding.ref:
                raise ValueError(
                    f"{binding.ref.identifier} e' gia' legato in questo "
                    "registro: un ref nomina uno stato canonico e non si "
                    "rilega.")
            if precedente.state == binding.state:
                raise ValueError(
                    f"{binding.ref.identifier} rilega il valore gia' legato "
                    f"a {precedente.ref.identifier}: un valore canonico ha "
                    "un solo ref in questo registro, come un ProofGraph "
                    "non ha due nodi sullo stesso stato.")
        return CircuitStateRegistry((*self.bindings, binding))

    def refs(self) -> tuple[StateRef, ...]:
        """I ref legati, in ordine di legame."""
        return tuple(binding.ref for binding in self.bindings)

    def __contains__(self, ref: object) -> bool:
        return any(binding.ref == ref for binding in self.bindings)

    def __len__(self) -> int:
        return len(self.bindings)


def stati_operativi(run: CertifiedDidacticRun) -> tuple[IR, ...]:
    """Gli stati operativi della run, nell'ordine dei ``state_ids``.

    Solo dati pubblici immutabili: il ``before`` di ogni esecuzione e la
    ``final_ir``. Per continuita' — validata dal dominio in costruzione — il
    ``before`` i-esimo e' lo stato che ``state_ids[i]`` nomina, e la
    ``final_ir`` e' lo stato che l'ultimo nomina.
    """
    if not isinstance(run, CertifiedDidacticRun):
        raise TypeError(
            f"proiezione di {type(run).__name__} invece di CertifiedDidacticRun")
    return tuple(esecuzione.before for esecuzione in run.transform_executions) + (
        run.final_ir,
    )


def componi_registro(
    run: CertifiedDidacticRun,
    refs_evidenza: tuple[StateRef, ...] = (),
) -> CircuitStateRegistry:
    """Il registro canonico di una run certificata.

    Lega ogni stato operativo al ``state_id`` che la run gli assegna, e ogni
    dopo letterale che differisce dagli stati operativi a un ref di evidenza
    fornito dal chiamante (il letterale coincidente condivide il ref per
    canonicita'). La fornitura puo' essere sovradimensionata: gli
    identificatori non consumati non entrano nel registro.
    """
    stati = stati_operativi(run)
    evidenza = tuple(refs_evidenza)
    for ref in evidenza:
        if not isinstance(ref, StateRef):
            raise TypeError(
                f"evidenza con {type(ref).__name__} invece di StateRef")
    registro = CircuitStateRegistry()
    for sid, stato in zip(run.state_ids, stati, strict=True):
        registro = registro.con_binding(StateBinding(StateRef(sid), stato))
    usate = 0
    for esecuzione in run.transform_executions:
        try:
            registro.ref_for(esecuzione.after)
        except KeyError:
            if usate >= len(evidenza):
                raise ValueError(
                    "refs_evidenza insufficienti: il dopo letterale di un passo "
                    "differisce dallo stato operativo e non ha un ref.")
            registro = registro.con_binding(
                StateBinding(evidenza[usate], esecuzione.after))
            usate += 1
    return registro
