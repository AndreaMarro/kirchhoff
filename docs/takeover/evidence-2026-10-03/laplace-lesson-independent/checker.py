"""External Laplace lesson audit, stdlib only and no product imports.

Six numerical evaluations of every displayed equation using a frozen independent
branch tableau. This is a falsifier, not symbolic proof or time-domain inversion.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction as F
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
OLD = ROOT.parent / 'laplace-independent'
OLD_HASHES = {
    'oracle.py':'62b803e5a6a79bfbbb0c5f9fed30ab44912dd392eedb14c79f0f1233483b4f7a',
    'cases.json':'8caa2622aa067f2063e53e7e1f59d49a276180c8a0c709089febce3083818e0f',
    'expected.json':'3cb19330473329bdac76cd85e9f44b3d965ac9b039ace2bea41e02e7a3bbb360',
}
TOLERANCE = 3e-8

def encoded(obj): return (json.dumps(obj,sort_keys=True,indent=2,ensure_ascii=False)+'\n').encode()
def sha(data): return hashlib.sha256(data).hexdigest()
def load_oracle():
    for name,digest in OLD_HASHES.items():
        assert sha((OLD/name).read_bytes()) == digest, f'frozen old file changed: {name}'
    spec = importlib.util.spec_from_file_location('frozen_branch_tableau', OLD/'oracle.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
O = load_oracle()


def parse_netlist(text):
    """Small independent parser for the preregistered lesson input grammar."""
    components, sources, source_data, capacitors, inductors = [], {}, {}, {}, {}
    request = None
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    assert lines.pop(0) == '@laplace'
    for line in lines:
        bits = line.split()
        if bits[0] == '@initial':
            _,cid,quantity,exact,unit = bits
            value = F(exact)
            target = capacitors if cid[0] == 'C' else inductors
            assert cid not in target
            assert (quantity,unit) == (('voltage','volt') if cid[0] == 'C' else ('current','ampere'))
            target[cid] = str(value)
        elif bits[0] == '?':
            assert request is None
            _,quantity,cid = bits
            assert quantity in {'voltage','current'}
            request = {'quantity':quantity,'component':cid}
        else:
            cid,p,q,exact,unit,*waveform = bits
            kind = cid[0]
            magnitude = F(exact)
            if kind in 'RLC':
                assert unit == {'R':'ohm','L':'henry','C':'farad'}[kind]
                assert not waveform
            else:
                assert kind in 'VI' and waveform in [['step'],['impulse']]
                wave = waveform[0]
                expected_unit = ('volt' if kind == 'V' else 'ampere')+('*s' if wave == 'impulse' else '')
                assert unit == expected_unit
                sources[cid] = O.rf([magnitude],[0,1] if wave == 'step' else [1])
                source_data[cid] = {'quantity':'voltage' if kind == 'V' else 'current',
                    'waveform':wave,'amplitude':{'exact':str(magnitude),
                    'unit':('V' if kind == 'V' else 'A')+('*s' if wave == 'impulse' else '')}}
            components.append(O.component(cid,p,q,magnitude))
    assert request is not None and request['component'] in {c['id'] for c in components}
    case = O.base('parsed-original',components,sources,capacitors,inductors)
    assert O.validate(case) is None
    return case,request,source_data


def netlist(case,source_data,request):
    lines = ['@laplace']
    for c in case['components']:
        kind,cid = c['kind'],c['id']
        if kind in 'RLC': tail = f"{c['value']} "+{'R':'ohm','L':'henry','C':'farad'}[kind]
        else:
            source = source_data[cid]
            unit = ('volt' if kind == 'V' else 'ampere')+('*s' if source['waveform']=='impulse' else '')
            tail = f"{source['amplitude']['exact']} {unit} {source['waveform']}"
        lines.append(f"{cid} {c['p']} {c['q']} {tail}")
    for cid,value in case['capacitor_voltages'].items(): lines.append(f'@initial {cid} voltage {value} volt')
    for cid,value in case['inductor_currents'].items(): lines.append(f'@initial {cid} current {value} ampere')
    lines.append(f"? {request['quantity']} {request['component']}")
    return '\n'.join(lines)+'\n'


def fixtures():
    C = O.component
    components = [C('V1','e','0'),C('R0','e','p',2),C('R1','p','a',3),C('R2','a','0',5),
        C('R3','p','b',7),C('R4','b','c',11),C('R5','c','0',13),C('R6','a','c',17),
        C('C1','a','b','1/3'),C('C2','p','c','2/5'),C('L1','p','a','3/2'),
        C('L2','b','0','4/3'),C('I1','0','b')]
    original = O.base('mesh_2c_2l',components,{'V1':O.rf([6],[0,1]),'I1':O.rf([2],[0,1])},
        {'C1':2,'C2':-3},{'L1':-1,'L2':4})
    cases = []
    for index,name in enumerate(['mixed_initial_step','reverse_c2_l1','swapped_initial','natural_response','mixed_impulses']):
        case = deepcopy(original)
        sources = {'V1':{'quantity':'voltage','waveform':'step','amplitude':{'exact':'6','unit':'V'}},
                   'I1':{'quantity':'current','waveform':'step','amplitude':{'exact':'2','unit':'A'}}}
        if name == 'reverse_c2_l1':
            for branch in case['components']:
                if branch['id'] in ['C2','L1']: branch['p'],branch['q'] = branch['q'],branch['p']
            case['capacitor_voltages']['C2'] = '3'
            case['inductor_currents']['L1'] = '1'
        if name == 'swapped_initial':
            case['capacitor_voltages'] = {'C1':'-3','C2':'2'}
            case['inductor_currents'] = {'L1':'4','L2':'-1'}
        if name == 'natural_response':
            for source in sources.values(): source['amplitude']['exact'] = '0'
        if name == 'mixed_impulses':
            for cid,area in [('V1','-3/2'),('I1','5/3')]:
                sources[cid]['waveform'] = 'impulse'
                sources[cid]['amplitude'] = {'exact':area,'unit':'V*s' if cid[0]=='V' else 'A*s'}
        request = {'quantity':'voltage' if index%2==0 else 'current','component':'C1' if index%2==0 else 'L2'}
        text = netlist(case,sources,request)
        parsed,query,parsed_sources = parse_netlist(text)
        samples = []
        for pair in O.POINTS:
            result = O.solve(parsed,O.point(pair))
            assert result['status']=='solved',result
            samples.append({'s':pair,**O.serial(result)})
        cases.append({'id':name,'netlist':text,'request':query,'expected_samples':samples})
    return cases


def trim(values):
    values = list(map(F,values))
    assert values
    while len(values)>1 and not values[-1]: values.pop()
    return values

def convolution(a,b):
    result = [F(0)]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b): result[i+j] += x*y
    return trim(result)

def rational(value):
    assert isinstance(value,dict)
    numerator,denominator = trim(value['numerator']),trim(value['denominator'])
    assert any(denominator),'zero denominator'
    return numerator,denominator

def equivalent(a,b):
    an,ad = rational(a); bn,bd = rational(b)
    return convolution(an,bd)==convolution(bn,ad)

def expr(node,bindings,depth=0):
    assert depth<180,'AST excessive depth'
    assert isinstance(node,dict)
    kind = node['kind']
    if kind=='number':
        values = list(map(F,node['coefficients']))
        assert len(values)==4 and values[1:]==[0,0,0],'Laplace scalar must be rational'
        return complex(float(values[0]))
    if kind=='symbol': return bindings[node['name']]
    if kind in {'add','multiply'}:
        result = 0j if kind=='add' else 1+0j
        assert isinstance(node['args'],list)
        for child in node['args']:
            v = expr(child,bindings,depth+1)
            result = result+v if kind=='add' else result*v
        return result
    if kind=='divide': return expr(node['numerator'],bindings,depth+1)/expr(node['denominator'],bindings,depth+1)
    raise AssertionError(f'unsupported expression: {kind}')

def walk(value,path='$'):
    if isinstance(value,dict):
        yield path,value
        for key,child in value.items(): yield from walk(child,path+'.'+key)
    elif isinstance(value,list):
        for i,child in enumerate(value): yield from walk(child,f'{path}[{i}]')

def binding(case,s,result):
    values = dict(result['observations'],s=s)
    for c in case['components']:
        if c['kind'] in 'VL': values[f"I({c['id']})"] = result['observations'][f"I[{c['id']}]"]
    for field,prefix in [('capacitor_voltages','v0'),('inductor_currents','i0')]:
        values.update({f'{prefix}({cid})':complex(float(F(x))) for cid,x in case[field].items()})
    return values


def compare_lesson(entry,payload):
    """Return audit findings, never modify original payload or expected data."""
    errors=[]; count=0; worst=0.
    case,request,sources = parse_netlist(entry['netlist'])
    lesson = payload.get('lesson',payload)
    try:
        inputs = lesson['laplace_inputs']
        assert inputs['initial_time']=='0-','initial time must be 0-'
        for field,unit in [('capacitor_voltages','V'),('inductor_currents','A')]:
            records = inputs[field]
            assert len({r['component'] for r in records})==len(records),'duplicate IC'
            assert {r['component'] for r in records}==set(case[field]),'IC inventory mismatch'
            for record in records:
                assert F(record['exact'])==F(case[field][record['component']]),'IC value mismatch'
                assert record['unit']==unit,'IC unit mismatch'
        records = inputs['sources']
        assert len({r['component'] for r in records})==len(records),'duplicate source'
        assert {r['component'] for r in records}==set(sources),'source inventory mismatch'
        for record in records:
            cid = record['component']; expected = sources[cid]
            assert record['quantity']==expected['quantity'],'source quantity mismatch'
            assert record['waveform']==expected['waveform'],'source waveform mismatch'
            assert F(record['amplitude']['exact'])==F(expected['amplitude']['exact']),'source amplitude/area mismatch'
            assert record['amplitude']['unit']==expected['amplitude']['unit'],'source amplitude/area unit mismatch'
            assert equivalent(record['transform'],case['source_transforms'][cid]),'source transform mismatch'
    except (AssertionError,KeyError,TypeError,ValueError,ZeroDivisionError) as exc:
        errors.append('inputs: '+str(exc))
    equations=[]; seen_states=set()
    try:
        assert lesson['steps'],'steps missing'
        for i,step in enumerate(lesson['steps']):
            for j,node in enumerate(step.get('math',[])):
                assert node['kind']=='equation','step.math contains non-equation'
                assert isinstance(node['label'],str) and node['unit'] in {'','V','A','V*s','A*s'},'equation unit/label malformed'
                equations.append((f'steps[{i}].math[{j}]',node))
                seen_states.update(n['name'] for _,n in walk(node) if n.get('kind')=='symbol' and n['name'].startswith(('v0(','i0(')))
        assert equations,'no displayed equations'
        wanted = {f'v0({cid})' for cid in case['capacitor_voltages']} | {f'i0({cid})' for cid in case['inductor_currents']}
        assert seen_states==wanted,'displayed IC symbols incomplete or contaminated'
    except (AssertionError,KeyError,TypeError) as exc:
        errors.append('equation inventory: '+str(exc))
    try:
        answer = lesson['answer']
        assert answer['quantity']==request['quantity'],'answer quantity mismatch'
        unit = 'V*s' if request['quantity']=='voltage' else 'A*s'
        assert answer['unit']==unit,'answer transform unit mismatch'
        target=next(c for c in case['components'] if c['id']==request['component'])
        assert answer['reference']==f"{target['p']} → {target['q']}",'answer passive reference mismatch'
        transform = answer['laplace_transform']
        assert transform['variable']=='s' and transform['coefficient_order']=='ascending','answer RF convention mismatch'
        rational(transform)
    except (AssertionError,KeyError,TypeError,ValueError) as exc:
        errors.append('answer metadata: '+str(exc)); transform=None
    for path,node in walk(lesson):
        if node.get('canonical_proof') is True or node.get('product_verified') is True:
            errors.append(path+': unsupported verified promotion')
    try:
        assert lesson['verification']['product_verified'] is False,'product_verified must be false'
    except (AssertionError,KeyError,TypeError) as exc: errors.append('verification: '+str(exc))
    samples=[]
    for sample in entry['expected_samples']:
        s=O.point(sample['s'])
        result={'observations':{name:complex(*pair) for name,pair in sample['observations'].items()}}
        values=binding(case,s,result)
        for path,equation in equations:
            try:
                left,right=expr(equation['left'],values),expr(equation['right'],values)
                error=abs(left-right)/max(1.,abs(left),abs(right))
                worst=max(worst,error); count+=1
                assert error<=TOLERANCE,f'equation residual {error:.6g}'
            except (AssertionError,KeyError,TypeError,ValueError,ZeroDivisionError,OverflowError) as exc:
                errors.append(f'{path} at s={sample["s"]}: {exc}')
        if transform is not None:
            try:
                got=O.value(transform,s)
                name=f"{'V' if request['quantity']=='voltage' else 'I'}[{request['component']}]"
                expected=values[name]
                error=abs(got-expected)/max(1.,abs(got),abs(expected))
                assert error<=TOLERANCE,f'answer residual {error:.6g}'
                samples.append({'s':sample['s'],'expected':[expected.real,expected.imag],'actual':[got.real,got.imag],'scaled_error':error})
            except (AssertionError,KeyError,TypeError,ValueError,ZeroDivisionError,OverflowError) as exc:
                errors.append(f'answer at s={sample["s"]}: {exc}')
    return {'id':entry['id'],'ok':not errors,'errors':errors,'equations':len(equations),
            'equation_evaluations':count,'max_equation_scaled_error':worst,'answer_samples':samples}


def mutated(payload,kind):
    out=deepcopy(payload); lesson=out.get('lesson',out)
    if kind=='intermediate_equation_plus_one':
        candidates=[eq for step in lesson['steps'][1:-1] for eq in step.get('math',[]) if eq['kind']=='equation']
        assert candidates,'need an actual intermediate displayed equation'
        eq=candidates[len(candidates)//2]
        eq['right']={'kind':'add','args':[eq['right'],{'kind':'number','coefficients':['1','0','0','0']}]}
    elif kind=='initial_condition_sign':
        states=lesson['laplace_inputs']['capacitor_voltages']+lesson['laplace_inputs']['inductor_currents']
        state=next(record for record in states if F(record['exact']))
        state['exact']=str(-F(state['exact']))
    elif kind=='impulse_area_unit':
        source=next(record for record in lesson['laplace_inputs']['sources'] if record['waveform']=='impulse')
        source['amplitude']['unit']=source['amplitude']['unit'].replace('*s','')
    else: raise ValueError(kind)
    return out


def selfcheck(cases):
    # Physical equations generated only by this oracle, never a product response.
    checked=0
    for entry in cases:
        case,_,_=parse_netlist(entry['netlist'])
        for sample in entry['expected_samples']:
            s=O.point(sample['s']); result=O.solve(case,s)
            for name,pair in sample['observations'].items():
                assert abs(result['observations'][name]-complex(*pair))<1e-12
            for c in case['components']:
                cid,k=c['id'],c['kind']; r=float(F(c['value']))
                v,i=result['observations'][f'V[{cid}]'],result['observations'][f'I[{cid}]']
                if k=='C': residual=i-(s*r*v-r*float(F(case['capacitor_voltages'][cid])))
                elif k=='L': residual=v-(s*r*i-r*float(F(case['inductor_currents'][cid])))
                elif k=='R': residual=v-r*i
                elif k=='V': residual=v-O.value(case['source_transforms'][cid],s)
                else: residual=i-O.value(case['source_transforms'][cid],s)
                assert abs(residual)<1e-9; checked+=1
    # Reversing a capacitor and an inductor with their states preserves node voltages.
    for a,b in zip(cases[0]['expected_samples'],cases[1]['expected_samples']):
        for name,pair in a['observations'].items():
            if name.startswith('V('): assert abs(complex(*pair)-complex(*b['observations'][name]))<1e-10
    # Swapping nonzero initial states really changes the observed response.
    assert any(abs(complex(*a['observations']['V[C1]'])-complex(*b['observations']['V[C1]']))>.1
               for a,b in zip(cases[0]['expected_samples'],cases[2]['expected_samples']))
    # AST falsifier independent of payload schema: initial law true; +1 false.
    n=lambda x:{'kind':'number','coefficients':[str(x),'0','0','0']}
    sym=lambda x:{'kind':'symbol','name':x}
    expr_ast={'kind':'add','args':[{'kind':'multiply','args':[sym('s'),n('1/3'),sym('V[C1]')]},n('-2/3')]}
    for sample in cases[0]['expected_samples']:
        case,_,_=parse_netlist(cases[0]['netlist'])
        values=binding(case,O.point(sample['s']),{'observations':{k:complex(*v) for k,v in sample['observations'].items()}})
        assert abs(expr(expr_ast,values)-values['I[C1]'])<1e-10
        bad={'kind':'add','args':[expr_ast,n(1)]}
        assert abs(expr(bad,values)-values['I[C1]'])>.99
    # Explicit analytic RC fixture validates the whole checker/mutation route.
    # It is an oracle self-test, never recorded as a real product response.
    rc=O.manual_cases()[0]
    rc_sources={'V1':{'quantity':'voltage','waveform':'step','amplitude':{'exact':'5','unit':'V'}}}
    rc_text=netlist(rc,rc_sources,{'quantity':'voltage','component':'C1'})
    rc_parsed,_,_=parse_netlist(rc_text)
    rc_entry={'id':'checker-analytic-self-test','netlist':rc_text,
        'expected_samples':[{'s':p,**O.serial(O.solve(rc_parsed,O.point(p)))} for p in O.POINTS]}
    eq=lambda left,right,unit='':{'kind':'equation','left':left,'right':right,'unit':unit,'label':''}
    multiply=lambda *args:{'kind':'multiply','args':list(args)}
    plus=lambda *args:{'kind':'add','args':list(args)}
    rc_payload={'laplace_inputs':{'initial_time':'0-',
        'sources':[{'component':'V1',**rc_sources['V1'],'transform':rc['source_transforms']['V1']}],
        'capacitor_voltages':[{'component':'C1','exact':'-2','unit':'V'}],'inductor_currents':[]},
        'steps':[{'math':[eq(sym('v0(C1)'),n(-2),'V')]},
                 {'math':[eq(sym('I[C1]'),plus(multiply(sym('s'),n('1/2'),sym('V[C1]')),n(1)),'A*s')]},
                 {'math':[eq(sym('V[C1]'),sym('V(a)'),'V*s')]}],
        'answer':{'quantity':'voltage','unit':'V*s','reference':'a → 0',
            'laplace_transform':{'variable':'s','coefficient_order':'ascending',**rc['analytic']['V[C1]']}},
        'verification':{'product_verified':False},'algebra':{'canonical_proof':False}}
    audit=compare_lesson(rc_entry,rc_payload)
    assert audit['ok'],audit
    for mutation in ['intermediate_equation_plus_one','initial_condition_sign']:
        assert not compare_lesson(rc_entry,mutated(rc_payload,mutation))['ok'],mutation
    return {'independent_branch_residual_checks':checked,'orientation_metamorphism':True,
            'initial_mapping_sensitivity':True,'ast_plus_one_mutation_rejected':True,
            'analytic_self_fixture_checked':True,'intermediate_equation_mutant_rejected':True,
            'initial_metadata_mutant_rejected':True}


def freeze():
    paths=[ROOT/'additive_cases.json',ROOT/'criteria.json']
    assert not any(p.exists() for p in paths),'freeze files already exist'
    cases=fixtures(); checks=selfcheck(cases)
    paths[0].write_bytes(encoded({'classification':'additive-post-kernel/pre-lesson-freeze','cases':cases}))
    criteria={
        'schema':'independent-laplace-lesson-audit.v1','frozen_at':datetime.now(timezone.utc).isoformat(),
        'model':'inherited/unknown','classification':'additive post-kernel tests; blind to new served lesson responses',
        'scope':'5 deterministic non-series-parallel RLC meshes, 2 C + 2 L, explicit step/impulse and 0- states',
        'old_holdout_untouched':OLD_HASHES,'sample_points':O.POINTS,'scaled_tolerance':TOLERANCE,
        'oracle':'frozen standard-library complex branch tableau; no production solver/math imports',
        'acceptance':['every step.math equation holds at all six independent tableau solutions',
            'answer transform agrees at all six samples','IC values, units, inventory and 0- metadata match original netlist',
            'source waveform, amplitude or impulse area, units and transform match original netlist',
            'no canonical_proof/product_verified promotion','mutated intermediate equation and nonzero IC rejected',
            'impulse area unit mutation rejected on impulse case'],
        'limitations':['finite numerical samples are not a symbolic identity proof','no inverse Laplace or time-domain claims',
            'no dimensional inference for substituted untyped numeric coefficients',
            'no claim about all 21 families; additive mesh corpus is not the former 80-case holdout',
            'unknown AST/symbol or missing metadata fails closed; ABI adaptation must be recorded separately'],
        'selfcheck':checks,
        'frozen_files':{name:sha((ROOT/name).read_bytes()) for name in ['checker.py','run_product.py','additive_cases.json']},
        'rollback':'outside-repo evidence only; no product changes','index_sync':'INDEX_SYNC_DEFERRED',
    }
    paths[1].write_bytes(encoded(criteria))
    print(json.dumps({'criteria_sha256':sha(paths[1].read_bytes()),**criteria},indent=2))


def integrity():
    criteria=json.loads((ROOT/'criteria.json').read_text())
    for name,digest in criteria['frozen_files'].items(): assert sha((ROOT/name).read_bytes())==digest,f'changed frozen file: {name}'
    cases=json.loads((ROOT/'additive_cases.json').read_text())['cases']
    assert encoded({'classification':'additive-post-kernel/pre-lesson-freeze','cases':fixtures()})==(ROOT/'additive_cases.json').read_bytes()
    assert selfcheck(cases)==criteria['selfcheck']
    return cases,criteria

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--freeze',action='store_true'); args=parser.parse_args()
    if args.freeze: freeze()
    else:
        cases,criteria=integrity(); print(json.dumps({'integrity':'PASS','cases':len(cases),'criteria_sha256':sha((ROOT/'criteria.json').read_bytes())}))
