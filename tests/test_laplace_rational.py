"""Leggi del campo e oracoli numerici Fraction esterni alla normalizzazione."""
from fractions import Fraction as F
from dataclasses import FrozenInstanceError
import json
import random

import pytest

from kirchhoff.domain.laplace_rational import RationalFunction as RF, ZERO, ONE, S


def raw_value(numerator, denominator, x):
    # Valuta i polinomi originali per potenze, senza Horner o helper del campo.
    top=sum((c*x**i for i,c in enumerate(numerator)),F(0))
    bottom=sum((c*x**i for i,c in enumerate(denominator)),F(0))
    return top/bottom


def test_gcd_cancellation_and_monic_denominator_define_unique_normal_form():
    cancelled=(S-1)*(S+2)/((S-1)*(2*S+6))
    assert cancelled.to_json()=={'numerator':['1','1/2'],'denominator':['3','1']}
    assert cancelled==RF((F(-2),F(-1)),(F(-6),F(-2)))
    assert cancelled.evaluate(F(1))==F(3,8)  # discontinuità eliminabile cancellata
    assert ZERO/(S-1)==ZERO
    assert (S*S-1)/(S-1)==S+1
    assert S/S==ONE
    assert RF((F(0),F(0)),(F(7),F(2)))==ZERO


def test_arithmetic_matches_unreduced_exact_values_for_frozen_random_polynomials():
    rng=random.Random(20261003)
    for _ in range(18):
        n1=tuple(F(rng.randint(-8,8),rng.randint(1,5)) for _ in range(3))
        n2=tuple(F(rng.randint(1,8),rng.randint(1,5)) for _ in range(3))
        d1=tuple(F(rng.randint(1,8),rng.randint(1,5)) for _ in range(3))
        d2=tuple(F(rng.randint(1,8),rng.randint(1,5)) for _ in range(2))
        left,right=RF(n1,d1),RF(n2,d2)
        for x in (F(0),F(1,3),F(2),F(7,2)):
            a,b=raw_value(n1,d1,x),raw_value(n2,d2,x)
            for actual,expected in ((left+right,a+b),(left-right,a-b),(left*right,a*b),(left/right,a/b),
                                    (2+left,2+a),(2-left,2-a),(3*left,3*a),(2/right,2/b)):
                assert actual.evaluate(x)==expected
                assert actual.denominator[-1]==1
            assert (left+right)*(left-right)==left**2-right**2


def test_zero_inverse_poles_and_finite_algebraic_limits_are_distinct():
    from kirchhoff.domain.laplace_rational import _divide
    assert bool(ONE) and not ZERO
    assert (S+2)**0==1
    assert (S+2)**-2==1/(S*S+4*S+4)
    assert (3*S/(S+2)).limit_at_infinity()==3
    assert (1/(S+2)).limit_at_infinity()==0
    assert (2/(S+2)).limit_at_zero()==1
    with pytest.raises(ValueError,match='limite finito'):(S+1).limit_at_infinity()
    for operation in (lambda:ZERO.inverse(),lambda:ONE/ZERO,lambda:RF((F(1),),(F(0),)),
                      lambda:(ONE/(S+1)).evaluate(F(-1)),lambda:(ONE/S).limit_at_zero(),
                      lambda:_divide((F(1),),(F(0),))):
        with pytest.raises(ZeroDivisionError):operation()


def test_constant_hash_matches_fraction_and_values_are_immutable():
    value=RF.of(F(2,3))
    assert value==F(2,3) and hash(value)==hash(F(2,3))
    assert len({value,F(2,3)})==1
    assert value!=object() and value!=True
    assert hash(S)==hash(RF((F(0),F(1))))
    with pytest.raises(FrozenInstanceError):value.numerator=(F(3),)
    assert RF.of(3).proper and not S.proper


@pytest.mark.parametrize('bad',[1.0,'1',True,complex(1,0),None])
def test_no_float_or_implicit_string_enters_the_field(bad):
    with pytest.raises(TypeError):RF.of(bad)
    with pytest.raises(TypeError):ONE+bad
    with pytest.raises(TypeError):S.evaluate(bad)


def test_raw_constructor_and_powers_reject_non_exact_shapes():
    for args in (([],(F(1),)),((1,),(F(1),)),((F(1),),(1,))):
        with pytest.raises(TypeError):RF(*args)
    with pytest.raises(ValueError):RF(())
    with pytest.raises(ValueError):RF((F(1),),())
    with pytest.raises(ValueError):RF.polynomial()
    with pytest.raises(TypeError):S**F(1,2)
    with pytest.raises(TypeError):S**True


def test_serialization_is_coefficients_only_and_rejects_noncanonical_payloads():
    value=(S+F(2,3))/(S*S+F(4,5)*S+F(7,8))
    wire=json.loads(json.dumps(value.to_json()))
    assert RF.from_json(wire)==value
    assert set(wire)=={'numerator','denominator'}
    for bad in [None,{},dict(wire,expression='s+1'),{'numerator':[1],'denominator':['1']},
                {'numerator':['1/0'],'denominator':['1']},{'numerator':['s'],'denominator':['1']},
                {'numerator':['2/4'],'denominator':['1']},{'numerator':['1','0'],'denominator':['1']},
                {'numerator':['2'],'denominator':['2']},{'numerator':[],'denominator':['1']},
                {'numerator':['1'],'denominator':['0']}]:
        with pytest.raises((ValueError,ZeroDivisionError)):RF.from_json(bad)
