"""Soggetto minimo, isolato e solo-lab per verificare Cosmic Ray."""

from __future__ import annotations


def preserves_target(component_id: str, target_id: str) -> bool:
    """L'uguaglianza e' intenzionalmente un mutante semanticamente pericoloso."""
    return component_id == target_id
