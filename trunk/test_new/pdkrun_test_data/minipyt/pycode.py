import pandokia.helpers.pycode as pycode

with pycode.test( 'pass_test' ) as t :
    t.tda['yes']='yes'

with pycode.test( 'fail_test' ) as t :
    t.tda['yes']='yes'
    t.tra['no'] ='no'
    assert 0

with pycode.test( 'error_test' ) as t :
    t.tda['yes']='yes'
    raise Exception('expect this error')

with pycode.setup( 'nest' ) as t :
    print "nest 1"
    with pycode.test( 'lev1' ) as t :
        print "lev1"
        with pycode.test( 'lev2' ) as t :
            print "lev2"
        print "lev1"
    print "nest1"

def test_plover() :
    print "just a plover"
    with pycode.test( 'egg' ) :
        print "An emerald the size of a plover's egg"
        with pycode.test( 'hatch' ) :
            # this test is named "plover.egg.hatch"
            assert 1

    with pycode.test( 'emerald' ) :
        print "just the emerald"

    print "that laid an egg"

def test_banana() :
    print "yellow"
    with pycode.test( 'fruit' ) :
        print "fruit"

    with pycode.test( 'cesium' ) as e :
        e.tra['cesium'] = 'high'
        assert 0

    with pycode.test( 'potassium' ) as e :
        e.tra['potassium'] = 'high'

        with pycode.test( 'radioactive' ) :
            pass

    with pycode.test( 'chocolate_coated' ) :
        assert 'yum'

