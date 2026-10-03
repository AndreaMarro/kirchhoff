"""Independent unilateral Laplace audit: branch tableau + exact hand formulas.

No Kirchhoff imports. Every branch current points p -> q. Initial conditions
are at 0-minus. The entire tableau uses Python complex, not rational functions.
"""
from __future__ import annotations
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parent
SEED = 2026100317
POINTS = [["1/4","0"],["1","0"],["5/2","0"],["3/4","5/4"],["2","-1/2"],["1/10","3"]]


def encoded(value): return (json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+"\n").encode()
def sha(data): return hashlib.sha256(data).hexdigest()
def point(pair): return complex(float(F(pair[0])),float(F(pair[1])))
def rf(num, den=(1,)): return {"numerator":list(map(str,num)), "denominator":list(map(str,den))}
def poly(coefficients, s):
    total = 0j
    for value in reversed(coefficients): total = total*s + float(F(value))
    return total
def value(transform, s):
    denominator = poly(transform['denominator'],s)
    if denominator == 0: raise ZeroDivisionError('evaluation pole')
    return poly(transform['numerator'],s)/denominator
def signed(transform, factor=-1): return rf([factor*F(v) for v in transform['numerator']],transform['denominator'])
def time_scaled(transform, factor=2):
    # Laplace{f(k t)} = F(s/k)/k. Denominator normalization is unnecessary here.
    return rf([F(v)/factor**(i+1) for i,v in enumerate(transform['numerator'])],
              [F(v)/factor**i for i,v in enumerate(transform['denominator'])])
def component(cid, p, q, magnitude=1): return {'id':cid,'kind':cid[0],'p':p,'q':q,'value':str(magnitude)}


def validate(case):
    components = case['components']
    if len({c['id'] for c in components}) != len(components): return 'invalid_component_id'
    if any(c['kind'] not in 'RLCVI' for c in components): return 'invalid_component_kind'
    if any(F(c['value']) <= 0 for c in components if c['kind'] in 'RLC'): return 'invalid_value'
    capacitors = {c['id'] for c in components if c['kind'] == 'C'}
    inductors = {c['id'] for c in components if c['kind'] == 'L'}
    sources = {c['id'] for c in components if c['kind'] in 'VI'}
    if set(case['capacitor_voltages']) != capacitors or set(case['inductor_currents']) != inductors:
        return 'invalid_initial_conditions'
    if set(case['source_transforms']) != sources: return 'invalid_source_transforms'
    for transform in case['source_transforms'].values():
        if not transform['numerator'] or not transform['denominator'] or not any(F(v) for v in transform['denominator']):
            return 'invalid_transform'
    if '0' not in {c[key] for c in components for key in ('p','q')}: return 'missing_reference'
    return None


