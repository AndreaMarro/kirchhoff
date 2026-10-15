"""Lezione fasoriale RLC con due assemblaggi esatti e controlli sui rami.

Il confronto non crea Claim VERIFIED: la spina didattica certificata resta
distinta. I fasori conservano la scala dell'ingresso; senza RMS/picco esplicito
non si pubblicano potenze né valori istantanei.
"""
from __future__ import annotations

from decimal import Decimal, localcontext
from fractions import Fraction as F
import hashlib

from kirchhoff.domain.exact import Cyc12, J, ONE, ZERO, SingularSystemError, zeta_pow
from kirchhoff.domain.independent_phasor import PhasorTableauSingularError, solve_phasor_tableau
from kirchhoff.domain.ir import IR, PortRequest, Request
from kirchhoff.domain.mna import solve_phasor
from kirchhoff.domain.refusal import Refusal
from kirchhoff.domain.validate import validate
from kirchhoff.domain.verify import controlli_eseguiti, verify
from kirchhoff.pipeline.lesson_svg import schematic
from kirchhoff.pipeline.netlist import AMPLITUDE_CONVENTIONS
from kirchhoff.pipeline.lesson_ac_power import checked_complex_powers
from kirchhoff.pipeline.lesson_ac_algebra import build_algebra
from kirchhoff.pipeline.lesson_ac_algebra_check import verify_algebra
from kirchhoff.pipeline.lesson_math import (add, divide, equation, equation_text, expression_text,
                                           multiply, number, symbol)


PHASOR_LESSON_TYPES = frozenset({
    'resistor', 'capacitor', 'inductor', 'voltage_source_ac', 'current_source_ac',
})


def _radical(rational: F, radical: F) -> str:
    """Scrive a + b sqrt(3) senza perdere il coefficiente o il segno."""
    if not radical:
        return str(rational)
    term = 'sqrt(3)' if abs(radical) == 1 else f'{abs(radical)}*sqrt(3)'
    if not rational:
        return ('-' if radical < 0 else '') + term
    return f'{rational} {"-" if radical < 0 else "+"} {term}'


def _decimal_component(rational: F, radical: F) -> tuple[str, int]:
    """Arrotonda solo quando entrambi gli estremi esatti danno otto cifre uguali.

    sqrt(3) è racchiusa fra due razionali usando un ulp della radice Decimal.
    La somma degli estremi usa Fraction: nessuna cancellazione a precisione
    finita può trasformare un fasore non nullo in zero. Un coefficiente
    radicale non nullo rende il valore irrazionale, quindi l'intervallo può
    sempre essere separato da una soglia decimale di arrotondamento.
    """
    def rounded(value: F) -> Decimal:
        with localcontext() as ctx:
            ctx.prec = 8
            return Decimal(value.numerator) / Decimal(value.denominator)

    if not radical:
        return format(rounded(rational), '.8g'), 8
    precision = 16
    while True:
        with localcontext() as ctx:
            ctx.prec = precision
            root = Decimal(3).sqrt()
            error = Decimal(1).scaleb(root.adjusted() - precision + 1)
        center, radius = F(root), F(error)
        lower, upper = sorted((rational + radical * (center - radius),
                               rational + radical * (center + radius)))
        low_decimal, high_decimal = rounded(lower), rounded(upper)
        if low_decimal == high_decimal and low_decimal:
            return format(low_decimal, '.8g'), precision
        precision *= 2


def phasor_view(value: Cyc12) -> dict:
    """Proiezione rettangolare esatta; il decimale è soltanto una lettura."""
    if not isinstance(value, Cyc12):
        raise ValueError('Un fasore esposto deve appartenere al campo esatto Cyc12.')
    a, b, c, d = value.c
    real = (a + c / 2, b / 2)
    imaginary = (d + b / 2, c / 2)
    real_exact, imaginary_exact = _radical(*real), _radical(*imaginary)
    real_decimal, real_precision = _decimal_component(*real)
    imaginary_decimal, imaginary_precision = _decimal_component(*imaginary)
    return dict(exact=f'({real_exact}) + j*({imaginary_exact})',
                decimal=f'({real_decimal}) + j*({imaginary_decimal})',
                phasor=dict(basis='1,zeta12,zeta12^2,zeta12^3',
                            coefficients=[str(x) for x in value.c],
                            real_exact=real_exact, imaginary_exact=imaginary_exact,
                            real_decimal=real_decimal, imaginary_decimal=imaginary_decimal,
                            decimal_precision=dict(real=real_precision, imaginary=imaginary_precision,
                                                   significant_digits=8, method='exact-rational-sqrt3-bounds')))


