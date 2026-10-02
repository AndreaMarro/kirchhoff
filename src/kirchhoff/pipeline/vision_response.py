"""Contratto non fidato fra il modello visivo e l'anteprima correggibile.

Le regioni sono coordinate normalizzate 0–1000 nell'immagine inviata. La loro
presenza rende la lettura contestabile; non certifica che il modello abbia
visto tutti i componenti. Soltanto la revisione esplicita dell'utente può
inoltrare la netlist al nucleo elettrico.
"""
from __future__ import annotations

from json import JSONDecodeError, loads

MAX_NETLIST_CHARS = 16000
MAX_LINES = 64
MAX_UNCERTAINTIES = 32

_REGION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {name: {"type": "integer"} for name in ("x1", "y1", "x2", "y2")},
    "required": ["x1", "y1", "x2", "y2"],
}

VISION_SCHEMA = {
    "type": "json_schema",
    "name": "circuit_image_transcription_v1",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "netlist": {"type": "string"},
            "complete": {"type": "boolean"},
            "uncertainties": {"type": "array", "items": {"type": "string"}},
            "observations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "line": {"type": "string"},
                        "region": _REGION_SCHEMA,
                    },
                    "required": ["line", "region"],
                },
            },
        },
        "required": ["netlist", "complete", "uncertainties", "observations"],
    },
}


def parse_vision_response(response: object) -> dict:
    """Accetta solo un messaggio completo con provenienza per ogni riga.

    La validazione locale resta necessaria anche con Structured Outputs: una
    risposta interrotta o un provider incompatibile non diventa una lettura.
    """
    if not isinstance(response, dict) or response.get("status") != "completed":
        raise ValueError("Trascrizione interrotta: nessun circuito è stato acquisito.")
    output = response.get("output")
    if not isinstance(output, list):
        raise ValueError("Risposta del riconoscitore non interpretabile.")
    contents = []
    for item in output:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        if not isinstance(item.get("content"), list):
            raise ValueError("Risposta del riconoscitore non interpretabile.")
        contents.extend(content for content in item["content"] if isinstance(content, dict))
    if any(content.get("type") == "refusal" for content in contents):
        raise ValueError("Il riconoscitore ha rifiutato la lettura: ricostruisci il circuito manualmente.")
    texts = [content.get("text") for content in contents if content.get("type") == "output_text"]
    if len(texts) != 1 or not isinstance(texts[0], str):
        raise ValueError("Risposta multipla o assente: nessun circuito è stato acquisito.")
    try:
        data = loads(texts[0])
    except JSONDecodeError as exc:
        raise ValueError("Risposta JSON del riconoscitore non valida.") from exc
    if not isinstance(data, dict) or set(data) != {"netlist", "complete", "uncertainties", "observations"}:
        raise ValueError("Struttura della trascrizione non valida.")

    netlist = data["netlist"]
    if not isinstance(netlist, str) or not 0 < len(netlist) <= MAX_NETLIST_CHARS:
        raise ValueError("La trascrizione supera 16000 caratteri o è vuota: ritaglia la foto o correggi manualmente.")
    lines = netlist.splitlines()
    if not lines or len(lines) > MAX_LINES or any(not line.strip() for line in lines):
        raise ValueError("Le righe del circuito non sono interpretabili: controlla la foto e correggi manualmente.")
    complete = data["complete"]
    uncertainties = data["uncertainties"]
    if type(complete) is not bool or not isinstance(uncertainties, list) or len(uncertainties) > MAX_UNCERTAINTIES or any(
        not isinstance(item, str) or not item.strip() or len(item) > 500 for item in uncertainties
    ):
        raise ValueError("Elenco dei dubbi del riconoscitore non valido.")
    if not complete and not uncertainties:
        raise ValueError("La lettura è incompleta ma non spiega i dubbi: ricostruisci manualmente.")
    if complete and uncertainties:
        raise ValueError("Lettura dichiarata completa ma con dubbi: controlla manualmente.")
    if complete and not lines[-1].lstrip().startswith("?"):
        raise ValueError("Lettura dichiarata completa senza domanda: controlla manualmente.")

    observations = data["observations"]
    if not isinstance(observations, list) or len(observations) != len(lines):
        raise ValueError("Manca la regione sorgente di una riga: ricostruisci manualmente.")
    for line, observation in zip(lines, observations):
        if not isinstance(observation, dict) or set(observation) != {"line", "region"} or observation["line"] != line:
            raise ValueError("Manca la regione sorgente di una riga: ricostruisci manualmente.")
        region = observation["region"]
        if not isinstance(region, dict) or set(region) != {"x1", "y1", "x2", "y2"} or any(
            type(value) is not int or not 0 <= value <= 1000 for value in region.values()
        ) or not region["x1"] < region["x2"] or not region["y1"] < region["y2"]:
            raise ValueError("La regione sorgente di una riga non è valida.")
    return {
        "netlist": netlist,
        "model_reported_complete": complete,
        "uncertainties": uncertainties,
        "observations": observations,
        "requires_confirmation": True,
    }