def solve(case, s, mutation=None):
    error = validate(case)
    if error: return {'status':error}
    components = case['components']
    nodes = sorted({c[key] for c in components for key in ('p','q')} - {'0'})
    node_index = {node:i for i,node in enumerate(nodes)}
    branch_index = {c['id']:len(nodes)+i for i,c in enumerate(components)}
    size = len(nodes)+len(components)
    matrix, rhs = [[0j]*size for _ in range(size)], [0j]*size
    for branch in components:
        cid, kind, p, q, magnitude = (branch[key] for key in ('id','kind','p','q','value'))
        magnitude = float(F(magnitude))
        col, row = branch_index[cid], branch_index[cid]
        # One KCL row per node: currents leaving the node sum to zero.
        for node, sign in ((p,1),(q,-1)):
            if node != '0': matrix[node_index[node]][col] += sign
        def voltage(factor):
            for node, sign in ((p,1),(q,-1)):
                if node != '0': matrix[row][node_index[node]] += sign*factor
        if kind == 'R':
            voltage(1); matrix[row][col] = -magnitude
        elif kind == 'L':
            initial = float(F(case['inductor_currents'][cid]))
            voltage(1); matrix[row][col] = -s*magnitude
            rhs[row] = -magnitude*initial
            if mutation == 'inductor_initial_sign': rhs[row] *= -1
            if mutation == 'omit_initial' : rhs[row] = 0
            if mutation == 'initial_times_s': rhs[row] *= s
        elif kind == 'C':
            initial = float(F(case['capacitor_voltages'][cid]))
            voltage(s*magnitude); matrix[row][col] = -1
            rhs[row] = magnitude*initial
            if mutation == 'capacitor_initial_sign': rhs[row] *= -1
            if mutation == 'omit_initial': rhs[row] = 0
            if mutation == 'initial_times_s': rhs[row] *= s
        else:
            transform = case['source_transforms'][cid]
            rhs[row] = value(transform,s)
            if mutation == 'step_as_impulse' and transform['denominator'] == ['0','1']:
                rhs[row] *= s
            if kind == 'V': voltage(1)
            else: matrix[row][col] = 1
    reduced = [row[:] + [b] for row,b in zip(matrix,rhs)]
    scale = max(1.,*(abs(v) for row in matrix for v in row))
    tolerance, pivots, row = 2e-12*scale, [], 0
    for col in range(size):
        pivot = max(range(row,size),key=lambda r:abs(reduced[r][col]),default=None)
        if pivot is None or abs(reduced[pivot][col]) <= tolerance: continue
        reduced[row],reduced[pivot] = reduced[pivot],reduced[row]
        divisor = reduced[row][col]
        reduced[row] = [v/divisor for v in reduced[row]]
        for r in range(size):
            if r == row: continue
            factor = reduced[r][col]
            reduced[r] = [v-factor*u for v,u in zip(reduced[r],reduced[row])]
        pivots.append(col); row += 1
    if any(max((abs(v) for v in values[:-1]),default=0) <= tolerance and abs(values[-1]) > tolerance for values in reduced):
        return {'status':'inconsistent_system','rank':len(pivots),'unknowns':size}
    if len(pivots) < size: return {'status':'nonunique_system','rank':len(pivots),'unknowns':size}
    answer = [0j]*size
    for r,col in enumerate(pivots): answer[col] = reduced[r][-1]
    residual = max(abs(sum(a*x for a,x in zip(row,answer))-b) for row,b in zip(matrix,rhs))
    assert residual <= 1e-8*max(1.,*(abs(x) for x in answer)), residual
    volts = {'0':0j,**{node:answer[index] for node,index in node_index.items()}}
    observations = {f'V({node})':v for node,v in volts.items()}
    for branch in components:
        cid = branch['id']
        observations[f'V[{cid}]'] = volts[branch['p']]-volts[branch['q']]
        observations[f'I[{cid}]'] = answer[branch_index[cid]]
    return {'status':'solved','observations':observations,'max_residual':residual}


def serial(result):
    return {key:({name:[z.real,z.imag] for name,z in values.items()} if key == 'observations' else values)
            for key,values in result.items()}


def base(cid, components, sources, capacitors, inductors, analytic=None):
    return {'id':cid,'components':components,'source_transforms':sources,
            'capacitor_voltages':{k:str(v) for k,v in capacitors.items()},
            'inductor_currents':{k:str(v) for k,v in inductors.items()},'analytic':analytic or {}}


