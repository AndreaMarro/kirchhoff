"""Formule RC/RL/RLC indipendenti, termini iniziali e rifiuti del nuovo kernel."""
from dataclasses import replace
from fractions import Fraction as F
import json

import pytest

from kirchhoff.domain.ir import IR, Component
from kirchhoff.domain.refusal import Refusal
from kirchhoff.domain import laplace
from kirchhoff.domain.laplace import assemble_laplace, solve_laplace, LaplaceSolution
from kirchhoff.domain.laplace_rational import RationalFunction as RF, ZERO, S


KINDS={'R':'resistor','L':'inductor','C':'capacitor','V':'voltage_source_dc','I':'current_source_dc'}


def circuit(*entries):
    components=tuple(Component.of(cid,KINDS[cid[0]],(p,q),F(value),cid) for cid,p,q,value in entries)
    nodes=tuple(dict.fromkeys(['0',*(node for c in components for node in c.terminals)]))
    return IR('1.0.0','laplace','generated',nodes,components,())


def rc(r=2,c=F(1,3)):
    return circuit(('V1','e','0',10),('R1','e','a',r),('C1','a','0',c))


@pytest.mark.parametrize('v0',[F(0),F(4),F(-3,2)])
def test_rc_step_and_initial_voltage_follow_direct_first_order_ode(v0):
    r,c,e=F(2),F(1,3),F(10)
    solved=solve_laplace(rc(r,c),source_transforms={'V1':e/S},capacitor_voltages={'C1':v0},inductor_currents={})
    assert isinstance(solved,LaplaceSolution)
    expected=(e/S+r*c*v0)/(1+r*c*S)
    assert solved.branch('C1').voltage==expected
    assert solved.branch('C1').current==(e/S-expected)/r
    assert (S*expected).limit_at_infinity()==v0
    assert (S*expected).limit_at_zero()==e  # R,C positivi: il polo è -1/(RC).
    assert (S*solved.branch('C1').current).limit_at_infinity()==(e-v0)/r


def test_rc_discharge_and_reversed_capacitor_initial_sign():
    ir=circuit(('R1','a','0',3),('C1','a','0',F(2,5)))
    value=F(7)
    solved=solve_laplace(ir,source_transforms={},capacitor_voltages={'C1':value},inductor_currents={})
    expected=value/(S+F(5,6))
    assert solved.branch('C1').voltage==expected
    assert solved.branch('C1').current==-expected/3
    reversed_ir=replace(ir,components=(ir.components[0],replace(ir.components[1],terminals=('0','a'))))
    reversed_solution=solve_laplace(reversed_ir,source_transforms={},capacitor_voltages={'C1':-value},inductor_currents={})
    assert reversed_solution.solution['V(a)']==solved.solution['V(a)']
    assert reversed_solution.branch('C1').voltage==-expected
    assert reversed_solution.branch('C1').current==expected/3


@pytest.mark.parametrize('i0',[F(0),F(3),F(-7,4)])
def test_rl_step_includes_negative_L_i0_on_kvl_rhs(i0):
    r,l,e=F(5),F(2,3),F(12)
    ir=circuit(('V1','e','0',e),('R1','e','a',r),('L1','a','0',l))
    solved=solve_laplace(ir,source_transforms={'V1':e/S},capacitor_voltages={},inductor_currents={'L1':i0})
    expected=(e/S+l*i0)/(r+l*S)
    assert solved.branch('L1').current==expected
    assert solved.branch('L1').voltage==l*S*expected-l*i0
    assert solved.branch('V1').current==-expected
    assert (S*expected).limit_at_infinity()==i0
    assert (S*expected).limit_at_zero()==e/r
    row=solved.system.row_labels.index('KVL(L1)')
    assert solved.system.rhs[row]==-l*i0
    index=next(i for i,v in enumerate(solved.system.variables) if v.name=='I(L1)')
    assert solved.system.matrix[row][index]==-l*S