def _impedance(ir: IR, component) -> Cyc12:
    if component.type == 'resistor':
        return Cyc12.of(component.value.amount)
    if component.type == 'inductor':
        return J * ir.omega * component.value.amount
    return ONE / (J * ir.omega * component.value.amount)


def _refusal(cause: str, message: str) -> dict:
    return dict(outcome='refusal', cause=cause, message=message)


def _check(ir: IR, first: dict, second: dict) -> dict | None:
    """Copertura completa, confronto esatto e leggi costitutive, prima della UI."""
    expected = {component.id for component in ir.components}
    if set(first) != expected or set(second) != expected:
        return _refusal('path_disagreement', 'Un percorso fasoriale non copre tutti e soli i componenti.')
    for component in ir.components:
        cid = component.id
        for quantity in ('voltage', 'current'):
            a, b = first[cid].get(quantity), second[cid].get(quantity)
            if not isinstance(a, Cyc12) or not isinstance(b, Cyc12) or a != b:
                return _refusal('path_disagreement', f'{cid}: {quantity} non coincide esattamente fra MNA e tableau indipendente.')
        values = first[cid]
        if component.type in {'resistor', 'inductor', 'capacitor'}:
            valid = values['voltage'] == _impedance(ir, component) * values['current']
        else:
            quantity = 'voltage' if component.type == 'voltage_source_ac' else 'current'
            valid = values[quantity] == component.value.amount * zeta_pow(component.phase_steps)
        if not valid:
            return _refusal('residual', f'{cid}: la soluzione non soddisfa la legge costitutiva del componente.')
    checked = verify(ir, first)
    if isinstance(checked, Refusal):
        return _refusal(checked.cause, checked.diagnosis)
    return None


