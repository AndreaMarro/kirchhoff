"""Impedenza di porta: trasformazione esplicita e algebra della prova a 1 A.

La domanda resta una coppia di nodi del circuito originale. La sonda appartiene
soltanto al circuito generato; la sua tensione ha verso opposto alla tensione
di porta. I controlli elettrici e algebrici non creano una prova canonica.
"""
from dataclasses import replace
from fractions import Fraction as F
import hashlib

from kirchhoff.domain.exact import Cyc12
from kirchhoff.domain.ir import IR, PortRequest, Request
from kirchhoff.domain.port import _ac_probe, analyze_ac_port
from kirchhoff.domain.refusal import Refusal
from kirchhoff.pipeline.lesson_math import add, divide, equation, equation_text, expression_text, multiply, number, symbol
from kirchhoff.pipeline.lesson_svg import schematic


PORT_CHECKS = [
    'sorgenti indipendenti spente e corrente di prova orientata',
    'impedenza di porta: rapporto tensione/corrente',
    'misura di porta confrontata con il kernel',
]


def _check_probe(original: IR, measured: IR, port: tuple[str, str], probe_id: str) -> None:
    """Controlla la trasformazione senza chiamare il costruttore della sonda.

    Due solver sulla stessa trasformazione errata non bastano. Confrontiamo
    separatamente tutti i campi del circuito e il verso fisico della prova.
    """
    if (measured.domain != original.domain or measured.omega != original.omega
            or measured.nodes != original.nodes or measured.ir_version != original.ir_version
            or measured.source_kind != 'generated' or measured.requests
            or len(measured.components) != len(original.components)+1):
        raise ValueError('La trasformazione di porta ha cambiato regime, nodi o componenti.')
    by_id = {c.id: c for c in measured.components}
    original_ids = {c.id for c in original.components}
    if set(by_id) != original_ids | {probe_id} or probe_id in original_ids:
        raise ValueError('La sonda deve essere un componente nuovo e unico.')
    for before in original.components:
        after = by_id[before.id]
        source = before.type in {'voltage_source_ac', 'current_source_ac'}
        if (after.type != before.type or after.terminals != before.terminals
                or after.value.unit != before.value.unit or after.symbolic != before.symbolic
                or after.control_nodes != before.control_nodes or after.provenance is not None
                or after.value.amount != (F(0) if source else before.value.amount)
                or after.phase_steps != (0 if source else before.phase_steps)):
            raise ValueError(f'{before.id}: la trasformazione deve soltanto spegnere le sorgenti indipendenti.')
    probe = by_id[probe_id]
    if (probe.type != 'current_source_ac' or probe.terminals != (port[1], port[0])
            or probe.value.unit != 'ampere' or probe.value.amount != F(1)
            or probe.phase_steps != 0 or probe.control_nodes is not None
            or probe.provenance is not None or probe.symbolic != probe_id):
        raise ValueError('La corrente di prova deve essere esattamente 1 A, fase zero, dal secondo morsetto al primo.')


def _checked_ratio(probe_answer: dict, expected: Cyc12) -> Cyc12:
    """Il verso viene verificato sui coefficienti razionali, senza divisione AC.

    La sonda vale 1 A: Z = -V(sonda)/1. Controllare i quattro coefficienti
    evita che un errore condiviso in moltiplicazione o divisione nasconda il segno.
    """
    coefficients = probe_answer.get('phasor', {}).get('coefficients')
    if (probe_answer.get('unit') != 'V' or not isinstance(coefficients, list)
            or len(coefficients) != 4 or any(not isinstance(c, str) for c in coefficients)):
        raise ValueError('La sottoprova deve restituire una tensione fasoriale esatta in volt.')
    values = tuple(F(c) for c in coefficients)
    opposite = tuple(-c for c in values)
    if opposite != expected.c or probe_answer.get('math') != number(Cyc12(values)):
        raise ValueError('Il segno o il valore della tensione di prova non coincide con l’impedenza di porta.')
    return Cyc12(opposite)