def manual_cases():
    cases = []
    for label,R,C,A,v0 in [('rc_step',F(3),F('1/2'),F(5),F(-2)),
                           ('rc_decay',F(2),F('1/3'),F(0),F(4))]:
        tau = R*C
        cases.append(base(label,[component('V1','e','0'),component('R1','e','a',R),component('C1','a','0',C)],
            {'V1':rf([A],[0,1])},{'C1':v0},{},
            {'V[C1]':rf([A/tau,v0],[0,1/tau,1]),'I[C1]':rf([(A-v0)/R],[1/tau,1])}))
    for label,R,L,A,i0 in [('rl_step',F(4),F(2),F(3),F(-2)),
                           ('rl_decay',F(3),F('1/2'),F(0),F(5))]:
        cases.append(base(label,[component('V1','e','0'),component('R1','e','a',R),component('L1','a','0',L)],
            {'V1':rf([A],[0,1])},{},{'L1':i0},
            {'I[L1]':rf([A/L,i0],[0,R/L,1]),'V[L1]':rf([A-R*i0],[R/L,1])}))
    for label,R,L,C,A,v0,i0 in [
        ('rlc_underdamped',F(1),F(1),F(1),F(4),F(-2),F(3)),
        ('rlc_critical',F(2),F(1),F(1),F(0),F(5),F(-3)),
        ('rlc_overdamped',F(3),F(1),F(1),F(7),F(2),F(-1)),
        ('lc_oscillation',F(0),F(2),F('1/8'),F(0),F(-2),F(3))]:
        components = [component('V1','e','0')]
        if R: components += [component('R1','e','a',R)]
        components += [component('L1','a' if R else 'e','b',L),component('C1','b','0',C)]
        denominator = [1/(L*C),R/L,1]
        case = base(label,components,{'V1':rf([A],[0,1])},{'C1':v0},{'L1':i0},
            {'I[L1]':rf([(A-v0)/L,i0],denominator),
             'V[C1]':rf([A/(L*C),i0/C+v0*R/L,v0],[0,*denominator]),
             'V[L1]':rf([-i0/C,A-v0-R*i0],denominator)})
        if not R: case['pole_checks'] = [{'s':['0','2'],'observation':'I[L1]'}]
        cases.append(case)
    return cases


def mesh_cases():
    rng = random.Random(SEED)
    bridge = base('bridge_initial',[
        component('V1','e','0'),component('R0','e','p',2),component('R1','p','a',3),
        component('R2','p','b',5),component('L1','a','0',2),component('C1','b','0','1/3'),
        component('R3','a','b',7),component('I1','0','b')],
        {'V1':rf([6],[0,1]),'I1':rf([2],[0,1])},{'C1':-3},{'L1':2})
    cases = [bridge]
    for i in range(3):
        edges = [('e','p'),('p','a'),('a','b'),('b','c'),('c','0'),('p','0'),('a','c')]
        components = [component('V1','e','0')]+[component(f'R{n}',a,b,rng.randrange(1,8)) for n,(a,b) in enumerate(edges)]
        components += [component('L1','a','0',F(rng.randrange(1,6),3)),
                       component('C1','p','b',F(rng.randrange(1,5),7)),component('I1','b','0')]
        voltage = [rf([5],[0,1]),rf([0,3],[4,0,1]),rf([7],[2,1])][i]
        current = [rf([1]),rf([-2],[0,1]),rf([3],[1,1])][i]
        cases.append(base(f'seeded_mesh_{i+1:02}',components,{'V1':voltage,'I1':current},
                          {'C1':rng.choice([-4,-2,3])},{'L1':rng.choice([-3,2,5])}))
    return cases


