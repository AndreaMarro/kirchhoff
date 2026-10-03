"""Additional post-opening contract checks; not part of the original holdout."""
from decimal import Decimal, localcontext
from fractions import Fraction as F
import json
from pathlib import Path

root = Path(__file__).resolve().parent
cases = {case['id']: case for case in json.loads((root/'cases.json').read_text())['cases']}
checked, builds = [], set()
for line in (root/'result.lessons.jsonl').read_text().splitlines():
    row = json.loads(line)
    lesson, identity = row['lesson'], row['case_id']
    if lesson['outcome'] != 'solved': continue
    answer, representation = lesson['answer'], lesson['answer']['complex_impedance']
    p, q = cases[identity]['netlist'].splitlines()[-1].split()[-2:]
    assert answer['reference'] == f'{p} → {q}', identity
    a,b,c,d = map(F, representation['coefficients'])
    # Rational omega/R/L/C and a real unit test source imply Z in Q(j), even
    # when the original independent sources had irrational phasor components.
    assert b == 0 and c == 0, (identity, 'source phase contamination')
    assert F(representation['real_exact']) == a, identity
    assert F(representation['imaginary_exact']) == d, identity
    assert answer['math']['coefficients'] == representation['coefficients'], identity
    with localcontext() as context:
        context.prec = 80
        for name, value in [('real',a), ('imaginary',d)]:
            actual = Decimal(representation[f'{name}_decimal'])
            exact = Decimal(value.numerator)/Decimal(value.denominator)
            if exact == 0: assert actual == 0, identity
            else:
                half_ulp = Decimal(1).scaleb(exact.adjusted()-7)/2
                assert abs(actual-exact) <= half_ulp + Decimal('1e-65'), (identity,name,actual,exact)
    assert lesson['verification']['product_verified'] is False, identity
    builds.add(lesson['lesson_build'])
    checked.append(identity)
result = {'post_opening_checks': True, 'frozen_expected_changed': False,
          'checked_solved_lessons':len(checked), 'checks':['requested port reference','impedance in Q(j)',
          'exact rectangular fields','math AST matches coefficients','8 significant decimal digits','no VERIFIED promotion'],
          'lesson_builds':sorted(builds), 'passed':True}
output = root/'additional_checks.json'
if output.exists(): raise SystemExit('Refusing to overwrite previous checks')
output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