def create_ac_port_lesson(text: str, ir: IR, req: PortRequest, method: str,
                          source_sha: str, amplitude: str) -> dict:
    from kirchhoff.pipeline.lesson import _checked_step, lesson_build
    from kirchhoff.pipeline.lesson_ac import PHASOR_LESSON_TYPES, create_phasor_lesson, phasor_view

    if method not in {'auto', 'test_current'}:
        raise ValueError('Per l’impedenza di porta seleziona Automatico o Corrente di prova.')
    if any(c.type not in PHASOR_LESSON_TYPES for c in ir.components):
        return dict(outcome='refusal', cause='unsupported_domain',
                    message='La lezione di impedenza AC accetta R, L, C e sorgenti sinusoidali indipendenti V/I.')
    # Il kernel esige anche una soluzione a vuoto unica del circuito originale.
    # Conserviamo questo limite, senza pubblicare Vth o Norton come nuove richieste.
    fact = analyze_ac_port(ir, req.port)
    if isinstance(fact, Refusal):
        return dict(outcome='refusal', cause=fact.cause, message=fact.diagnosis)
    measured, probe_id = _ac_probe(ir, req.port, F(1), off=True)
    try:
        _check_probe(ir, measured, req.port, probe_id)
    except ValueError as exc:
        return dict(outcome='refusal', cause='path_disagreement', message=str(exc))
    question = Request(req.id+'_probe', 'voltage', probe_id)
    measured = replace(measured, requests=(question,))
    sublesson = create_phasor_lesson(text, measured, question, 'phasor', source_sha, amplitude)
    if sublesson['outcome'] != 'solved':
        return sublesson
    try:
        impedance = _checked_ratio(sublesson['answer'], fact.impedance.amount)
    except (ValueError, ZeroDivisionError) as exc:
        return dict(outcome='refusal', cause='path_disagreement', message=str(exc))

    p, q = req.port
    original = schematic(ir)
    tested = sublesson['original']
    def math_step(title, explanation, svg, expressions, focus=()):
        step = _checked_step(title, explanation, svg, [equation_text(e) for e in expressions], focus)
        step['math'] = expressions
        return step
    def potential(node):
        return number(0) if node == '0' else symbol(f'V({node})')
    port_voltage = add(potential(p), multiply(number(-1), potential(q)))
    voltage_symbol, current_symbol = symbol(f'V({p},{q})'), symbol('I_prova')
    impedance_symbol = symbol(f'Z({p},{q})')
    sources = [c for c in ir.components if c.type in {'voltage_source_ac', 'current_source_ac'}]
    deactivated_math = [equation(symbol(f'{"V" if c.type == "voltage_source_ac" else "I"}({c.id})'),
                                number(0), 'V' if c.type == 'voltage_source_ac' else 'A') for c in sources]
    declared = {'rms': 'valori efficaci (RMS)', 'peak': 'valori di picco',
                'unspecified': 'ampiezza non specificata'}[amplitude]
    steps = [
        math_step('Fissiamo la porta e la frequenza',
                  f'Cerchiamo l’impedenza vista fra {p} e {q}, alla pulsazione dell’ingresso. '
                  'Usiamo exp(+j*omega*t). La tensione di porta è il potenziale del primo morsetto meno quello del secondo. '
                  f'L’ingresso dichiara {declared}; il rapporto fra tensione e corrente non dipende da RMS o picco. Non calcoliamo potenze.',
                  original, [equation(symbol('omega'), number(ir.omega), 'rad/s'),
                             equation(voltage_symbol, port_voltage, 'V')]),
        math_step('Spegniamo le sorgenti indipendenti e applichiamo la prova',
                  'Una sorgente ideale di tensione spenta impone zero volt, cioè un cortocircuito; '
                  'una sorgente ideale di corrente spenta impone zero ampere, cioè un circuito aperto. '
                  f'Conserviamo R, L, C e la frequenza. La sonda {probe_id} inietta 1 A dal nodo {q} al nodo {p}. '
                  'La sonda è un componente del calcolo, aggiunto dopo aver fissato la domanda.',
                  tested, deactivated_math + [equation(current_symbol, number(1), 'A')], [probe_id]),
        # Stessa derivazione già controllata: impedenze, KCL, sostituzioni,
        # eliminazioni, soluzione e recupero della tensione orientata della sonda.
        *sublesson['steps'][1:-1],
        math_step('Orientiamo la tensione della porta',
                  f'La tensione del ramo {probe_id} è riferita da {q} a {p}, mentre la porta è riferita da {p} a {q}. '
                  'Cambiamo quindi il segno prima di formare il rapporto.',
                  tested, [equation(voltage_symbol, port_voltage, 'V'),
                           equation(voltage_symbol, multiply(number(-1), symbol(f'V({probe_id})')), 'V'),
                           equation(voltage_symbol, number(impedance), 'V')], [probe_id]),
        math_step('Dividiamo per la corrente di prova',
                  'L’impedenza è la tensione di porta divisa per la corrente che entra nella rete dal primo morsetto. '
                  'La prova vale esattamente 1 A: il numero coincide con quello della tensione, ma l’unità diventa ohm. '
                  'Il risultato coincide con la misura di porta del kernel, che confronta MNA e tableau.',
                  tested, [equation(impedance_symbol, divide(voltage_symbol, current_symbol), 'Ω'),
                           equation(impedance_symbol, divide(number(impedance), number(1)), 'Ω'),
                           equation(impedance_symbol, number(impedance), 'Ω')], [probe_id]),
        math_step('Torniamo alla porta del circuito originale',
                  f'L’impedenza riguarda i morsetti {p} e {q} del circuito iniziale, con le sorgenti indipendenti spente. '
                  'Invertire insieme tensione e corrente di porta conserva il rapporto. La sonda non fa parte del circuito originale. '
                  'La trasformazione e l’algebra sono controllate; la lezione non è una prova canonica VERIFIED.',
                  original, [equation(impedance_symbol, number(impedance), 'Ω')]),
    ]
    projected = phasor_view(impedance)
    coordinates = projected.pop('phasor')
    answer = dict(**projected, quantity='equivalent_impedance', unit='Ω', reference=f'{p} → {q}',
                  complex_impedance=coordinates, math=number(impedance), display_exact=expression_text(number(impedance)))
    return dict(schema='circuit-lesson.v1', outcome='solved', title=f'Impedenza vista fra {p} e {q}',
                netlist=text, method='test_current', available=['auto', 'test_current'], original=original,
                steps=steps, answer=answer, algebra=sublesson['algebra'],
                port_analysis=dict(schema='ac-port-analysis.v1', port=[p, q],
                                   test_source=dict(id=probe_id, terminals=[q, p], current=dict(exact='1', unit='A', phase_degrees=0)),
                                   deactivated_sources=[c.id for c in sources], status='EXACT_TRANSFORM_AND_RATIO_CHECKED',
                                   canonical_proof=False),
                conventions=dict(**sublesson['conventions'], impedance_definition='Z=V(port)/I_test',
                                 test_current='second → first', impedance_amplitude_invariant=True),
                verification=dict(electrical_claim='PHASOR_PORT_PATHS_CROSSCHECKED', backend='PHASOR_PORT_RESIDUALS_CHECKED',
                                  lesson='phasor-port-crosscheck', product_verified=False,
                                  checks=sublesson['verification']['checks'] + PORT_CHECKS),
                source_sha=source_sha,
                lesson_build=lesson_build('lesson_ac.py', 'lesson_ac_power.py', 'lesson_ac_algebra.py',
                                          'lesson_ac_algebra_check.py', 'lesson_math.py', 'lesson_ac_port.py'),
                fingerprint=hashlib.sha256(text.encode()).hexdigest())