def test_rl_natural_response_and_reversed_inductor_reference():
    ir=circuit(('R1','a','0',3),('L1','a','0',2))
    solved=solve_laplace(ir,source_transforms={},capacitor_voltages={},inductor_currents={'L1':F(5)})
    expected=5/(S+F(3,2))
    assert solved.branch('L1').current==expected
    assert solved.branch('L1').voltage==-3*expected
    reverse=replace(ir,components=(ir.components[0],replace(ir.components[1],terminals=('0','a'))))
    other=solve_laplace(reverse,source_transforms={},capacitor_voltages={},inductor_currents={'L1':F(-5)})
    assert other.branch('R1')==solved.branch('R1')
    assert other.branch('L1').current==-expected


@pytest.mark.parametrize('v0,i0',[(F(0),F(0)),(F(4),F(2)),(F(-2,3),F(7,5))])
def test_series_rlc_second_order_with_both_initial_states(v0,i0):
    r,l,c,e=F(3),F(2),F(1,5),F(11)
    ir=circuit(('V1','e','0',e),('R1','e','a',r),('L1','a','b',l),('C1','b','0',c))
    solved=solve_laplace(ir,source_transforms={'V1':e/S},capacitor_voltages={'C1':v0},inductor_currents={'L1':i0})
    expected=(e+l*i0*S-v0)/(l*S*S+r*S+1/c)
    voltage=expected/(c*S)+v0/S
    assert solved.branch('L1').current==expected
    assert solved.branch('C1').voltage==voltage
    assert (S*expected).limit_at_infinity()==i0
    assert (S*voltage).limit_at_infinity()==v0
    assert (S*expected).limit_at_zero()==0
    assert (S*voltage).limit_at_zero()==e  # Secondo ordine stabile con R,L,C positivi.


def test_observable_rc_matrix_rhs_and_json_keep_exact_coefficients_and_units():
    solved=solve_laplace(rc(),source_transforms={'V1':10/S},capacitor_voltages={'C1':F(4)},inductor_currents={})
    system=solved.system
    assert [v.name for v in system.variables]==['V(e)','V(a)','I(V1)']
    assert system.matrix==((RF.of(F(1,2)),RF.of(F(-1,2)),RF.of(1)),
                           (RF.of(F(-1,2)),RF.of(F(1,2))+S/3,ZERO),
                           (RF.of(1),ZERO,ZERO))
    assert system.rhs==(ZERO,RF.of(F(4,3)),10/S)
    wire=json.loads(json.dumps(solved.to_json()))
    assert wire['canonical_proof'] is False
    assert wire['system']['initial_time']=='0-'
    assert wire['system']['variables'][0]['unit']=='V*s'
    assert wire['branches'][2]['current']['unit']=='A*s'
    for branch in wire['branches']:
        assert RF.from_json(branch['voltage']['value'])==solved.branch(branch['component']).voltage
        assert RF.from_json(branch['current']['value'])==solved.branch(branch['component']).current
    with pytest.raises(KeyError):solved.branch('unknown')


def test_current_source_floating_voltage_and_general_proper_inputs():
    # V1 impone Va-Vb=E(s); supernodo: Va/2+Vb/3=J(s).
    ir=circuit(('V1','a','b',99),('I1','0','a',99),('R1','a','0',2),('R2','b','0',3))
    e,j=7/(S+2),5/S
    solved=solve_laplace(ir,source_transforms={'V1':e,'I1':j},capacitor_voltages={},inductor_currents={})
    va=(j+e/3)/F(5,6)
    assert solved.solution['V(a)']==va
    assert solved.solution['V(b)']==va-e
    assert solved.branch('I1').current==j
    assert solved.branch('V1').current==j-va/2
    # I valori nominali nell'IR non reinterpretano gli ingressi trasformati espliciti.
    altered=replace(ir,components=tuple(replace(c,value=replace(c.value,amount=F(123))) if c.id in {'V1','I1'} else c for c in ir.components))
    assert solve_laplace(altered,source_transforms={'V1':e,'I1':j},capacitor_voltages={},inductor_currents={})==solved


def test_zero_state_zero_input_and_impulse_are_explicit_not_inferred():
    zero=solve_laplace(rc(),source_transforms={'V1':ZERO},capacitor_voltages={'C1':F(0)},inductor_currents={})
    assert all(not b.voltage and not b.current for b in zero.branches)
    impulse=solve_laplace(rc(),source_transforms={'V1':RF.of(5)},capacitor_voltages={'C1':F(0)},inductor_currents={})
    assert impulse.branch('C1').voltage==5/(1+F(2,3)*S)
    # Un ingresso impulsivo ideale può produrre una derivata d'impulso in uscita.
    direct=circuit(('V1','a','0',0),('C1','a','0',2))
    distribution=solve_laplace(direct,source_transforms={'V1':RF.of(3)},capacitor_voltages={'C1':F(4)},inductor_currents={})
    assert distribution.branch('C1').current==6*S-8
    assert not distribution.branch('C1').current.proper


