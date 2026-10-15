"""Lezione Laplace da sorgenti e stati espliciti, con replay polinomiale indipendente."""
import hashlib

from kirchhoff.domain.laplace import solve_laplace
from kirchhoff.domain.laplace_rational import RationalFunction as RF
from kirchhoff.domain.refusal import Refusal
from kirchhoff.pipeline.laplace_input import parse_laplace
from kirchhoff.pipeline.lesson_laplace_algebra import build_laplace_algebra, rational_math
from kirchhoff.pipeline.lesson_laplace_check import verify_laplace_presentation
from kirchhoff.pipeline.lesson_math import equation, equation_text, expression_text, symbol
from kirchhoff.pipeline.lesson_svg import schematic


CHECKS = ['residui della matrice MNA', 'legge dei nodi su tutti i rami',
          'leggi costitutive con stato iniziale', 'algebra: identità polinomiali indipendenti',
          'passaggi e risposta: proiezioni esatte controllate']


def create_laplace_lesson(text, method, source_sha):
    from kirchhoff.pipeline.lesson import _checked_step, lesson_build

    if method not in {'auto', 'laplace'}:
        raise ValueError('Per @laplace seleziona Automatico o Laplace.')
    parsed = parse_laplace(text)
    ir, request = parsed.ir, parsed.ir.requests[0]
    result = solve_laplace(ir, **parsed.solver_inputs)
    if isinstance(result, Refusal):
        return dict(outcome='refusal', cause=result.cause, message=result.diagnosis)
    target = ir.component(request.target)
    prefix, unit = ('V', 'V*s') if request.quantity == 'voltage' else ('I', 'A*s')
    value = getattr(result.branch(target.id), request.quantity)
    math = rational_math(value)
    answer = dict(quantity=request.quantity, unit=unit, reference=' → '.join(target.terminals),
                  exact=expression_text(math), display_exact=expression_text(math), math=math,
                  laplace_transform=dict(variable='s', coefficient_order='ascending', **value.to_json()))
    original = schematic(ir, source_labels=parsed.source_labels)
    def step(title, explanation, expressions, focus=()):
        item = _checked_step(title, explanation, schematic(ir, source_labels=parsed.source_labels, focus=list(focus)),
                             [equation_text(eq) for eq in expressions], list(focus))
        item['math'] = expressions
        return item
    try:
        proof = build_laplace_algebra(parsed, result)
        steps = [step('Dichiariamo sorgenti e stato iniziale',
                      'Usiamo la trasformata unilaterale di Laplace. s ha unità 1/s; V(s) e I(s) hanno unità V·s e A·s. '
                      'Le condizioni iniziali sono a t=0−: la tensione del condensatore è primo morsetto meno secondo, '
                      'la corrente dell’induttore va dal primo al secondo. Un gradino di ampiezza A ha trasformata A/s; '
                      'un impulso di area A ha trasformata A. Ogni stato iniziale, anche nullo, viene dall’ingresso.', proof['declarations']),
                 step('Scriviamo le leggi trasformate dei rami',
                      'La tensione è la differenza dei potenziali. Per il condensatore I(s)=sCV(s)−Cv(0−); '
                      'per l’induttore V(s)=sLI(s)−Li(0−). Le correnti degli induttori e delle sorgenti ideali di tensione '
                      'restano incognite, anche con sorgenti flottanti.', proof['laws'])]
        for entry in proof['initial']:
            steps.append(step('Sostituiamo e raccogliamo: '+entry['substituted']['label'],
                              'Imponiamo la legge dei nodi o il vincolo di tensione, sostituiamo le relazioni dei rami '
                              'e raccogliamo i coefficienti esatti delle incognite. Gli stati iniziali entrano nei termini noti con il loro segno.',
                              [entry['substituted'], entry['collected']], entry['focus']))
        for group in proof['groups']:
            expressions, descriptions = [], []
            for index in group['operations']:
                operation = proof['operations'][index]
                row = operation['row']+1
                if operation['kind'] == 'swap':
                    descriptions.append(f'Scambiamo E{row} con E{operation["other"]+1} per scegliere un coefficiente non nullo.')
                else:
                    descriptions.append(f'Moltiplichiamo E{row} per il reciproco del coefficiente di {group["variable"]}.'
                                        if operation['kind'] == 'scale' else
                                        f'Combiniamo E{row} con E{operation["other"]+1} per eliminare {group["variable"]}.')
                    expressions.extend(operation['math'])
            steps.append(step('Isoliamo '+group['variable'], ' '.join(descriptions)+
                              ' Ogni identità viene confrontata con prodotti di polinomi razionali indipendenti.', expressions))
        steps.append(step('Leggiamo le incognite isolate',
                          'I potenziali sono riferiti al nodo 0. Le correnti conservano i riferimenti dichiarati; '
                          'i coefficienti razionali non sono approssimati.',
                          [equation(symbol(v['name']), rational_math(RF.from_json(proof['solution'][v['name']])), v['unit'])
                           for v in proof['variables']]))
        branch = next(b for b in proof['branches'] if b['component'] == target.id)
        steps.append(step('Torniamo ai morsetti di '+target.id,
                          'Recuperiamo la tensione orientata sottraendo i potenziali e la corrente dalla legge del ramo. '
                          'Il riferimento finale è '+answer['reference']+'.',
                          [equation(symbol(f'V[{target.id}]'), branch['voltage'], 'V*s'),
                           equation(symbol(f'I[{target.id}]'), branch['current'], 'A*s')], [target.id]))
        steps.append(step('La trasformata richiesta',
                          'Questo risultato è una funzione razionale di s, con numeratore e denominatore esatti. '
                          'Una parte polinomiale può rappresentare impulsi o loro derivate: non la trattiamo come una funzione ordinaria del tempo. '
                          'L’antitrasformata e i teoremi del valore iniziale e finale non sono calcolati in questa lezione.',
                          [equation(symbol(f'{prefix}[{target.id}]'), math, unit)], [target.id]))
        verify_laplace_presentation(parsed, proof, result, steps, answer)
    except (ValueError, KeyError, TypeError, IndexError, ZeroDivisionError) as exc:
        return dict(outcome='refusal', cause='path_disagreement', message=str(exc))
    polynomial_degree = len(value.numerator)-len(value.denominator) if value else -1
    return dict(schema='circuit-lesson.v1', outcome='solved',
                title=f'{"Tensione" if request.quantity == "voltage" else "Corrente"} di {target.id} nel dominio di Laplace',
                netlist=text, method='laplace', available=['auto','laplace'], original=original, steps=steps, answer=answer,
                algebra=dict(**proof, status='EXACT_OPERATIONS_CHECKED'), laplace_inputs=parsed.to_json(),
                laplace_output=dict(time_domain_evaluated=False, contains_impulse_terms=polynomial_degree >= 0,
                                    polynomial_part_degree=polynomial_degree if polynomial_degree >= 0 else None),
                conventions=dict(domain='laplace', variable=dict(symbol='s',unit='1/s'), initial_time='0-',
                                 voltage='V(first)-V(second)', current='first → second', power_calculated=False),
                verification=dict(electrical_claim='LAPLACE_ALGEBRA_CROSSCHECKED', backend='SYMBOLIC_MNA_AND_ALGEBRA_CHECKED',
                                  lesson='laplace-exact-algebra-crosscheck', product_verified=False, checks=CHECKS[:]),
                source_sha=source_sha, lesson_build=lesson_build('lesson_laplace.py','lesson_laplace_algebra.py',
                                                               'lesson_laplace_check.py','laplace_input.py','lesson_math.py'),
                fingerprint=hashlib.sha256(text.encode()).hexdigest())
