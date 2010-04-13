import pandokia.helpers.minipyt as mpt
import nose.tools as nt
import time

def test_p() :
    print "We are here!"
    assert True

def test_f() :
    print "We are here!"
    assert False

def test_e() :
    print "We are here!"
    raise Exception('Bomb')

@mpt.test
def minipyt_decorated() :
    print "We are here!"
    assert True

@mpt.nottest
def test_not_a_test_minipyt() :
    print "We are here!"
    # there should be no test report for this one
    raise Exception('Bomb')

@mpt.test
def fn_with_tda() :
    print "We are here!"
    tda['tda_1'] = 1
    tda['tda_2'] = 2


@mpt.test
def fn_with_tra() :
    print "(Do you hear a Who?)"
    tra['tra_1'] = 1
    tra['tra_2'] = 2

@mpt.test
def fn_with_attributes() :
    print "We are here!"
    tda['tda_1'] = 1
    tda['tda_2'] = 2
    tra['tra_1'] = 1
    tra['tra_2'] = 2
    assert False

@nt.istest
def fn_nose_decorated() :
    print "We are here!"

@nt.nottest
def test_nose_nottest() :
    print "We are here!"
    assert False

@nt.raises(ValueError)
def test_nose_raises_not() :
    pass

@nt.raises(ValueError)
def test_nose_raises_does() :
    raise ValueError('Expect ValueError')

@nt.timed(1)
def test_nose_timed_ok() :
    pass

@nt.timed(.1)
def test_nose_timed_nok() :
    time.sleep(1)

@nt.timed(1)
def test_nose_timed_asserts() :
    assert False

@nt.timed(1)
def test_nose_timed_asserts() :
    assert False

@nt.timed(1)
def test_nose_timed_exc() :
    raise ValueError('value error')

print "We are here!"
