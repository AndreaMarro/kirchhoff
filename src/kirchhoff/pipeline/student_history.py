"""Cronologia applicativa di input StudentTrace, mai diagnosi importate."""
from hashlib import sha256
import json
import re

from kirchhoff.pipeline.student_trace import diagnose_payload

MAX_TRACE_ATTEMPTS = 32
MAX_TRACE_HISTORY_BYTES = 2_500_000
_OPERATIONS = {'serie', 'parallelo', 'kcl', 'kvl', 'corrente', 'tensione', 'ohm-tensione', 'altro'}


def recheck_history(netlist: str, attempts: list) -> list:
    """Valida l'intero inventario prima di ricalcolarne gli esiti canonici."""
    fingerprint = sha256(netlist.encode()).hexdigest()
    invalid = ValueError('La cronologia contiene un tentativo non valido o supera 32 controlli.')
    if not isinstance(attempts, list) or len(attempts) > MAX_TRACE_ATTEMPTS:
        raise invalid
    for attempt in attempts:
        if (not isinstance(attempt, dict) or set(attempt) != {'steps', 'engineRevision', 'circuitFingerprint'}
                or not isinstance(attempt['engineRevision'], str)
                or not re.fullmatch('[a-f0-9]{40}', attempt['engineRevision'])
                or attempt['circuitFingerprint'] != fingerprint
                or not isinstance(attempt['steps'], list) or not 1 <= len(attempt['steps']) <= 32):
            raise invalid
        for step in attempt['steps']:
            if (not isinstance(step, dict)
                    or set(step) != {'transcription', 'operation', 'first', 'second', 'claimed_value', 'reading'}
                    or not all(isinstance(step[k], str) and len(step[k]) <= 500
                               for k in ('transcription', 'operation', 'first', 'second', 'reading'))
                    or step['operation'] not in _OPERATIONS or step['reading'] not in {'clear', 'ambiguous', 'unreadable'}
                    or not (step['claimed_value'] is None or isinstance(step['claimed_value'], str) and len(step['claimed_value']) <= 100)):
                raise invalid
    if len(json.dumps(attempts, ensure_ascii=False, separators=(',', ':')).encode('utf-8')) > MAX_TRACE_HISTORY_BYTES:
        raise ValueError('La cronologia supera 2,5 MB: nessun tentativo viene sovrascritto.')
    return [{**attempt, 'diagnosis': diagnose_payload(netlist, dict(
        schema='student-trace.v1', circuit_fingerprint=fingerprint, steps=attempt['steps']))}
        for attempt in attempts]