def test_initial_state_maps_are_complete_exact_and_never_silently_zero():
    valid=dict(source_transforms={'V1':10/S},capacitor_voltages={'C1':F(0)},inductor_currents={})
    for changes in ({'source_transforms':{}},{'capacitor_voltages':{}},{'inductor_currents':{'Lx':F(0)}},
                    {'source_transforms':{'V1':10/S,'Ix':ZERO}}):
        with pytest.raises(ValueError,match='tutte e sole'):solve_laplace(rc(),**(valid|changes))
    for changes in ({'source_transforms':{'V1':F(10)}},{'capacitor_voltages':{'C1':0}},
                    {'capacitor_voltages':{'C1':0.0}},{'inductor_currents':[]}):
        with pytest.raises(TypeError):solve_laplace(rc(),**(valid|changes))
    with pytest.raises(TypeError):solve_laplace(None,**valid)


def test_domain_and_improper_source_limits_are_refusals():
    args=dict(source_transforms={'V1':10/S},capacitor_voltages={'C1':F(0)},inductor_currents={})
    for ir in (replace(rc(),domain='dc'),replace(rc(),omega=F(3))):
        refused=solve_laplace(ir,**args)
        assert isinstance(refused,Refusal) and refused.cause=='claim_unsupported'
    refused=solve_laplace(rc(),**(args|{'source_transforms':{'V1':S}}))
    assert isinstance(refused,Refusal) and refused.subject=='V1'
    empty=IR('1.0.0','laplace','generated',('0',),(),())
    assert solve_laplace(empty,source_transforms={},capacitor_voltages={},inductor_currents={}).cause=='topology'


@pytest.mark.parametrize('ir,inputs',[
    (circuit(('I1','a','0',0)),{'I1':ZERO}),
    (circuit(('V1','a','0',1),('V2','a','0',2)),{'V1':1/S,'V2':2/S}),
    (circuit(('V1','a','0',1),('V2','a','0',1)),{'V1':1/S,'V2':1/S}),
    (circuit(('R1','a','b',2)),{}),
])
def test_identically_singular_system_is_a_refusal(ir,inputs):
    refused=solve_laplace(ir,source_transforms=inputs,capacitor_voltages={},inductor_currents={})
    assert isinstance(refused,Refusal) and refused.cause=='unsolvable'


def test_undamped_lc_has_poles_but_is_not_identically_singular_in_Q_s():
    ir=circuit(('L1','a','0',2),('C1','a','0',F(1,2)))
    solved=solve_laplace(ir,source_transforms={},capacitor_voltages={'C1':F(4)},inductor_currents={'L1':F(0)})
    assert solved.branch('C1').voltage==4*S/(S*S+1)
    # s*V(s) tends to zero at s=0, but v(t)=4*cos(t) has no final value.
    # The API reports an algebraic limit only and has no final_value inference.
    assert (S*solved.branch('C1').voltage).limit_at_zero()==0
    assert 'final_value' not in solved.to_json()


def test_corrupt_solver_or_recovered_branch_fails_residuals(monkeypatch):
    ir=rc();args=dict(source_transforms={'V1':10/S},capacitor_voltages={'C1':F(4)},inductor_currents={})
    good=solve_laplace(ir,**args)
    monkeypatch.setattr(laplace,'solve_linear',lambda matrix,rhs:[ZERO]*len(rhs))
    assert solve_laplace(ir,**args).cause=='residual'
    branches=list(good.branches);branches[0]=replace(branches[0],current=-branches[0].current)
    assert laplace._check_residuals(ir,good.system,good.values,branches,**args).subject=='0'
    branches=list(good.branches);branches[2]=replace(branches[2],voltage=-branches[2].voltage)
    assert laplace._check_residuals(ir,good.system,good.values,branches,**args).subject=='C1'