def fixtures():
    cases = []
    for original in manual_cases()+mesh_cases():
        name = original['id']
        for variant in ['base','reordered','directions_reversed','source_metadata_changed','time_scaled']:
            case = deepcopy(original)
            case.update(id=f'{name}/{variant}',group=name,variant=variant,require_solved=True)
            if variant == 'reordered': case['components'].reverse()
            if variant == 'directions_reversed':
                for branch in case['components']: branch['p'],branch['q'] = branch['q'],branch['p']
                for field in ['capacitor_voltages','inductor_currents']:
                    case[field] = {key:str(-F(v)) for key,v in case[field].items()}
                case['source_transforms'] = {key:signed(v) for key,v in case['source_transforms'].items()}
                case['analytic'] = {key:signed(v) for key,v in case['analytic'].items()}
            if variant == 'source_metadata_changed':
                for branch in case['components']:
                    if branch['kind'] in 'VI': branch['value'] = '97/3'
            if variant == 'time_scaled':
                for branch in case['components']:
                    if branch['kind'] in 'LC': branch['value'] = str(F(branch['value'])/2)
                case['source_transforms'] = {key:time_scaled(v) for key,v in case['source_transforms'].items()}
                case['analytic'] = {key:time_scaled(v) for key,v in case['analytic'].items()}
                if 'pole_checks' in case:
                    case['pole_checks'] = [{'s':['0','4'],'observation':'I[L1]'}]
            cases.append(case)
        if name.startswith(('bridge','seeded')):
            for variant in ['forced_only','initial_only']:
                case = deepcopy(original)
                case.update(id=f'{name}/{variant}',group=name,variant=variant,require_solved=True)
                if variant == 'forced_only':
                    case['capacitor_voltages'] = {key:'0' for key in case['capacitor_voltages']}
                    case['inductor_currents'] = {key:'0' for key in case['inductor_currents']}
                else: case['source_transforms'] = {key:rf([0]) for key in case['source_transforms']}
                cases.append(case)
    special = [
        base('redundant_voltage_constraints',[component('V1','p','0'),component('V2','p','0'),component('R1','p','0',3)],
             {'V1':rf([2],[0,1]),'V2':rf([2],[0,1])},{},{}),
        base('inconsistent_voltage_constraints',[component('V1','p','0'),component('V2','p','0'),component('R1','p','0',3)],
             {'V1':rf([2],[0,1]),'V2':rf([3],[0,1])},{},{}),
        base('open_inductor_initial_impulse',[component('L1','p','0',3)],{}, {},{'L1':2},{'V[L1]':rf([-6]),'I[L1]':rf([0])}),
        base('clamped_capacitor_initial_impulse',[component('V1','p','0'),component('C1','p','0',2)],
             {'V1':rf([5],[0,1])},{'C1':-1},{},{'I[C1]':rf([12]),'V[C1]':rf([5],[0,1])}),
    ]
    island = deepcopy(manual_cases()[0]); island['id'] = 'floating_island'; island['components'].append(component('R9','x','y',7)); special.append(island)
    for name,change in [
        ('zero_resistance',lambda c:c['components'][1].update(value='0')),
        ('missing_capacitor_initial',lambda c:c['capacitor_voltages'].clear()),
        ('unknown_capacitor_initial',lambda c:c['capacitor_voltages'].update(C99='0')),
        ('missing_source_transform',lambda c:c['source_transforms'].clear()),
        ('zero_source_denominator',lambda c:c['source_transforms'].update(V1=rf([1],[0]))),
        ('duplicate_component_id',lambda c:c['components'].append(deepcopy(c['components'][1]))),
    ]:
        case = deepcopy(manual_cases()[0]); case['id'] = name; change(case); special.append(case)
    missing_l = deepcopy(manual_cases()[2]);missing_l['id']='missing_inductor_initial';missing_l['inductor_currents'].clear();special.append(missing_l)
    classes = ['nonunique_system','inconsistent_system','solved','solved','nonunique_system',
               'invalid_value','invalid_initial_conditions','invalid_initial_conditions','invalid_source_transforms',
               'invalid_transform','invalid_component_id','invalid_initial_conditions']
    for case,status in zip(special,classes):
        case.update(group='special',variant=case['id'],expected_status=status,require_solved=status=='solved')
        cases.append(case)
    return cases


def max_difference(left,right):
    return max(abs(left[key]-right[key])/max(1,abs(left[key])) for key in left)


