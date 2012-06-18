def test_pytest( verbose=False ) :
    #
    import os, sys, pytest

    # import the test package
    test_pkg = __name__ + '.tests.pytest'
    exec( "import %s" % test_pkg )

    # find the directory where the test package lives
    dir = os.path.dirname( sys.modules[test_pkg].__file__ )

    # assemble the py.test args
    args = [ dir ]

    # run py.test
    try :
        return pytest.main( args )
    except SystemExit as e :
        return e.code

def test_nose( verbose=False ) :
    import os, sys, nose

    # import the test package
    test_pkg = __name__ + '.tests.nose'
    exec( "import %s" % test_pkg )

    # find the directory where the test package lives
    xdir = os.path.dirname( sys.modules[test_pkg].__file__ )

    # get the name of the test package
    argv = [ 'nosetests', xdir ]

    # run nose
    try :
        return nose.main( argv = argv )
    except SystemExit as e :
        return e.code

def test_pycode( verbose=False ) :
    import pandokia.helpers.pycode as pycode

    return pycode.package_test(
        parent = __name__,
        test_package = 'tests.pycode',
        test_modules = [ 'test_a', ],
        verbose = verbose,
    )

def test( verbose=False ) :
    print "PYCODE"
    pc = test_pycode(verbose)
    print "NOSE"
    no = test_nose(verbose)
    print "PYTEST"
    pt = test_pytest(verbose)
    print "FINISHED"
    return pt | no | pc

