"""Configurazione: da ambiente, validata all'avvio, senza ripieghi silenziosi.

Una configurazione non valida **impedisce l'avvio**. Non degrada, non assume, non
sceglie un default ragionevole: nomina la variabile e dice cosa si aspettava.

Il valore vero di questo modulo non è avere una configurazione — è che tre vincoli
che finora vivevano solo nella prosa del piano diventino qui condizioni di avvio:

    K >= 3 passi di estrazione   D4, AD-12   l'ambiguità si misura come disaccordo
                                             fra almeno tre letture indipendenti,
                                             o non si misura affatto
    immagini <= 72 ore           FR-30       il termine è un obbligo, non una
                                             preferenza
    dati in Unione Europea       NFR-14      residenza dei dati e degli artefatti

Un vincolo scritto e non imposto dura quanto l'attenzione di chi scrive: è la
lezione R1 della retrospettiva di Epic 1, e questo modulo è la sua applicazione.

Sta fuori da `domain/` perché legge l'ambiente, che è I/O.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

#: Ambienti ammessi. Chiuso: un nome non previsto è un errore di deploy.
ENVIRONMENTS = ("dev", "staging", "prod")

#: Prefisso delle regioni dell'Unione Europea (NFR-14).
EU_REGION_PREFIX = "eu-"

#: Limite inferiore dei Pass di estrazione, imposto dal codice (AD-12, D4).
MIN_EXTRACTION_PASSES = 3

#: Vita massima di un'immagine caricata, in ore (FR-30, AD-9).
MAX_IMAGE_TTL_HOURS = 72


class ConfigError(RuntimeError):
    """Configurazione non valida. L'avvio si ferma qui."""


#: Nome della variabile d'ambiente da cui viene ogni campo. Serve perché un errore
#: nomini ciò che l'operatore deve cambiare, non il campo interno.
VARIABILE = {
    "env": "KIRCHHOFF_ENV",
    "data_region": "KIRCHHOFF_DATA_REGION",
    "extraction_passes": "KIRCHHOFF_EXTRACTION_PASSES",
    "image_ttl_hours": "KIRCHHOFF_IMAGE_TTL_HOURS",
}


@dataclass(frozen=True, slots=True)
class Settings:
    """Configurazione valida per costruzione.

    Le soglie stanno qui e non nel lettore: `K >= 3` è «imposto dal codice» (AD-12),
    e un limite che vive in un solo percorso di caricamento si aggira costruendo il
    tipo a mano. Nessuna istanza di `Settings` può contenere un valore illegale.
    """

    env: str
    data_region: str
    extraction_passes: int
    image_ttl_hours: int

    def __post_init__(self) -> None:
        if self.env not in ENVIRONMENTS:
            raise ConfigError(
                f"{VARIABILE['env']}: {self.env!r} non è un ambiente previsto. "
                f"Attesi: {', '.join(ENVIRONMENTS)}.")
        if not self.data_region.startswith(EU_REGION_PREFIX):
            raise ConfigError(
                f"{VARIABILE['data_region']}: {self.data_region!r} è fuori dall'Unione "
                "Europea. Dati e artefatti risiedono in UE (NFR-14): serve una regione "
                f"con prefisso {EU_REGION_PREFIX!r}.")
        if self.extraction_passes < MIN_EXTRACTION_PASSES:
            raise ConfigError(
                f"{VARIABILE['extraction_passes']}: {self.extraction_passes}, ma ne servono "
                f"almeno {MIN_EXTRACTION_PASSES}. L'ambiguità si misura come disaccordo fra "
                "letture indipendenti: sotto tre non c'è disaccordo da misurare, "
                "c'è un'opinione.")
        if self.image_ttl_hours <= 0:
            raise ConfigError(
                f"{VARIABILE['image_ttl_hours']}: {self.image_ttl_hours}, deve essere positivo.")
        if self.image_ttl_hours > MAX_IMAGE_TTL_HOURS:
            raise ConfigError(
                f"{VARIABILE['image_ttl_hours']}: {self.image_ttl_hours}, oltre il limite di "
                f"{MAX_IMAGE_TTL_HOURS} ore imposto dalla cancellazione automatica (FR-30).")


def _obbligatoria(env: Mapping[str, str], nome: str) -> str:
    valore = env.get(nome)
    if not valore:
        raise ConfigError(
            f"{nome}: variabile obbligatoria assente. Non esiste un valore di ripiego: "
            "una configurazione incompleta ferma l'avvio invece di indovinare.")
    return valore


def _intero(nome: str, grezzo: str) -> int:
    try:
        return int(grezzo)
    except ValueError:
        raise ConfigError(f"{nome}: atteso un intero, trovato {grezzo!r}") from None


def load_settings(env: Mapping[str, str]) -> Settings:
    """Legge l'ambiente, converte, e lascia al tipo il compito di rifiutare.

    Qui vive solo ciò che l'ambiente aggiunge: presenza e forma testuale. Le soglie
    stanno in `Settings`, dove nessuno può scavalcarle.
    """
    return Settings(
        env=_obbligatoria(env, VARIABILE["env"]),
        data_region=_obbligatoria(env, VARIABILE["data_region"]),
        extraction_passes=_intero(VARIABILE["extraction_passes"],
                                  _obbligatoria(env, VARIABILE["extraction_passes"])),
        image_ttl_hours=_intero(VARIABILE["image_ttl_hours"],
                                _obbligatoria(env, VARIABILE["image_ttl_hours"])),
    )


def from_environment() -> Settings:
    """Il percorso d'avvio vero: legge `os.environ` e valida."""
    return load_settings(os.environ)
