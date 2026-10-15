"""Mechanical binding to the separately frozen staging kernel; no solving here."""
from fractions import Fraction as F
from dataclasses import asdict
from kirchhoff.domain.ir import IR, Component
from kirchhoff.domain.refusal import Refusal
from laplace import solve_laplace, LaplaceSolution
from laplace_rational import RationalFunction as RF

KINDS = {'R':'resistor','L':'inductor','C':'capacitor','V':'voltage_source_dc','I':'current_source_dc'}


def solve_case(case):
    components = tuple(Component.of(c['id'],KINDS[c['kind']],(c['p'],c['q']),F(c['value']),c['id'])
                       for c in case['components'])
    nodes = tuple(dict.fromkeys(['0',*(node for c in components for node in c.terminals)]))
    circuit = IR('1.0.0','laplace','generated',nodes,components,())
    sources = {cid:RF(tuple(map(F,transform['numerator'])),tuple(map(F,transform['denominator'])))
               for cid,transform in case['source_transforms'].items()}
    result = solve_laplace(circuit,source_transforms=sources,
                          capacitor_voltages={cid:F(v) for cid,v in case['capacitor_voltages'].items()},
                          inductor_currents={cid:F(v) for cid,v in case['inductor_currents'].items()})
    if isinstance(result,Refusal):
        return {'outcome':'refusal','cause':result.cause,'kernel_wire':asdict(result)}
    assert isinstance(result,LaplaceSolution)
    # V(0)=0 is the definition of the reference coordinate. Every other voltage
    # and every branch current/voltage comes directly from the kernel result.
    observations = {'V(0)':RF.of(0).to_json()}
    observations.update({f'V({node})':result.solution[f'V({node})'].to_json() for node in nodes if node!='0'})
    for branch in result.branches:
        observations[f'V[{branch.component}]'] = branch.voltage.to_json()
        observations[f'I[{branch.component}]'] = branch.current.to_json()
    wire = result.to_json()
    assert wire['canonical_proof'] is False
    return {'outcome':'solved','observations':observations,'kernel_wire':wire,'canonical_proof':wire['canonical_proof']}