def create_phasor_lesson(text: str, ir: IR, req: Request | PortRequest,
                         method: str, source_sha: str, amplitude: str = 'unspecified') -> dict:
    """Serve tensione, corrente e potenza AC, senza promuovere la prova DC."""
    from kirchhoff.pipeline.lesson import _checked_step, lesson_build

    if amplitude not in AMPLITUDE_CONVENTIONS:
        raise ValueError('Convenzione di ampiezza fasoriale non riconosciuta.')
    if isinstance(req, PortRequest) and req.quantity == 'equivalent_impedance':
        from kirchhoff.pipeline.lesson_ac_port import create_ac_port_lesson
        return create_ac_port_lesson(text, ir, req, method, source_sha, amplitude)
    if method not in {'auto', 'phasor'}:
        raise ValueError('Per il regime AC seleziona Automatico o Fasori.')
    if not isinstance(req, Request) or req.quantity not in {'current', 'voltage', 'power'}:
        return _refusal('unsupported_domain', 'La lezione AC serve tensioni, correnti e potenze complesse di componente; porte e transitori richiedono un altro percorso.')
    is_power = req.quantity == 'power'
    if is_power and amplitude == 'unspecified':
        return _refusal('claim_unsupported', 'La potenza richiede @amplitude rms oppure @amplitude peak: unspecified non basta.')
    if any(c.type not in PHASOR_LESSON_TYPES for c in ir.components):
        return _refusal('unsupported_domain', 'La lezione AC accetta R, L, C e sorgenti sinusoidali indipendenti V/I. Le sorgenti controllate e gli operazionali hanno solo supporto kernel.')
    validated = validate(ir)
    if isinstance(validated, Refusal):
        return _refusal(validated.cause, validated.diagnosis)
    try:
        primary, independent = solve_phasor(ir), solve_phasor_tableau(ir)
    except (SingularSystemError, PhasorTableauSingularError):
        return _refusal('unsolvable', 'Il sistema fasoriale è singolare: tensioni e correnti non sono determinate univocamente.')
    failed = _check(ir, primary, independent)
    if failed:
        return failed
    try:
        algebra = build_algebra(ir)
        verify_algebra(ir, algebra, independent)
    except (ValueError, SingularSystemError) as exc:
        return _refusal('path_disagreement', str(exc))
    powers = None
    if is_power:
        powers = checked_complex_powers(ir, primary, independent, amplitude)
        if isinstance(powers, Refusal):
            return _refusal(powers.cause, powers.diagnosis)

    target = ir.component(req.target)
    direction = f'{target.terminals[0]} → {target.terminals[1]}'
    unit, answer_symbol = {'voltage': ('V', 'V'), 'current': ('A', 'I'), 'power': ('VA', 'S')}[req.quantity]
    title = f'Potenza complessa di {req.target}' if is_power else f'{"Tensione" if req.quantity == "voltage" else "Corrente"} fasoriale di {req.target}'
    original = schematic(ir)
    source_equations, impedances, laws = [], [], []
    source_math, impedance_math, law_math = [], [], []
    def potential(node):
        return number(0) if node == '0' else symbol(f'V({node})')
    def drop(component):
        return add(potential(component.terminals[0]), multiply(number(-1), potential(component.terminals[1])))
    for component in ir.components:
        cid = component.id
        if component.type in {'resistor', 'inductor', 'capacitor'}:
            formula = {'resistor': 'R', 'inductor': 'j*omega*L', 'capacitor': '1/(j*omega*C)'}[component.type]
            impedances.append(f'Z({cid}) = {formula} = {expression_text(number(_impedance(ir, component)))} Ω')
            laws.append(f'I({cid}) = [V({component.terminals[0]}) - V({component.terminals[1]})] / Z({cid})')
            substitution = number(component.value.amount) if component.type == 'resistor' else (
                multiply(number(J), number(ir.omega), number(component.value.amount)) if component.type == 'inductor' else
                divide(number(1), multiply(number(J), number(ir.omega), number(component.value.amount))))
            impedance_math.extend([equation(symbol(f'Z({cid})'), substitution, 'Ω'),
                                   equation(symbol(f'Z({cid})'), number(_impedance(ir, component)), 'Ω')])
            if impedance_math[-1] == impedance_math[-2]:
                impedance_math.pop()
            law_math.append(equation(symbol(f'I({cid})'), divide(drop(component), symbol(f'Z({cid})')), 'A'))
        else:
            source_quantity = 'voltage' if component.type == 'voltage_source_ac' else 'current'
            source_symbol, source_unit = ('V', 'V') if source_quantity == 'voltage' else ('I', 'A')
            source_equations.append(f'{source_symbol}({cid}) = {component.value.amount} ∠ {component.phase_steps * 30}° = {expression_text(number(primary[cid][source_quantity]))} {source_unit}')
            source_math.append(equation(symbol(f'{source_symbol}({cid})'), number(primary[cid][source_quantity]), source_unit))
            if source_quantity == 'voltage':
                laws.append(f'V({component.terminals[0]}) - V({component.terminals[1]}) = {source_symbol}({cid})')
                law_math.append(equation(drop(component), number(primary[cid][source_quantity]), source_unit))
            else:
                laws.append(source_equations[-1])
                law_math.append(source_math[-1])

    kcl, kcl_math = [], []
    for node in ir.nodes:
        if node == '0':
            continue
        terms = [('+' if c.terminals[0] == node else '-') + f' I({c.id})'
                 for c in ir.components if node in c.terminals]
        kcl.append(f'Nodo {node}: {" ".join(terms).lstrip("+ ")} = 0 A')
        kcl_math.append(equation(add(*(multiply(number(1 if c.terminals[0] == node else -1), symbol(f'I({c.id})'))
                                        for c in ir.components if node in c.terminals)), number(0), 'A', f'Nodo {node}'))
    projected = phasor_view(powers[req.target] if is_power else primary[req.target][req.quantity])
    answer = dict(**projected, unit=unit, reference=direction)
    answer['math'] = number(powers[req.target] if is_power else primary[req.target][req.quantity])
    answer['display_exact'] = expression_text(answer['math'])
    if is_power:
        view = answer.pop('phasor')
        answer.update(quantity='power', complex_power=dict(
            basis=view['basis'], coefficients=view['coefficients'],
            active=dict(exact=view['real_exact'], decimal=view['real_decimal'], unit='W'),
            reactive=dict(exact=view['imaginary_exact'], decimal=view['imaginary_decimal'], unit='var'),
            decimal_precision=view['decimal_precision']))
    amplitude_note = {
        'rms': 'La netlist dichiara valori efficaci (RMS) per tutti i fasori, compreso il risultato.',
        'peak': 'La netlist dichiara valori di picco per tutti i fasori, compreso il risultato.',
        'unspecified': 'La convenzione di ampiezza non è specificata: la netlist non distingue RMS e picco.',
    }[amplitude]
    if is_power:
        amplitude_note = amplitude_note.replace('per tutti i fasori, compreso il risultato.', 'per i fasori di tensione e corrente.')
    scale_note = ' La potenza usa questa scala esplicita; non calcoliamo valori istantanei.' if is_power else ' Manteniamo la scala fornita, senza conversioni; non calcoliamo potenze o valori istantanei.'
    steps = [
        _checked_step('Fissiamo regime, fase e riferimenti',
                      f'Cerchiamo {title.lower()} con riferimento {direction}. '
                      'Usiamo exp(+j*omega*t): la derivata moltiplica per j*omega. '
                      'V è il potenziale del primo morsetto meno quello del secondo; I va dal primo al secondo. '
                      + amplitude_note + scale_note,
                      original, [f'omega = {ir.omega} rad/s', 'j^2 = -1', 'V(0) = 0 V'] + source_equations),
        _checked_step('Passiamo dalle R, L e C alle impedenze',
                      'Alla pulsazione assegnata il resistore mantiene R, l’induttore ha impedenza j*omega*L '
                      'e il condensatore 1/(j*omega*C). Il circuito e i morsetti restano gli stessi.',
                      original, impedances),
        _checked_step('Scriviamo le relazioni dei rami',
                      'La legge di Ohm fasoriale lega ogni corrente alla tensione orientata. '
                      'Le sorgenti ideali impongono la tensione o la corrente indicata dal loro fasore.',
                      original, laws),
        _checked_step('Imponiamo il bilancio delle correnti',
                      'In ciascun nodo sommiamo le correnti uscenti con segno positivo e quelle entranti con segno negativo. '
                      'Sostituiamo ora le leggi dei rami e risolviamo il sistema con operazioni esatte, mostrate una alla volta.',
                      original, kcl),
    ]

    def math_step(title, explanation, expressions, focus=(), algebra_step=None):
        step = _checked_step(title, explanation, schematic(ir, focus=list(focus)),
                             [equation_text(item) for item in expressions], list(focus))
        step['math'] = expressions
        if algebra_step is not None:
            step['algebra'] = dict(schema='ac-algebra-step.v1', **algebra_step)
        return step

    base_math = [[equation(symbol('ω'), number(ir.omega), 'rad/s'),
                  equation(symbol('j²'), number(-1)), equation(symbol('V(0)'), number(0), 'V')] + source_math,
                 impedance_math, law_math, kcl_math]
    for step, expressions in zip(steps, base_math):
        step['math'] = expressions
        step['equations'] = [equation_text(item) for item in expressions]

    for index, entry in enumerate(algebra['initial']):
        heading = f"Sostituiamo le correnti al nodo {entry['node']}" if entry['origin'] == 'kcl' else f"Aggiungiamo il vincolo di {entry['component']}"
        explanation = ('Al posto di ogni corrente passiva scriviamo la differenza dei potenziali divisa per l’impedenza. '
                       'La corrente del generatore ideale di tensione resta un’incognita; la sorgente di corrente entra con il suo segno.'
                       if entry['origin'] == 'kcl' else 'La sorgente impone la differenza fra i potenziali dei suoi morsetti, anche quando nessuno dei due è il riferimento.')
        steps.append(math_step(heading, explanation + ' Sviluppando e raccogliendo i coefficienti otteniamo la seconda equazione.',
                               [entry['substituted'], entry['collected']], entry['focus'], dict(operation='substitute', initial=index)))
    for group in algebra['groups']:
        effective = [algebra['operations'][i] for i in group['operations']
                     if algebra['operations'][i]['kind'] != 'scale' or algebra['operations'][i]['factor'] != number(1)]
        if not effective:
            continue
        expressions, descriptions = [], []
        for index in group['operations']:
            op = algebra['operations'][index]
            label = f"E{op['row']+1}"
            if op['kind'] == 'swap':
                descriptions.append(f"Scambiamo {label} ed E{op['other']+1} per scegliere una riga con coefficiente non nullo.")
                continue
            if op['kind'] == 'scale':
                if op['factor'] == number(1):
                    expressions.append(op['equation'])
                    continue
                divisor = op['before'][op['row']]
                descriptions.append(f"Moltiplichiamo {label} per il reciproco del coefficiente non nullo di {group['variable']}.")
                if any(F(x) for x in divisor[1:]):
                    descriptions.append('Per dividere fra complessi moltiplichiamo numeratore e denominatore per il coniugato.')
                    expressions.extend(op['normalization'])
                else:
                    expressions.append(equation(op['normalization'][0]['left'], op['factor']))
                transformation = multiply(op['factor'], symbol(label))
            else:
                descriptions.append(f"Combiniamo {label} con E{op['other']+1} per eliminare {group['variable']}.")
                transformation = add(symbol(label), multiply(op['factor'], symbol(f"E{op['other']+1}")))
            expressions.extend([equation(symbol(label + ' nuova'), transformation), op['equation']])
        steps.append(math_step(f"Eliminiamo {group['variable']} dalle altre equazioni", ' '.join(descriptions), expressions,
                               algebra_step=dict(operation='eliminate', operations=group['operations'])))
    steps.append(math_step('Leggiamo le incognite isolate',
                           'Dopo le sostituzioni ogni equazione contiene una sola incognita. I potenziali sono rispetto al nodo 0; le correnti dei generatori conservano il verso iniziale.',
                           [equation(symbol(v['name']), algebra['solution'][v['name']], v['unit']) for v in algebra['variables']],
                           algebra_step=dict(operation='solution')))
    for branch in algebra['branches']:
        cid = branch['component']
        if cid != req.target:
            continue
        steps.append(math_step(f'Ritroviamo tensione e corrente di {cid}',
                               f"Torniamo ai morsetti {branch['reference'][0]} → {branch['reference'][1]}. Sottraiamo i potenziali nel verso dichiarato; per R, L e C dividiamo poi per l’impedenza. Le sorgenti mantengono il proprio vincolo.",
                               [equation(symbol(f'V({cid})'), branch['voltage'], 'V'),
                                equation(symbol(f'V({cid})'), number(primary[cid]['voltage']), 'V'),
                                equation(symbol(f'I({cid})'), branch['current'], 'A'),
                                equation(symbol(f'I({cid})'), number(primary[cid]['current']), 'A')], [cid],
                               dict(operation='recover', component=cid)))
    if is_power:
        formula = 'S = V * conj(I)' + (' / 2' if amplitude == 'peak' else '')
        power_values = []
        for cid, power in powers.items():
            view = phasor_view(power)
            power_values.append(f'{cid}: S = {expression_text(number(power))} VA; P = {view["phasor"]["real_exact"]} W; Q = {view["phasor"]["imaginary_exact"]} var')
        steps.extend([
            _checked_step('Dichiariamo la potenza e i segni',
                          'Usiamo la convenzione passiva: V è positiva al primo morsetto e I entra nello stesso morsetto. '
                          'P positiva indica potenza attiva assorbita; P negativa indica potenza attiva erogata. '
                          'Q positiva indica reattiva assorbita, Q negativa reattiva erogata. '
                          'Un induttore ideale ha Q positiva e un condensatore ideale Q negativa. '
                          + ('Con fasori di picco il prodotto va diviso per due.' if amplitude == 'peak' else 'Con fasori efficaci RMS il prodotto non va diviso per due.'),
                          original, [formula, 'P = Re(S) [W]', 'Q = Im(S) [var]', 'S = P + j*Q [VA]']),
            _checked_step('Controlliamo il bilancio delle potenze',
                          'Calcoliamo la potenza di ogni ramo con il kernel e, dai valori del tableau, con '
                          'P = Vr*Ir + Vi*Ii e Q = Vi*Ir - Vr*Ii. Applichiamo il fattore della scala dichiarata. '
                          'I due prodotti devono coincidere esattamente. Includendo le sorgenti, la somma delle '
                          'potenze attive e quella delle reattive devono essere nulle. Questo controllo non certifica la lezione completa.',
                          original, power_values + ['Somma P = 0 W', 'Somma Q = 0 var', 'Somma S = 0 VA']),
            _checked_step('Torniamo alla potenza richiesta',
                          f'La potenza di {req.target} usa V e I con riferimento {direction}, in convenzione passiva. '
                          'P è la potenza attiva media; Q è la potenza reattiva. I segni distinguono assorbimento ed erogazione.',
                          schematic(ir, focus=[req.target]), [f'S({req.target}) = {answer["display_exact"]} VA',
                          f'P = {answer["complex_power"]["active"]["exact"]} W',
                          f'Q = {answer["complex_power"]["reactive"]["exact"]} var'], [req.target]),
        ])
    else:
        steps.append(_checked_step('Torniamo alla grandezza richiesta',
                      f'Il fasore cercato è riferito a {direction}. La parte reale e quella immaginaria '
                      'descrivono insieme ampiezza e fase; il decimale è solo un’approssimazione del valore esatto. ' + amplitude_note,
                      schematic(ir, focus=[req.target]), [f'{answer_symbol}({req.target}) = {answer["display_exact"]} {unit}'], [req.target]))
    final_math = [equation(symbol(f'{answer_symbol}({req.target})'), answer['math'], unit)]
    if is_power:
        a,b,c,d = powers[req.target].c
        real = Cyc12((a+c/2, b, F(0), -b/2))
        imaginary = Cyc12((d+b/2, c, F(0), -c/2))
        final_math.extend([equation(symbol('P'), number(real), 'W'), equation(symbol('Q'), number(imaginary), 'var')])
    steps[-1]['math'] = final_math
    steps[-1]['equations'] = [equation_text(item) for item in final_math]
    power_conventions = dict(power_sign='passive', power_factor='1/2' if amplitude == 'peak' else '1',
                             power_formula='S=V*conj(I)/2' if amplitude == 'peak' else 'S=V*conj(I)') if is_power else {}
    return dict(schema='circuit-lesson.v1', outcome='solved', title=title,
                netlist=text, method='phasor', available=['auto', 'phasor'], original=original,
                steps=steps, answer=answer, algebra=dict(**algebra, status='EXACT_OPERATIONS_CHECKED'),
                conventions=dict(domain='ac_sinusoidal', time_dependence='exp(+jωt)',
                                 amplitude=amplitude, omega=dict(exact=str(ir.omega), unit='rad/s'),
                                 voltage='V(first)-V(second)', current='first → second', power_calculated=is_power, **power_conventions),
                verification=dict(electrical_claim='PHASOR_POWER_CROSSCHECKED' if is_power else 'PHASOR_PATHS_CROSSCHECKED',
                                  backend='PHASOR_RESIDUALS_AND_POWER_CHECKED' if is_power else 'PHASOR_RESIDUALS_CHECKED',
                                  lesson='phasor-power-all-branches-crosscheck' if is_power else 'phasor-all-branches-crosscheck', product_verified=False,
                                  checks=list(controlli_eseguiti(ir, primary)) + ['leggi costitutive di tutti i componenti']
                                  + (['potenze di tutti i rami: prodotto indipendente', 'bilancio delle potenze complesse'] if is_power else [])),
                source_sha=source_sha,
                lesson_build=lesson_build('lesson_ac.py', 'lesson_ac_power.py', 'lesson_ac_algebra.py', 'lesson_ac_algebra_check.py', 'lesson_math.py'),
                fingerprint=hashlib.sha256(text.encode()).hexdigest())
