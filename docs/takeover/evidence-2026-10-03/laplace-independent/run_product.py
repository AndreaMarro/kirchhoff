"""Load a product adapter only after checking the frozen independent oracle.

Adapter ABI: solve_case(case) -> {outcome:'solved', observations:{name:RF}} or
{outcome:'refusal', cause:...}. RF is {numerator:[str], denominator:[str]},
ascending powers of s. The adapter must not calculate any missing observable.
"""
from __future__ import annotations
from copy import deepcopy
from fractions import Fraction as F
import importlib.util
import argparse
import json
from pathlib import Path
import sys

from oracle import ROOT, check, point, value, sha


def trim(polynomial):
    result = list(polynomial)
    while len(result)>1 and result[-1]==0: result.pop()
    return result or [F(0)]


def multiply(left,right):
    result = [F(0)]*(len(left)+len(right)-1)
    for i,a in enumerate(left):
        for j,b in enumerate(right): result[i+j] += a*b
    return trim(result)


def remainder(left,right):
    result = trim(left)
    while any(result) and len(result)>=len(right):
        offset,factor = len(result)-len(right),result[-1]/right[-1]
        for index,coefficient in enumerate(right): result[offset+index] -= factor*coefficient
        result = trim(result)
    return result


def canonical(transform):
    assert set(transform)=={'numerator','denominator'}, 'Unknown rational-function wire fields'
    num,den = [list(map(F,transform[key])) for key in ('numerator','denominator')]
    assert num and den and num==trim(num) and den==trim(den), 'Noncanonical polynomial coefficients'
    assert den[-1]==1, 'Denominator is not monic'
    if not any(num): assert num==[0] and den==[1], 'Noncanonical zero'
    a,b = num[:],den[:]
    while any(b): a,b=b,remainder(a,b)
    assert len(trim(a))==1, 'Numerator/denominator share a nonconstant factor'


def equivalent(left,right):
    ln,ld = [list(map(F,left[key])) for key in ('numerator','denominator')]
    rn,rd = [list(map(F,right[key])) for key in ('numerator','denominator')]
    return multiply(ln,rd)==multiply(rn,ld)


def exact_complex_polynomial(coefficients, coordinates):
    sr,si = map(F,coordinates)
    re,im = F(0),F(0)
    for coefficient in reversed(coefficients):
        re,im = re*sr-im*si+F(coefficient), re*si+im*sr
    return re,im


def compare(case,response,samples):
    assert response.get('outcome')=='solved', 'Finite supported case was not solved'
    assert response.get('product_verified') is not True, 'Unexpected product VERIFIED promotion'
    assert response.get('verification',{}).get('product_verified') is not True, 'Unexpected nested VERIFIED promotion'
    observations = response['observations']
    assert set(observations)==set(samples[0]['observations']), 'Missing or extra physical observables'
    for transform in observations.values(): canonical(transform)
    maximum = 0.
    for row in samples:
        s = point(row['s'])
        for name,expected in row['observations'].items():
            actual = value(observations[name],s)
            wanted = complex(*expected)
            error = abs(actual-wanted)/max(1,abs(wanted))
            assert error<=3e-9,(name,row['s'],actual,wanted,error)
            maximum = max(maximum,error)
    for name,analytic in case['analytic'].items():
        assert equivalent(observations[name],analytic), f'Exact analytic mismatch: {name}'
    for pole in case.get('pole_checks',[]):
        transform = observations[pole['observation']]
        assert exact_complex_polynomial(transform['denominator'],pole['s'])==(0,0), 'Expected pole absent'
        assert exact_complex_polynomial(transform['numerator'],pole['s'])!=(0,0), 'Expected pole cancels'
    return maximum


def source_manifest(repo):
    paths = sorted((repo/'src').rglob('*.py'))+[repo/'pyproject.toml']
    entries = [{'path':str(path.relative_to(repo)),'bytes':path.stat().st_size,'sha256':sha(path.read_bytes())}
               for path in paths if path.is_file()]
    return {'files':entries,'sha256':sha(json.dumps(entries,sort_keys=True,separators=(',',':')).encode())}


