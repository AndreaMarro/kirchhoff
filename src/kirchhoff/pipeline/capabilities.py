"""Capacità del percorso prodotto, distinte da quelle del kernel matematico.

Il risultato per un circuito passa dallo stesso ingresso di ``solve_circuit``:
una sintassi leggibile o un solver capace non implicano una lezione disponibile.
"""

from __future__ import annotations

from typing import Any

from kirchhoff.domain.didactic.capabilities import DIDACTIC_NODAL_COMPONENT_TYPES
from kirchhoff.pipeline.circuitikz import SCHEMA as CIRCUITIKZ_SCHEMA
from kirchhoff.pipeline.lesson import create_lesson
from kirchhoff.pipeline.lesson_ac import PHASOR_LESSON_TYPES
from kirchhoff.pipeline.spice import SCHEMA as SPICE_SCHEMA


SOLVE_DESCRIPTION = (
    "Risolve un circuito DC resistivo confermato con R/V/I indipendenti "
    "quando il percorso didattico e' applicabile, inclusa la resistenza vista "
    "fra due morsetti; serve anche tensioni/correnti fasoriali AC RLC con V/I "
    "indipendenti, pulsazione positiva e fasi multiple di 30 gradi, con confronto "
    "esatto fra MNA e tableau. Dopo @ac si può dichiarare @amplitude rms, peak "
    "o unspecified (predefinito). La richiesta ? power <componente> serve S, P e Q "
    "in convenzione passiva, con RMS o picco espliciti obbligatori. Restituisce un rifiuto "
    "negli altri casi; non interpreta fotografie. La richiesta ? impedance <p> <q> "
    "calcola l’impedenza AC fra due morsetti tramite corrente di prova, con le "
    "sorgenti indipendenti azzerate. Con @laplace serve V(s)/I(s) di RLC e sorgenti "
    "step/impulse esplicite; @initial dichiara ogni stato C/L, anche nullo. Le unità "
    "di un impulso sono volt*s o ampere*s. La risposta è una funzione razionale esatta."
)
SCOPE = (
    "Circuiti resistivi in continua con resistori e sorgenti indipendenti di "
    "tensione o corrente, quando esiste un percorso didattico applicabile. "
    "La resistenza di porta DC usa due sottoprove e un controllo indipendente. "
    "Le sorgenti controllate VCVS/VCCS sono accettate dal kernel, ma non "
    "hanno ancora una lezione. La lezione AC espone tensioni/correnti RLC e V/I "
    "indipendenti con confronto esatto dei due assemblaggi, senza Claim VERIFIED. "
    "La richiesta power espone potenza complessa, attiva e reattiva con convenzione passiva "
    "e bilancio esatto di tutti i rami. @amplitude rms oppure @amplitude peak dichiara la scala "
    "comune dei fasori ed è obbligatoria per la potenza; se omessa resta unspecified. "
    "L’impedenza di porta AC usa una corrente di prova e due assemblaggi esatti "
    "della rete a sorgenti indipendenti azzerate; richiede una soluzione originale "
    "e una prova uniche. Il rapporto tensione/corrente non richiede RMS o picco. "
    "Il percorso @laplace espone tensioni e correnti trasformate in reti RLC con sorgenti "
    "indipendenti step/impulse e condizioni iniziali C/L esplicite. Le operazioni algebriche "
    "sono confrontate con identità polinomiali indipendenti. Antitrasformata, sorgenti "
    "dipendenti e commutazione fra topologie non sono ancora esposte."
)


def product_capabilities(netlist: str | None = None, *, vision: bool = False) -> dict[str, Any]:
    """Contratto comune a HTTP, MCP e testo di ambito della UI.

    La disponibilità per una netlist viene misurata sul percorso servito e
    restituisce soltanto esito e metodi, senza spacciare il parser per un solver.
    """
    result: dict[str, Any] = dict(
        schema="kirchhoff-capabilities.v1",
        solve=True,
        scope=SCOPE,
        component_types=sorted(DIDACTIC_NODAL_COMPONENT_TYPES),
        controlled_sources=False,
        kernel_controlled_sources=["VCVS", "VCCS"],
        diagnosis="riduzioni R, KCL al nodo, KVL su maglia chiusa e valori DC di corrente/tensione sul circuito originale; le semplificazioni incerte non sono giudicate",
        spice=SPICE_SCHEMA,
        circuitikz=CIRCUITIKZ_SCHEMA,
        photo=vision,
        vision=vision,
        ac=True,
        ac_scope=dict(component_types=sorted(PHASOR_LESSON_TYPES),
                      quantities=['voltage', 'current', 'power', 'impedance'], methods=['auto', 'phasor', 'test_current'],
                      port_impedance=True, port_methods=['auto', 'test_current'],
                      angular_frequency_unit='rad/s', source_phase_step_degrees=30,
                      amplitude='unspecified', amplitude_default='unspecified',
                      amplitude_conventions=['rms', 'peak', 'unspecified'],
                      powers=True, power_amplitude_conventions=['rms', 'peak'],
                      power_sign='passive', certified_lesson=False),
        transients=True,
        laplace_scope=dict(component_types=["resistor", "capacitor", "inductor", "voltage_source", "current_source"],
                           quantities=["voltage", "current"], methods=["auto", "laplace"],
                           source_waveforms=["step", "impulse"], initial_conditions="explicit_all_C_L_at_0-",
                           response_domain="laplace", coefficient_order="ascending", exact_coefficients="rational",
                           response_units=["V*s", "A*s"], inverse_transform=False,
                           topology_switching=False, certified_lesson=False),
        product_verified=False,
    )
    if netlist is not None:
        try:
            lesson = create_lesson(netlist)
        except ValueError as exc:
            result["circuit"] = dict(outcome="invalid", available_methods=[], message=str(exc))
        else:
            result["circuit"] = dict(
                outcome=lesson["outcome"],
                available_methods=lesson.get("available", []),
                message=lesson.get("message"),
            )
    return result
