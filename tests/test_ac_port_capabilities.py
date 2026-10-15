"""The published port capability must traverse the actual lesson entrypoint."""
from kirchhoff.pipeline.capabilities import product_capabilities, SOLVE_DESCRIPTION


def test_ac_impedance_capability_exposes_the_real_test_current_path():
    text='@ac 2 rad/s\nR1 a b 3 ohm\nL1 b 0 2 henry\n? impedance a 0'
    capability=product_capabilities(text)
    assert 'impedance' in capability['ac_scope']['quantities']
    assert capability['ac_scope']['port_methods']==['auto','test_current']
    assert capability['ac_scope']['port_impedance'] is True
    assert capability['product_verified'] is False
    assert capability['circuit']['outcome']=='solved'
    assert set(capability['circuit']['available_methods'])=={'auto','test_current'}
    assert '? impedance' in SOLVE_DESCRIPTION


def test_ac_impedance_capability_does_not_promote_an_invalid_dc_request():
    result=product_capabilities('R1 a 0 3 ohm\n? impedance a 0')
    assert result['circuit']['outcome']=='invalid'
    assert result['circuit']['available_methods']==[]