def staging_manifest(directory):
    entries = [{'path':path.name,'bytes':path.stat().st_size,'sha256':sha(path.read_bytes())}
               for path in sorted(directory.glob('*.py'))]
    return {'files':entries,'sha256':sha(json.dumps(entries,sort_keys=True,separators=(',',':')).encode())}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--adapter-file',type=Path,required=True)
    parser.add_argument('--staging-dir',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    responses_path = args.output.with_suffix('.responses.jsonl')
    if args.output.exists() or responses_path.exists(): raise SystemExit('Refusing to overwrite previous evidence')
    content,expected = check()
    source_before = source_manifest(args.repo.resolve())
    staging_before = staging_manifest(args.staging_dir.resolve())
    sys.path.insert(0,str(args.repo.resolve()/'src'))
    sys.path.insert(0,str(args.staging_dir.resolve()))
    spec = importlib.util.spec_from_file_location('laplace_product_adapter',args.adapter_file.resolve())
    assert spec and spec.loader
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    rows,failures,mutations = [],0,[]
    for case in content['cases']:
        row = {'id':case['id'],'status':'failed'}
        samples = expected['samples'][case['id']]
        try:
            response = adapter.solve_case(deepcopy(case))
            serialized = (json.dumps({'case_id':case['id'],'response':response},ensure_ascii=False,sort_keys=True,allow_nan=False)+'\n').encode()
            with responses_path.open('ab') as stream: stream.write(serialized)
            row.update(response_sha256=sha(serialized),response_bytes=len(serialized))
            if case['require_solved']:
                row.update(status='passed',max_scaled_error=compare(case,response,samples))
                # These declared response mutations are not production-code
                # mutations. The independent comparator must reject them.
                if case['id']=='rc_step/base':
                    for label in ['capacitor_current_sign','missing_initial_contribution','extra_s']:
                        changed = deepcopy(response)
                        target = changed['observations']['I[C1]']
                        if label=='capacitor_current_sign': target['numerator']=[str(-F(v)) for v in target['numerator']]
                        elif label=='missing_initial_contribution': target['numerator'][0]=str(F(target['numerator'][0])+1)
                        else: target['numerator']=['0',*target['numerator']]
                        try: compare(case,changed,samples)
                        except (AssertionError,ZeroDivisionError): mutations.append({'mutation':label,'rejected':True})
                        else: raise AssertionError(f'Comparator accepted mutation {label}')
            else:
                assert response.get('outcome')=='refusal' and response.get('cause'), 'Degenerate input did not refuse explicitly'
                assert not response.get('observations'), 'Refusal includes solved observables'
                row.update(status='expected_refusal',cause=response['cause'],expected=samples[0]['status'])
        except (ValueError,TypeError,KeyError,ZeroDivisionError) as error:
            # Typed input errors are part of the declared library boundary,
            # not evidence of a numerical failure or an HTTP response.
            invalid = samples[0]['status'].startswith('invalid_') or samples[0]['status']=='missing_reference'
            row.update(status='expected_input_error' if invalid else 'failed',error=f'{type(error).__name__}: {error}')
            if not invalid: failures += 1
        except Exception as error:
            row['error']=f'{type(error).__name__}: {error}';failures += 1
        rows.append(row)
        print(f'{case["id"]}: {row["status"]}',flush=True)
    source_after = source_manifest(args.repo.resolve())
    staging_after = staging_manifest(args.staging_dir.resolve())
    if source_after!=source_before: failures += 1
    if staging_after!=staging_before: failures += 1
    report = {'model':'inherited/unknown','seed':content['seed'],'case_count':len(rows),'failures':failures,
              'cases_sha256':expected['cases_sha256'],'oracle_sha256':expected['oracle_sha256'],
              'expected_sha256':sha((ROOT/'expected.json').read_bytes()),'runner_sha256':sha(Path(__file__).read_bytes()),
              'adapter_sha256':sha(args.adapter_file.read_bytes()),'source_manifest_before':source_before,
              'source_manifest_after':source_after,'source_unchanged':source_before==source_after,
              'staging_manifest_before':staging_before,'staging_manifest_after':staging_after,
              'staging_unchanged':staging_before==staging_after,
              'responses_sha256':sha(responses_path.read_bytes()) if responses_path.exists() else None,
              'assurance_scope':'kernel rational response; no time inversion, lesson/PDF or product verification inferred',
              'now_a_regression_suite':True,'response_mutations':mutations,'results':rows}
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({key:value for key,value in report.items() if key not in
                     ('results','source_manifest_before','source_manifest_after','staging_manifest_before','staging_manifest_after')},indent=2))
    return int(failures>0)


if __name__=='__main__': raise SystemExit(main())