def freeze():
    if (ROOT/'cases.json').exists() or (ROOT/'expected.json').exists(): raise SystemExit('Refusing to overwrite frozen evidence')
    cases, expected, grouped = fixtures(), {}, {}
    largest_residual = 0.
    for case in cases:
        samples = []
        for coordinates in POINTS:
            s = point(coordinates); result = solve(case,s)
            if case['require_solved']: assert result['status']=='solved',(case['id'],result)
            if 'expected_status' in case: assert result['status']==case['expected_status'],(case['id'],result)
            if result['status']=='solved':
                largest_residual = max(largest_residual,result['max_residual'])
                for observation,transform in case['analytic'].items():
                    exact = value(transform,s)
                    assert abs(result['observations'][observation]-exact) <= 2e-10*max(1,abs(exact)),(case['id'],observation)
            samples.append({'s':coordinates,**serial(result)})
        expected[case['id']] = samples
        grouped[(case['group'],case['variant'])] = case
    # Freeze independently tested physical metamorphisms, not merely each run.
    relations = 0
    for (group,variant),case in grouped.items():
        if group=='special' or variant=='base': continue
        original = grouped[(group,'base')]
        for coordinates in POINTS:
            s = point(coordinates)
            target = solve(case,s)['observations']
            if variant in ('reordered','source_metadata_changed'):
                reference = solve(original,s)['observations']
            elif variant=='directions_reversed':
                reference = {key:(-z if '[' in key else z) for key,z in solve(original,s)['observations'].items()}
            elif variant=='time_scaled': reference = {key:z/2 for key,z in solve(original,s/2)['observations'].items()}
            elif variant in ('initial_only','forced_only'):
                other = grouped[(group,'forced_only' if variant=='initial_only' else 'initial_only')]
                total = solve(original,s)['observations']; part = solve(other,s)['observations']
                reference = {key:total[key]-part[key] for key in total}
            assert max_difference(reference,target)<3e-10,(group,variant,coordinates)
            relations += 1
    mutants = []
    for mutation in ['capacitor_initial_sign','inductor_initial_sign','omit_initial','initial_times_s','step_as_impulse']:
        rejected = []
        for case in cases:
            if not case['require_solved'] or case['variant']!='base': continue
            differences = [max_difference(solve(case,point(p))['observations'],solve(case,point(p),mutation)['observations']) for p in POINTS]
            if max(differences)>1e-6: rejected.append(case['id'])
        assert rejected,mutation
        mutants.append({'mutation':mutation,'detected_in':rejected})
    case_bytes = encoded({'seed':SEED,'points':POINTS,'conventions':{'initial_time':'0-','voltage':'Vp-Vq','current':'p->q',
        'source_authority':'explicit rational transform, not component magnitude'},'cases':cases})
    report = {'model':'inherited/unknown','frozen_at_utc':datetime.now(timezone.utc).isoformat(),'seed':SEED,
              'case_count':len(cases),'required_solved':sum(c['require_solved'] for c in cases),
              'points_per_case':len(POINTS),'physical_metamorphic_checks':relations,'max_tableau_residual':largest_residual,
              'cases_sha256':sha(case_bytes),'oracle_sha256':sha(Path(__file__).read_bytes()),
              'product_implementation_read':False,'product_called':False,
              'mutation_scope':'oracle sensitivity, not mutations of production implementation','mutations':mutants,'samples':expected}
    (ROOT/'cases.json').write_bytes(case_bytes);(ROOT/'expected.json').write_bytes(encoded(report))
    print(json.dumps({k:v for k,v in report.items() if k not in ('samples','mutations')},indent=2))
    print('Mutant detections:',{m['mutation']:len(m['detected_in']) for m in mutants})


def check():
    expected=json.loads((ROOT/'expected.json').read_text());content=json.loads((ROOT/'cases.json').read_text())
    assert sha((ROOT/'cases.json').read_bytes())==expected['cases_sha256']
    assert sha(Path(__file__).read_bytes())==expected['oracle_sha256']
    assert content['cases']==fixtures()
    for case in content['cases']:
        for row in expected['samples'][case['id']]:
            assert serial(solve(case,point(row['s'])))=={k:v for k,v in row.items() if k!='s'},case['id']
    return content,expected


if __name__=='__main__':
    if sys.argv[1:] == ['freeze']: freeze()
    elif sys.argv[1:] == ['check']:
        content,expected=check();print(json.dumps({'frozen_integrity':True,'cases':len(content['cases']),'expected_sha256':sha((ROOT/'expected.json').read_bytes())}))
    else: raise SystemExit('Usage: python oracle.py freeze|check')
