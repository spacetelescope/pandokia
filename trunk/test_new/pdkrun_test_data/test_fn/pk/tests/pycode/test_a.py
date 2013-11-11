import pandokia.helpers.pycode as pycode

with pycode.test( 'test_p_with' ) as t:
    pass

with pycode.test( 'test_f_with' ) as t:
    assert 0

with pycode.test( 'test_e_with' ) as t:
    raise Exception()

